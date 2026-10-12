const CATEGORY_ICONS = {
  "Clothing and Ethnic Wear": "🧵",
  "Electronics": "🎧",
  "Jewellery and Accessories": "💍",
  "Beauty and Personal Care": "🌼",
  "Healthcare and Wellness": "🌿",
  "Indian Handicrafts": "🏺",
  "Home and Kitchen": "🏡",
  "Footwear": "👡",
  "Snacks and Namkeen": "🥨",
  "Chocolates and Sweets": "🍬",
  "Books and Stationery": "📚",
  "Local and Handmade Products": "🪡",
  "Agriculture and Natural Products": "🌱",
  "Festival and Gift Collections": "🪔"
};

const STATUS_STEPS = [
  "Order Placed", "Confirmed", "Preparing", "Shipped",
  "Out for delivery", "Delivered"
];

let allProducts = [];
let categories = [];
let selectedCategory = "All";
let selectedSort = "popular";
let currentPage = 1;
let totalPages = 1;
let requestSequence = 0;
let editingProductId = null;
let selectedSellerId = null;
let selectedSeller = null;
let cart = JSON.parse(localStorage.getItem("aikya_cart") || "[]");
let me = null;
const productCache = new Map();

const $ = id => document.getElementById(id);
const rupees = amount => "₹" + Number(amount).toLocaleString("en-IN", {
  maximumFractionDigits: 2
});

async function api(url, options = {}) {
  const headers = {...(options.headers || {})};
  if (typeof options.body === "string") headers["Content-Type"] = "application/json";
  const response = await fetch(url, {...options, headers});
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.error || "Something went wrong.");
  return data;
}

function toast(message) {
  const el = $("toast");
  el.textContent = message;
  el.classList.add("show");
  clearTimeout(toast.timer);
  toast.timer = setTimeout(() => el.classList.remove("show"), 3000);
}

function escapeHTML(value) {
  return String(value ?? "").replace(/[&<>"']/g, char => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;",
    '"': "&quot;", "'": "&#39;"
  })[char]);
}

function saveCart() {
  localStorage.setItem("aikya_cart", JSON.stringify(cart));
  $("cartCount").textContent = cart.reduce((sum, item) => sum + item.quantity, 0);
}

function showSection(section) {
  ["shop", "cart", "account", "orders", "admin", "seller", "orderConfirmation"].forEach(name => {
    $(name + "Section").classList.toggle("hidden",
      name !== section && !(name === "orderConfirmation" && section === "confirmation"));
  });
  if (section === "cart") renderCart();
  if (section === "orders") loadOrders();
  if (section === "account") renderAccount();
  if (section === "admin") loadAdmin();
  if (section === "seller") loadSellerSection();
  window.scrollTo({top: 0, behavior: "smooth"});
}

async function loadCategories() {
  categories = await api("/api/categories");
  renderCategories();
  const options = categories.map(category =>
    `<option value="${escapeHTML(category.name)}">${escapeHTML(category.name)}</option>`
  ).join("");
  $("adminCategory").innerHTML = options;
  $("sellerCategory").innerHTML = options;
}

function renderCategories() {
  $("categories").innerHTML = categories.map(category => `
    <button type="button" class="category-card ${selectedCategory === category.name ? "active" : ""}"
      data-category="${escapeHTML(category.name)}">
      <span class="category-icon">${CATEGORY_ICONS[category.name] || "✦"}</span>
      <strong>${escapeHTML(category.name)}</strong>
      <small>${category.count} available item${category.count === 1 ? "" : "s"}</small>
    </button>
  `).join("");
}

function buildProductQuery(page) {
  const params = new URLSearchParams();
  params.set("category", selectedCategory);
  params.set("page", page);
  params.set("limit", 12);
  params.set("sort", selectedSort);
  if (selectedSellerId) params.set("seller_id", selectedSellerId);
  const search = [$("searchInput").value, $("categorySearch").value]
    .map(value => value.trim()).filter(Boolean).join(" ");
  if (search) params.set("search", search);
  if ($("minPrice").value) params.set("min_price", $("minPrice").value);
  if ($("maxPrice").value) params.set("max_price", $("maxPrice").value);
  if ($("availableOnly").checked) params.set("available", "true");
  return params;
}

async function loadProducts(reset = true) {
  if (reset) currentPage = 1;
  const requestId = ++requestSequence;
  try {
    const data = await api(`/api/products?${buildProductQuery(currentPage)}`);
    if (requestId !== requestSequence) return;
    const incoming = data.products || [];
    incoming.forEach(product => productCache.set(product.id, product));
    allProducts = reset ? incoming : allProducts.concat(incoming);
    totalPages = data.pages || 1;
    renderProducts(data.total || 0);
  } catch (err) {
    if (requestId === requestSequence) toast(err.message);
  }
}

function renderProducts(total) {
  const category = categories.find(item => item.name === selectedCategory);
  $("collectionTitle").textContent = selectedSeller
    ? selectedSeller.shop_name
    : selectedCategory === "All" ? "Find your favourites" : selectedCategory;
  $("collectionEyebrow").textContent = selectedSeller
    ? `SELLER STOREFRONT · ${selectedSeller.city}, ${selectedSeller.state}`
    : selectedCategory === "All" ? "THE DEMO COLLECTION" : "EXPLORE THIS COLLECTION";
  $("categoryDescription").textContent = selectedSeller
    ? (selectedSeller.description || `${selectedSeller.available_products} active product listings from this approved seller.`)
    : category ? category.description : "Browse sample products from the AIKYA demo catalogue.";
  $("productCount").textContent = `${total} available item${total === 1 ? "" : "s"}`;
  $("allCategoriesBtn").classList.toggle("hidden", selectedCategory === "All" && !selectedSeller);

  if (!allProducts.length) {
    $("productsGrid").innerHTML = `
      <div class="empty">
        <h3>No products found in this collection yet.</h3>
        <p>Try another search or clear the filters to see more of AIKYA.</p>
        <button class="secondary" onclick="clearCatalogFilters()">Clear filters</button>
      </div>`;
  } else {
    $("productsGrid").innerHTML = allProducts.map(productCardMarkup).join("");
  }
  $("loadMoreBtn").classList.toggle("hidden", currentPage >= totalPages);
}

function productCardMarkup(product) {
  const demoLabel = product.source === "demo"
    ? `<span class="demo-label">DEMO LISTING</span>` : "";
  const badge = product.badge
    ? `<span class="product-badge">${escapeHTML(product.badge)}</span>` : "";
  const seller = product.seller_name || "Aikya Demo Store";
  const location = [product.seller_city, product.seller_state].filter(Boolean).join(", ");
  return `
    <article class="product-card">
      <img class="product-image"
        src="${escapeHTML(product.image || "")}"
        alt="${escapeHTML(product.name)}"
        loading="lazy"
        onerror="this.onerror=null;this.src='https://placehold.co/600x450/fff2dc/7d2342?text=AIKYA+Demo'">
      <div class="product-info">
        <span class="product-category">${escapeHTML(product.category)}</span>
        <h3>${escapeHTML(product.name)}</h3>
        <p class="seller-location">${escapeHTML(seller)}${location ? ` · ${escapeHTML(location)}` : ""}</p>
        ${product.seller_id ? `<button class="seller-store-link" onclick="openSellerStore(${product.seller_id})">Visit seller storefront</button>` : ""}
        <div class="product-labels">${demoLabel}${badge}</div>
        <div class="product-rating">${product.rating ? `★ ${Number(product.rating).toFixed(1)} (${product.rating_count || 0})` : "New collection"}</div>
        <div class="product-bottom">
          <span class="price">${rupees(product.price)}</span>
          <button class="add-btn" ${product.stock <= 0 ? "disabled" : ""}
            onclick="addToCart(${product.id})">${product.stock <= 0 ? "Sold out" : "＋ Add"}</button>
        </div>
        <p class="stock">${product.stock > 0 ? `${product.stock} in stock` : "Currently unavailable"}</p>
        <button class="details-btn" onclick="openProductDetails(${product.id})">View details</button>
      </div>
    </article>`;
}

function scrollToCollection() {
  const collection = $("products");
  const headerOffset = document.querySelector(".topbar").getBoundingClientRect().height + 16;
  const top = collection.getBoundingClientRect().top + window.scrollY - headerOffset;
  window.scrollTo({top, behavior: "smooth"});
}

function selectCategory(category, sort = null) {
  selectedCategory = category;
  selectedSellerId = null;
  selectedSeller = null;
  if (sort) {
    selectedSort = sort;
    $("sortProducts").value = sort;
  }
  $("categorySearch").value = "";
  renderCategories();
  scrollToCollection();
  loadProducts();
}

function setPriceCollection(maxPrice) {
  selectedCategory = "All";
  selectedSellerId = null;
  selectedSeller = null;
  $("maxPrice").value = maxPrice;
  $("minPrice").value = "";
  renderCategories();
  scrollToCollection();
  loadProducts();
}

async function openSellerStore(sellerId) {
  try {
    selectedSeller = await api(`/api/sellers/${sellerId}`);
    selectedSellerId = sellerId;
    selectedCategory = "All";
    renderCategories();
    scrollToCollection();
    loadProducts();
  } catch (err) { toast(err.message); }
}

function clearCatalogFilters() {
  $("searchInput").value = "";
  $("categorySearch").value = "";
  $("minPrice").value = "";
  $("maxPrice").value = "";
  $("availableOnly").checked = false;
  selectedSellerId = null;
  selectedSeller = null;
  selectedCategory = "All";
  renderCategories();
  loadProducts();
}

function loadMoreProducts() {
  if (currentPage >= totalPages) return;
  currentPage++;
  loadProducts(false);
}

async function openProductDetails(id) {
  try {
    const product = await api(`/api/products/${id}`);
    productCache.set(product.id, product);
    const location = [product.seller_city, product.seller_state].filter(Boolean).join(", ");
    $("productDialogContent").innerHTML = `
      <img src="${escapeHTML(product.image || "")}" alt="${escapeHTML(product.name)}"
        onerror="this.onerror=null;this.src='https://placehold.co/700x450/fff2dc/7d2342?text=AIKYA+Demo'">
      <p class="eyebrow">${escapeHTML(product.category)}</p>
      <h2>${escapeHTML(product.name)}</h2>
      <p class="seller-location">Sold by ${escapeHTML(product.seller_name || "Aikya Demo Store")}${location ? ` · ${escapeHTML(location)}` : ""}</p>
      ${product.seller_id ? `<p><button class="seller-store-link" onclick="closeProductDialog();openSellerStore(${product.seller_id})">Visit this seller's store</button></p>` : ""}
      <p>${escapeHTML(product.description || "A sample product from the AIKYA demo catalogue.")}</p>
      <p>${product.source === "demo" ? '<span class="demo-label">DEMO LISTING — illustrative catalogue item</span>' : ""} ${product.badge ? `<span class="product-badge">${escapeHTML(product.badge)}</span>` : ""}</p>
      <p class="dialog-price">${rupees(product.price)}</p>
      <p class="stock">${product.stock > 0 ? `${product.stock} available` : "Currently unavailable"}</p>
      <label>Quantity <input id="detailQuantity" type="number" min="1" max="${Math.min(product.stock, 20)}" value="1" ${product.stock < 1 ? "disabled" : ""}></label>
      <button class="primary" ${product.stock < 1 ? "disabled" : ""} onclick="addDetailToCart(${product.id})">Add to bag</button>`;
    $("productDialog").showModal();
  } catch (err) {
    toast(err.message);
  }
}

function closeProductDialog() {
  $("productDialog").close();
}

function addDetailToCart(id) {
  addToCart(id, Number($("detailQuantity").value));
  closeProductDialog();
}

function addToCart(id, quantity = 1) {
  const product = productCache.get(id);
  if (!product || product.stock < 1) {
    toast("This product is unavailable.");
    return;
  }
  const item = cart.find(entry => entry.id === id);
  const newQuantity = (item ? item.quantity : 0) + Number(quantity);
  if (!Number.isInteger(Number(quantity)) || quantity < 1 ||
      newQuantity > product.stock || newQuantity > 20) {
    toast("Choose a quantity within the available stock.");
    return;
  }
  if (item) item.quantity = newQuantity;
  else cart.push({id, quantity: Number(quantity)});
  saveCart();
  toast("Added to your bag!");
}

async function ensureCartProducts() {
  const missing = cart.filter(item => !productCache.has(item.id));
  await Promise.all(missing.map(async item => {
    try {
      const product = await api(`/api/products/${item.id}`);
      productCache.set(product.id, product);
    } catch {
      cart = cart.filter(entry => entry.id !== item.id);
    }
  }));
}

async function renderCart() {
  await ensureCartProducts();
  saveCart();
  if (!cart.length) {
    $("cartContent").innerHTML = `<div class="empty"><h3>Your bag is waiting for something lovely.</h3><button class="primary" onclick="showSection('shop')">Explore products</button></div>`;
    return;
  }
  const subtotal = cart.reduce((sum, item) =>
    sum + productCache.get(item.id).price * item.quantity, 0);
  const shipping = subtotal >= 999 ? 0 : 49;
  $("cartContent").innerHTML = `
    ${cart.map(item => {
      const product = productCache.get(item.id);
      return `<div class="cart-row">
        <div><strong>${escapeHTML(product.name)}</strong><p class="muted">${rupees(product.price)} each · ${escapeHTML(product.seller_name || "Aikya Demo Store")}</p></div>
        <div class="qty-controls"><button onclick="changeQuantity(${item.id},-1)">−</button><strong>${item.quantity}</strong><button onclick="changeQuantity(${item.id},1)">＋</button></div>
        <div><strong>${rupees(product.price * item.quantity)}</strong><button class="remove-btn" onclick="removeItem(${item.id})">Remove</button></div>
      </div>`;
    }).join("")}
    <div class="summary">
      <div class="summary-line"><span>Subtotal</span><strong>${rupees(subtotal)}</strong></div>
      <div class="summary-line"><span>Delivery</span><strong>${shipping ? rupees(shipping) : "FREE"}</strong></div>
      <div class="summary-line summary-total"><span>Total</span><span>${rupees(subtotal + shipping)}</span></div>
      <button class="primary" onclick="openCheckout()" style="width:100%">Continue to demo checkout →</button>
      <p class="muted">Cash-on-delivery simulation only. No real payment is collected.</p>
    </div>`;
}

function changeQuantity(id, change) {
  const item = cart.find(entry => entry.id === id);
  const product = productCache.get(id);
  if (!item || !product) return;
  const quantity = item.quantity + change;
  if (quantity < 1) cart = cart.filter(entry => entry.id !== id);
  else if (quantity <= product.stock && quantity <= 20) item.quantity = quantity;
  else return toast("No more stock available.");
  saveCart();
  renderCart();
}

function removeItem(id) {
  cart = cart.filter(item => item.id !== id);
  saveCart();
  renderCart();
}

function openCheckout() {
  if (!cart.length) return toast("Your bag is empty.");
  if (!me) {
    toast("Please log in before checkout.");
    showSection("account");
    return;
  }
  $("checkoutForm").elements.name.value = me.name || "";
  $("checkoutDialog").showModal();
}

function closeCheckoutDialog() {
  $("checkoutDialog").close();
}

async function submitCheckout(event) {
  event.preventDefault();
  const form = new FormData(event.target);
  const details = Object.fromEntries(form.entries());
  try {
    const result = await api("/api/orders", {
      method: "POST",
      body: JSON.stringify({...details, items: cart})
    });
    cart = [];
    saveCart();
    closeCheckoutDialog();
    await loadProducts();
    $("confirmationContent").innerHTML = `
      <p>Order number <strong>#${result.order_id}</strong></p>
      <p>Order total <strong>${rupees(result.total)}</strong> · Delivery ${result.shipping ? rupees(result.shipping) : "FREE"}</p>
      <p>Estimated delivery: ${escapeHTML(result.eta)}</p>
      <p class="muted">This is a local demo/Cash on Delivery simulation. No payment was processed.</p>`;
    toast(`Demo order #${result.order_id} placed.`);
    showSection("confirmation");
  } catch (err) {
    toast(err.message);
  }
}

async function renderAccount() {
  try {
    const result = await api("/api/me");
    me = result.user;
  } catch {
    me = null;
  }
  $("accountForms").classList.toggle("hidden", !!me);
  $("logoutBtn").classList.toggle("hidden", !me);
  if (me) {
    $("accountMessage").innerHTML =
      `Signed in as <strong>${escapeHTML(me.name)}</strong> (${escapeHTML(me.role)}).`;
    if (me.role === "admin") $("accountMessage").innerHTML +=
      `<p><button class="primary" onclick="showSection('admin')">Open admin dashboard</button></p>`;
    if (me.role === "seller") $("accountMessage").innerHTML +=
      `<p><button class="primary" onclick="showSection('seller')">Open seller centre</button></p>`;
  } else {
    $("accountMessage").textContent =
      "Log in or create an account to place orders, track deliveries, or sell on AIKYA.";
  }
}

async function refreshUser() {
  const result = await api("/api/me");
  me = result.user;
}

$("loginForm").addEventListener("submit", async event => {
  event.preventDefault();
  const form = new FormData(event.target);
  try {
    await api("/api/login", {method: "POST", body: JSON.stringify({
      email: form.get("email"), password: form.get("password")
    })});
    await refreshUser();
    toast("Welcome back!");
    showSection("shop");
  } catch (err) { toast(err.message); }
});

$("registerForm").addEventListener("submit", async event => {
  event.preventDefault();
  const form = new FormData(event.target);
  try {
    await api("/api/register", {method: "POST", body: JSON.stringify({
      name: form.get("name"), email: form.get("email"), password: form.get("password")
    })});
    await refreshUser();
    toast("Account created successfully!");
    showSection("shop");
  } catch (err) { toast(err.message); }
});

$("logoutBtn").addEventListener("click", async () => {
  try {
    await api("/api/logout", {method: "POST"});
    me = null;
    toast("You have logged out.");
    renderAccount();
  } catch (err) { toast(err.message); }
});

async function loadOrders() {
  if (!me) {
    $("ordersContent").innerHTML = `<div class="empty">Please <button class="secondary" onclick="showSection('account')">log in</button> to view your orders.</div>`;
    return;
  }
  try {
    const orders = await api("/api/orders");
    $("ordersContent").innerHTML = orders.length
      ? orders.map(order => orderCard(order)).join("")
      : `<div class="empty">You haven't placed an order yet.</div>`;
  } catch (err) { $("ordersContent").textContent = err.message; }
}

function orderCard(order) {
  const status = order.status;
  const currentIndex = STATUS_STEPS.indexOf(status);
  const timeline = status === "Cancelled"
    ? `<span class="done">Order Cancelled</span>`
    : STATUS_STEPS.map((step, index) =>
      `<span class="${index <= currentIndex ? "done" : ""}">${index <= currentIndex ? "✓ " : ""}${escapeHTML(step)}</span>`
    ).join("");
  const fullAddress = [order.address, order.city, order.state, order.pin_code].filter(Boolean).join(", ");
  const mapURL = "https://www.google.com/maps/search/?api=1&query=" + encodeURIComponent(fullAddress);
  return `<article class="order-card">
    <div class="order-top"><div><strong>Order #${order.id}</strong><p class="muted">Placed ${escapeHTML(order.created_at)}</p></div><span class="status-pill">${escapeHTML(status)}</span></div>
    <div class="timeline">${timeline}</div><p><strong>Items</strong></p>
    ${order.items.map(item => `<p>${escapeHTML(item.product_name)} × ${item.quantity} · ${escapeHTML(item.seller_name || "Aikya Demo Store")} · ${escapeHTML(item.seller_status || order.status)} — ${rupees(item.price * item.quantity)}</p>`).join("")}
    <p><strong>Total: ${rupees(order.total)}</strong></p><p class="muted">Estimated delivery: ${escapeHTML(order.eta)}</p>
    <p class="muted">Delivery address: ${escapeHTML(fullAddress)}</p>
    <p><a class="secondary" href="${mapURL}" target="_blank" rel="noopener noreferrer">Open address in Maps ↗</a></p>
    <button class="secondary" onclick="showTracking(${order.id})">Refresh tracking</button>
  </article>`;
}

async function showTracking(orderId) {
  try {
    const order = await api(`/api/orders/${orderId}`);
    toast(`Order #${order.id}: ${order.status}`);
    loadOrders();
  } catch (err) { toast(err.message); }
}

async function loadSellerSection() {
  if (!me) {
    $("sellerMessage").textContent = "Please log in with a customer account before applying to sell.";
    $("sellerApplication").classList.add("hidden");
    $("sellerDashboard").classList.add("hidden");
    return;
  }
  if (me.role === "customer") {
    $("sellerMessage").textContent = "Apply once to open your seller storefront. Listings are reviewed before they are visible to customers.";
    $("sellerApplication").classList.remove("hidden");
    $("sellerDashboard").classList.add("hidden");
    return;
  }
  if (me.role !== "seller") {
    $("sellerMessage").textContent = "This section is for customer seller applications and seller tools.";
    $("sellerApplication").classList.add("hidden");
    $("sellerDashboard").classList.add("hidden");
    return;
  }
  $("sellerApplication").classList.add("hidden");
  try {
    const data = await api("/api/seller/dashboard");
    $("sellerMessage").textContent = data.seller.status === "approved"
      ? `Welcome, ${data.seller.shop_name}. Your seller account is approved.`
      : `Your seller application is ${data.seller.status}. You can view its status here; listings are available after approval.`;
    $("sellerDashboard").classList.toggle("hidden", data.seller.status !== "approved");
    if (data.seller.status === "approved") renderSellerDashboard(data);
  } catch (err) {
    $("sellerDashboard").classList.add("hidden");
    toast(err.message);
  }
}

$("sellerApplyForm").addEventListener("submit", async event => {
  event.preventDefault();
  const form = new FormData(event.target);
  try {
    await api("/api/seller/register", {method: "POST", body: JSON.stringify({
      phone: form.get("phone"), shop_name: form.get("shop_name"),
      city: form.get("city"), state: form.get("state"),
      description: form.get("description")
    })});
    await refreshUser();
    toast("Seller application submitted for review.");
    loadSellerSection();
  } catch (err) { toast(err.message); }
});

function renderSellerDashboard(data) {
  $("sellerStats").innerHTML = [
    ["Listings", data.products.length],
    ["Orders", data.summary.orders],
    ["Sales", rupees(data.summary.sales)],
    ["Low stock", data.products.filter(product => product.stock <= 5).length]
  ].map(([label, value]) => `<div class="stat-card"><span class="muted">${label}</span><strong>${value}</strong></div>`).join("");

  $("sellerProducts").innerHTML = data.products.length ? data.products.map(product => `
    <article class="product-card">
      <img class="product-image" src="${escapeHTML(product.image || "")}" alt="${escapeHTML(product.name)}" onerror="this.onerror=null;this.src='https://placehold.co/600x450/fff2dc/7d2342?text=AIKYA+Demo'">
      <div class="product-info"><span class="product-category">${escapeHTML(product.category)}</span><h3>${escapeHTML(product.name)}</h3>
        <p>${rupees(product.price)} · ${product.stock} in stock ${product.stock <= 5 ? "· Low stock" : ""}</p>
        <div class="seller-listing-actions"><button class="secondary" onclick="editSellerProduct(${product.id})">Edit</button><button class="secondary" onclick="toggleSellerProduct(${product.id},${product.active ? "false" : "true"})">${product.active ? "Pause" : "Activate"}</button><button class="remove-btn" onclick="deleteSellerProduct(${product.id})">Remove</button></div>
      </div>
    </article>`).join("") : `<p class="empty">No listings yet. Add your first product above.</p>`;

  $("sellerOrders").innerHTML = data.orders.length ? data.orders.map(order => `
    <article class="order-card"><div class="order-top"><div><strong>Order #${order.id}</strong><p>${escapeHTML(order.product_name)} × ${order.quantity} · ${rupees(order.price * order.quantity)}</p></div><span class="status-pill">${escapeHTML(order.seller_status || "Order Placed")}</span></div>
      <div class="seller-listing-actions"><select id="seller-status-${order.id}">${["Order Placed", "Confirmed", "Preparing", "Ready to Ship"].map(status => `<option ${status === (order.seller_status || "Order Placed") ? "selected" : ""}>${status}</option>`).join("")}</select><button class="secondary" onclick="updateSellerOrder(${order.id})">Update my preparation status</button></div>
    </article>`).join("") : `<p class="empty">Orders containing your products will appear here.</p>`;
}

$("sellerProductForm").addEventListener("submit", async event => {
  event.preventDefault();
  const form = new FormData(event.target);
  const url = editingProductId
    ? `/api/seller/products/${editingProductId}` : "/api/seller/products";
  try {
    await api(url, {method: editingProductId ? "PUT" : "POST", body: form});
    event.target.reset();
    editingProductId = null;
    $("sellerProductSubmit").textContent = "Publish listing";
    $("cancelEditProduct").classList.add("hidden");
    toast("Product listing saved.");
    loadSellerSection();
  } catch (err) { toast(err.message); }
});

async function editSellerProduct(id) {
  try {
    const product = await api(`/api/seller/products/${id}`);
    const form = $("sellerProductForm");
    ["name", "category", "description", "price", "stock", "brand", "size", "color"].forEach(key => {
      if (form.elements[key]) form.elements[key].value =
        key === "category" ? product[key] : (key in (product.attributes || {}) ? product.attributes[key] : product[key] || "");
    });
    form.elements.condition.value = (product.attributes || {}).condition || "new";
    form.elements.made_in_india.checked = Boolean((product.attributes || {}).made_in_india);
    form.elements.image.value = product.image && product.image.startsWith("http") ? product.image : "";
    editingProductId = id;
    $("sellerProductSubmit").textContent = "Save listing";
    $("cancelEditProduct").classList.remove("hidden");
    form.scrollIntoView({behavior: "smooth"});
  } catch (err) { toast(err.message); }
}

function cancelProductEdit() {
  editingProductId = null;
  $("sellerProductForm").reset();
  $("sellerProductSubmit").textContent = "Publish listing";
  $("cancelEditProduct").classList.add("hidden");
}

async function toggleSellerProduct(id, active) {
  try {
    await api(`/api/seller/products/${id}`, {method: "PATCH", body: JSON.stringify({active})});
    loadSellerSection();
  } catch (err) { toast(err.message); }
}

async function deleteSellerProduct(id) {
  if (!confirm("Remove this listing from AIKYA?")) return;
  try {
    await api(`/api/seller/products/${id}`, {method: "DELETE"});
    toast("Listing removed from the marketplace.");
    loadSellerSection();
  } catch (err) { toast(err.message); }
}

async function updateSellerOrder(id) {
  try {
    await api(`/api/seller/orders/${id}`, {
      method: "PATCH",
      body: JSON.stringify({status: $(`seller-status-${id}`).value})
    });
    toast("Your preparation status has been updated.");
    loadSellerSection();
  } catch (err) { toast(err.message); }
}

async function loadAdmin() {
  if (!me || me.role !== "admin") {
    $("adminStats").innerHTML = "";
    $("adminOrders").innerHTML = `<p class="muted">Log in with an administrator account to access this page.</p>`;
    $("adminSellers").innerHTML = "";
    $("adminLowStock").innerHTML = "";
    $("adminProducts").innerHTML = "";
    $("adminOrderStatuses").innerHTML = "";
    return;
  }
  try {
    const data = await api("/api/admin/summary");
    $("adminStats").innerHTML = [
      ["Products", data.products], ["Orders", data.orders],
      ["Customers", data.customers],       ["Total sellers", data.total_sellers],
      ["Approved sellers", data.sellers],
      ["Pending approvals", data.pending_sellers], ["Low stock", data.low_stock],
      ["Revenue", rupees(data.revenue)]
    ].map(([label, value]) => `<div class="stat-card"><span class="muted">${label}</span><strong>${value}</strong></div>`).join("");

    $("adminSellers").innerHTML = data.sellers_list.length ? data.sellers_list.map(seller => `
      <article class="order-card"><div class="order-top"><div><strong>${escapeHTML(seller.shop_name)}</strong><p>${escapeHTML(seller.name)} · ${escapeHTML(seller.city)}, ${escapeHTML(seller.state)} · ${escapeHTML(seller.email)}</p></div><span class="status-pill">${escapeHTML(seller.status)}</span></div>
        <p>${escapeHTML(seller.description || "")}</p>
        <div class="seller-listing-actions">
          ${seller.status !== "approved" ? `<button class="primary" onclick="reviewSeller(${seller.user_id},'approved')">Approve</button>` : ""}
          ${seller.status !== "rejected" ? `<button class="secondary" onclick="reviewSeller(${seller.user_id},'rejected')">Reject</button>` : ""}
          ${seller.status !== "suspended" ? `<button class="secondary" onclick="reviewSeller(${seller.user_id},'suspended')">Suspend</button>` : ""}
        </div>
      </article>`).join("") : `<p class="muted">No seller applications.</p>`;

    $("adminLowStock").innerHTML = data.low_stock_list.length
      ? data.low_stock_list.map(product => `<p>${escapeHTML(product.name)} · ${escapeHTML(product.category)} · ${product.stock} left</p>`).join("")
      : `<p class="muted">No low-stock products.</p>`;

    $("adminProducts").innerHTML = data.products_list.map(product => `
      <article class="order-card product-moderation">
        <div><strong>${escapeHTML(product.name)}</strong><p class="muted">${escapeHTML(product.category)} · Stock ${product.stock} · ${escapeHTML(product.source)}</p></div>
        <span class="status-pill">${product.active ? "Active" : "Inactive"}</span>
        <button class="secondary" onclick="moderateProduct(${product.id},${product.active ? "false" : "true"})">${product.active ? "Deactivate" : "Activate"}</button>
      </article>`).join("");

    $("adminOrderStatuses").innerHTML = Object.entries(data.order_statuses)
      .map(([status, count]) => `<span class="product-badge">${escapeHTML(status)} · ${count}</span>`)
      .join("") || `<span class="muted">No orders yet.</span>`;

    $("adminOrders").innerHTML = data.orders_list.length ? data.orders_list.map(order => `
      <article class="order-card"><div class="order-top"><div><strong>Order #${order.id} · ${escapeHTML(order.customer_name)}</strong><p class="muted">${escapeHTML(order.created_at)} · ${rupees(order.total)}</p></div><span class="status-pill">${escapeHTML(order.status)}</span></div>
        <div class="form"><select id="status-${order.id}">${["Order Placed", "Confirmed", "Preparing", "Processing", "Packed", "Shipped", "Out for delivery", "Out for Delivery", "Delivered", "Cancelled"].map(status => `<option ${status === order.status ? "selected" : ""}>${status}</option>`).join("")}</select><button class="primary" onclick="updateStatus(${order.id})">Update status</button></div>
      </article>`).join("") : `<p class="muted">No orders yet.</p>`;
  } catch (err) { toast(err.message); }
}

async function moderateProduct(id, active) {
  try {
    await api(`/api/admin/products/${id}`, {
      method: "PATCH", body: JSON.stringify({active})
    });
    toast("Product listing moderated.");
    await loadAdmin();
    await loadProducts();
  } catch (err) { toast(err.message); }
}

async function reviewSeller(id, status) {
  try {
    await api(`/api/admin/sellers/${id}`, {method: "PATCH", body: JSON.stringify({status})});
    toast(`Seller ${status}.`);
    loadAdmin();
  } catch (err) { toast(err.message); }
}


async function updateStatus(id) {
  try {
    await api(`/api/admin/orders/${id}`, {
      method: "PATCH", body: JSON.stringify({status: $(`status-${id}`).value})
    });
    toast("Order tracking updated.");
    loadAdmin();
  } catch (err) { toast(err.message); }
}

$("addProductForm").addEventListener("submit", async event => {
  event.preventDefault();
  if (!me || me.role !== "admin") return toast("Admin access required.");
  const form = new FormData(event.target);
  try {
    await api("/api/admin/products", {method: "POST", body: JSON.stringify({
      name: form.get("name"), category: form.get("category"),
      price: form.get("price"), stock: form.get("stock"), image: form.get("image")
    })});
    event.target.reset();
    await loadProducts();
    await loadAdmin();
    toast("Product added successfully!");
  } catch (err) { toast(err.message); }
});

$("categories").addEventListener("click", event => {
  const card = event.target.closest(".category-card[data-category]");
  if (card) selectCategory(card.dataset.category);
});

$("searchBtn").addEventListener("click", () => loadProducts());
$("searchInput").addEventListener("input", () => loadProducts());
$("searchInput").addEventListener("keydown", event => {
  if (event.key === "Enter") loadProducts();
});
$("categorySearch").addEventListener("input", () => loadProducts());
$("sortProducts").addEventListener("change", event => {
  selectedSort = event.target.value;
  loadProducts();
});
["minPrice", "maxPrice", "availableOnly"].forEach(id =>
  $(id).addEventListener("change", () => loadProducts())
);
$("checkoutForm").addEventListener("submit", submitCheckout);

async function init() {
  saveCart();
  try {
    await loadCategories();
    await loadProducts();
  } catch (err) { toast(err.message); }
  await refreshUser().catch(() => { me = null; });
  await renderAccount();
}

init();
