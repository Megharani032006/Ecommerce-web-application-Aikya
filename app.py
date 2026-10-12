
from flask import Flask, render_template, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
import secrets
import math
import uuid
import json
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", secrets.token_hex(32))
DB = os.environ.get("AIKYA_DATABASE", os.path.join(app.root_path, "aikya.db"))
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024
app.config["UPLOAD_FOLDER"] = os.path.join(app.root_path, "static", "uploads")
app.config["ALLOWED_IMAGE_EXTENSIONS"] = {".jpg", ".jpeg", ".png", ".webp"}
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

CATEGORIES = [
    "Clothing and Ethnic Wear", "Electronics", "Jewellery and Accessories",
    "Beauty and Personal Care", "Healthcare and Wellness", "Indian Handicrafts",
    "Home and Kitchen", "Footwear", "Snacks and Namkeen",
    "Chocolates and Sweets", "Books and Stationery",
    "Local and Handmade Products", "Agriculture and Natural Products",
    "Festival and Gift Collections"
]

CATEGORY_DESCRIPTIONS = {
    "Clothing and Ethnic Wear": "Everyday styles and Indian clothing from local makers.",
    "Electronics": "Useful devices and everyday tech essentials.",
    "Jewellery and Accessories": "Finishing touches, artisan jewellery, bags, and more.",
    "Beauty and Personal Care": "Thoughtful everyday skincare and personal-care picks.",
    "Healthcare and Wellness": "Wellness essentials for your home and routine.",
    "Indian Handicrafts": "Traditional craft and contemporary work by Indian artisans.",
    "Home and Kitchen": "Warm, practical pieces for Indian homes and kitchens.",
    "Footwear": "Comfortable everyday and occasion footwear.",
    "Snacks and Namkeen": "A taste of regional snacks and savoury favourites.",
    "Chocolates and Sweets": "Sweet treats and thoughtful festive boxes.",
    "Books and Stationery": "Tools for learning, writing, and making.",
    "Local and Handmade Products": "One-of-a-kind work from independent creators.",
    "Agriculture and Natural Products": "Garden, farm, and nature-inspired essentials.",
    "Festival and Gift Collections": "Small ways to make celebrations feel special."
}

PRODUCTS = [
    ("Floral Summer Dress", "Dresses", 899, "https://images.unsplash.com/photo-1515372039744-b8f02a3ae446", 15),
    ("Casual Cotton Kurti", "Dresses", 699, "https://images.unsplash.com/photo-1583391733956-6c78276477e5", 20),
    ("Party Wear Dress", "Dresses", 1499, "https://images.unsplash.com/photo-1566174053879-31528523f8ae", 10),
    ("Classic Denim Jacket", "Dresses", 1299, "https://images.unsplash.com/photo-1543076447-215ad9ba6923", 8),
    ("Wireless Headphones", "Electronics", 1499, "https://images.unsplash.com/photo-1505740420928-5e560c06d30e", 15),
    ("Bluetooth Speaker", "Electronics", 999, "https://images.unsplash.com/photo-1608043152269-423dbba4e7e1", 12),
    ("Smart Watch", "Electronics", 1999, "https://images.unsplash.com/photo-1523275335684-37898b6baf30", 10),
    ("Wireless Mouse", "Electronics", 499, "https://images.unsplash.com/photo-1527814050087-3793815479db", 25),
    ("Elegant Handbag", "Accessories", 1199, "https://images.unsplash.com/photo-1584917865442-de89df76afd3", 12),
    ("Minimalist Watch", "Accessories", 899, "https://images.unsplash.com/photo-1524592094714-0f0654e20314", 10),
    ("Sunglasses", "Accessories", 599, "https://images.unsplash.com/photo-1511499767150-a48a237f0083", 20),
    ("Silver Pendant", "Accessories", 399, "https://images.unsplash.com/photo-1611652022419-a9419f74343d", 15),
    ("Digital Thermometer", "Healthcare", 249, "https://images.unsplash.com/photo-1584308666744-24d5c474f2ae", 30),
    ("First Aid Kit", "Healthcare", 399, "https://images.unsplash.com/photo-1603398938378-e54eab446dde", 15),
    ("Reusable Hot Water Bag", "Healthcare", 299, "https://images.unsplash.com/photo-1576091160399-112ba8d25d1d", 20),
    ("Fitness Water Bottle", "Healthcare", 349, "https://images.unsplash.com/photo-1602143407151-7111542de6e8", 20),
    ("Vitamin C Face Serum", "Facial Care", 499, "https://images.unsplash.com/photo-1601049541289-9b1b7bbbfe19", 15),
    ("Gentle Face Cleanser", "Facial Care", 299, "https://images.unsplash.com/photo-1556229010-6c3f2c9ca5f8", 20),
    ("Daily Moisturizer", "Facial Care", 399, "https://images.unsplash.com/photo-1608248543803-ba4f8c70ae0b", 15),
    ("Sunscreen SPF 50", "Facial Care", 449, "https://images.unsplash.com/photo-1556228720-195a672e8a03", 20),
    ("Chocolate Gift Box", "Chocolates", 499, "https://images.unsplash.com/photo-1548907040-4d42cfcf8e24", 20),
    ("Dark Chocolate Bar", "Chocolates", 199, "https://images.unsplash.com/photo-1511381939415-e44015466834", 30),
    ("Assorted Truffles", "Chocolates", 349, "https://images.unsplash.com/photo-1481391319762-47dff72954d9", 15),
    ("Chocolate Cookies", "Chocolates", 149, "https://images.unsplash.com/photo-1499636136210-6f4ee915583e", 25),
    ("Masala Chips Pack", "Namkeen & Snacks", 50, "https://images.unsplash.com/photo-1566478989037-eec170784d0b", 50),
    ("Traditional Mixture", "Namkeen & Snacks", 120, "https://images.unsplash.com/photo-1626132647523-66f5bf380027", 30),
    ("Roasted Nuts Pack", "Namkeen & Snacks", 249, "https://images.unsplash.com/photo-1505576399274-565b52d4ac71", 25),
    ("Salted Crackers", "Namkeen & Snacks", 99, "https://images.unsplash.com/photo-1590080877777-1c7f9c5d4d22", 30),
    ("Classic Sneakers", "Shoes", 1799, "https://images.unsplash.com/photo-1542291026-7eec264c27ff", 12),
    ("Running Shoes", "Shoes", 2199, "https://images.unsplash.com/photo-1460353581641-37baddab0fa2", 10),
    ("Casual Flats", "Shoes", 699, "https://images.unsplash.com/photo-1543163521-1bf539c55dd2", 15),
    ("Everyday Sandals", "Shoes", 499, "https://images.unsplash.com/photo-1562273138-f46be4ebdf33", 20),
]

DEMO_CATALOG = [
    ("Cotton Anarkali Kurta", "Clothing and Ethnic Wear", 1299, 18, "Nila Textiles", "Jaipur", "Rajasthan", "Soft cotton kurta inspired by block-print traditions.", "Clothing", False),
    ("Ajrakh Print Dupatta", "Clothing and Ethnic Wear", 899, 14, "Kutch Loom House", "Bhuj", "Gujarat", "A lightweight dupatta with an Ajrakh-inspired print.", "Clothing", True),
    ("Festive Silk Blend Saree", "Clothing and Ethnic Wear", 2499, 8, "Nila Textiles", "Jaipur", "Rajasthan", "A demo festive drape in a rich silk blend.", "Clothing", False),
    ("Handloom Kids Kurta Set", "Clothing and Ethnic Wear", 999, 11, "Nila Textiles", "Jaipur", "Rajasthan", "Comfortable handloom-inspired kidswear set.", "Clothing", False),
    ("USB-C Fast Charger", "Electronics", 799, 24, "Aikya Demo Store", "Pune", "Maharashtra", "Compact demo charger with USB-C output.", "Electronics", False),
    ("Wireless Earbuds", "Electronics", 1599, 15, "Aikya Demo Store", "Pune", "Maharashtra", "Everyday wireless earbuds for calls and music.", "Electronics", False),
    ("Compact Power Bank", "Electronics", 1199, 12, "Aikya Demo Store", "Pune", "Maharashtra", "Portable charging for your daily commute.", "Electronics", False),
    ("Mechanical Keyboard", "Electronics", 2299, 7, "Aikya Demo Store", "Pune", "Maharashtra", "A compact keyboard for work and study.", "Electronics", False),
    ("Kundan Drop Earrings", "Jewellery and Accessories", 649, 16, "Sunehri Studio", "Jaipur", "Rajasthan", "Lightweight festive earrings with a kundan-inspired finish.", "Accessories", True),
    ("Brass Tone Bangle Set", "Jewellery and Accessories", 499, 21, "Sunehri Studio", "Jaipur", "Rajasthan", "A set of four bangles for everyday and festive looks.", "Accessories", False),
    ("Handwoven Cotton Wallet", "Jewellery and Accessories", 399, 19, "Kutch Loom House", "Bhuj", "Gujarat", "Small handwoven wallet with a zip closure.", "Accessories", True),
    ("Beaded Hair Accessory Set", "Jewellery and Accessories", 299, 20, "Sunehri Studio", "Jaipur", "Rajasthan", "Colourful handmade clips for everyday styling.", "Accessories", True),
    ("Aloe Vera Face Wash", "Beauty and Personal Care", 249, 31, "Neem & Nila", "Kochi", "Kerala", "Gentle demo cleanser for a simple skincare routine.", "Beauty", False),
    ("Neem Herbal Soap Set", "Beauty and Personal Care", 349, 26, "Neem & Nila", "Kochi", "Kerala", "A set of four locally-inspired herbal soaps.", "Beauty", False),
    ("Coconut Hair Oil", "Beauty and Personal Care", 199, 40, "Neem & Nila", "Kochi", "Kerala", "Everyday coconut hair oil in a demo bottle.", "Beauty", False),
    ("Rose Water Toner", "Beauty and Personal Care", 279, 22, "Neem & Nila", "Kochi", "Kerala", "A refreshing rose water toner for daily use.", "Beauty", False),
    ("Digital Thermometer", "Healthcare and Wellness", 299, 32, "Aikya Demo Store", "Pune", "Maharashtra", "Digital thermometer for home first-aid kits.", "Healthcare", False),
    ("First Aid Essentials Kit", "Healthcare and Wellness", 599, 17, "Aikya Demo Store", "Pune", "Maharashtra", "Demo kit with common non-prescription first-aid supplies.", "Healthcare", False),
    ("Yoga Cotton Mat", "Healthcare and Wellness", 899, 13, "Sattva Living", "Mysuru", "Karnataka", "Textured cotton-blend mat for stretching and yoga.", "Wellness", False),
    ("Copper Tongue Cleaner Set", "Healthcare and Wellness", 249, 28, "Sattva Living", "Mysuru", "Karnataka", "Reusable personal-care set for home use.", "Wellness", False),
    ("Blue Pottery Tea Light Holder", "Indian Handicrafts", 799, 10, "Mittika Crafts", "Jaipur", "Rajasthan", "Hand-finished demo pottery with a blue floral motif.", "Handmade", True),
    ("Carved Wooden Elephant Pair", "Indian Handicrafts", 1099, 9, "Mittika Crafts", "Jaipur", "Rajasthan", "Decorative wooden pair made in a traditional style.", "Handmade", True),
    ("Madhubani Art Print", "Indian Handicrafts", 699, 12, "Rang Rekha Studio", "Madhubani", "Bihar", "Colourful folk-art-inspired print in a paper sleeve.", "Handmade", True),
    ("Terracotta Planter", "Indian Handicrafts", 549, 14, "Mittika Crafts", "Jaipur", "Rajasthan", "Small breathable terracotta planter for indoor plants.", "Handmade", True),
    ("Stainless Steel Masala Dabba", "Home and Kitchen", 899, 18, "Gharana Home", "Indore", "Madhya Pradesh", "Seven-compartment spice box for Indian kitchens.", "Home", False),
    ("Handblock Table Runner", "Home and Kitchen", 749, 12, "Kutch Loom House", "Bhuj", "Gujarat", "Cotton table runner with a handblock-style print.", "Home", True),
    ("Brass Diya Pair", "Home and Kitchen", 599, 20, "Gharana Home", "Indore", "Madhya Pradesh", "A pair of brass-finish diyas for home decor.", "Home", False),
    ("Jute Storage Basket", "Home and Kitchen", 499, 16, "Gharana Home", "Indore", "Madhya Pradesh", "Handwoven basket for shelves and everyday storage.", "Home", True),
    ("Kolhapuri Style Sandals", "Footwear", 1199, 15, "Paar Footwear", "Kolhapur", "Maharashtra", "Demo leather-look sandals with traditional detailing.", "Footwear", False),
    ("Embroidered Jutti", "Footwear", 1499, 9, "Paar Footwear", "Jaipur", "Rajasthan", "Colourful embroidered flats for festive outfits.", "Footwear", True),
    ("Everyday Canvas Sneakers", "Footwear", 1399, 18, "Paar Footwear", "Pune", "Maharashtra", "Lightweight canvas sneakers for daily wear.", "Footwear", False),
    ("Comfort Slide Slippers", "Footwear", 399, 27, "Paar Footwear", "Pune", "Maharashtra", "Easy-to-wear indoor and casual slides.", "Footwear", False),
    ("Coastal Murukku Pack", "Snacks and Namkeen", 149, 35, "Malabar Pantry", "Kozhikode", "Kerala", "Crunchy demo murukku snack pack; sample listing.", "Food", False),
    ("Poha Chivda Mix", "Snacks and Namkeen", 129, 30, "Malabar Pantry", "Indore", "Madhya Pradesh", "Lightly spiced chivda inspired by regional recipes.", "Food", False),
    ("Chakli Snack Tin", "Snacks and Namkeen", 199, 22, "Malabar Pantry", "Pune", "Maharashtra", "Crisp chakli in a resealable demo tin.", "Food", False),
    ("Kodubale Crunch Pack", "Snacks and Namkeen", 169, 24, "Malabar Pantry", "Mysuru", "Karnataka", "A savoury kodubale-inspired snack for tea time.", "Food", False),
    ("Kesar Peda Gift Box", "Chocolates and Sweets", 499, 13, "Mithai Mock Shop", "Lucknow", "Uttar Pradesh", "Demo gift box; not a real-store stock claim.", "Food", False),
    ("Assorted Dry Fruit Bites", "Chocolates and Sweets", 599, 10, "Mithai Mock Shop", "Delhi", "Delhi", "A festive assortment shown as sample marketplace data.", "Food", False),
    ("Cocoa Chai Chocolate Bar", "Chocolates and Sweets", 249, 18, "Mithai Mock Shop", "Mumbai", "Maharashtra", "Small-batch-style demo chocolate bar.", "Food", False),
    ("Festival Ladoo Hamper", "Chocolates and Sweets", 799, 8, "Mithai Mock Shop", "Lucknow", "Uttar Pradesh", "Celebration hamper sample; availability is illustrative.", "Food", False),
    ("Devanagari Notebook Set", "Books and Stationery", 299, 29, "Kagaz Co.", "Delhi", "Delhi", "Three ruled notebooks with Indian-script cover art.", "Stationery", False),
    ("Watercolour Art Kit", "Books and Stationery", 699, 12, "Kagaz Co.", "Bengaluru", "Karnataka", "Beginner art kit with paints and a small pad.", "Stationery", False),
    ("Student Geometry Box", "Books and Stationery", 199, 25, "Kagaz Co.", "Delhi", "Delhi", "Everyday school geometry kit for demo listing.", "Stationery", False),
    ("Calligraphy Pen Set", "Books and Stationery", 449, 15, "Kagaz Co.", "Bengaluru", "Karnataka", "Starter pen set for lettering and sketching.", "Stationery", False),
    ("Crochet Lotus Coaster Set", "Local and Handmade Products", 599, 7, "Little Loom Studio", "Chennai", "Tamil Nadu", "Hand-crocheted cotton coaster set from a demo creator.", "Handmade", True),
    ("Resin Name Keychain", "Local and Handmade Products", 249, 10, "Little Loom Studio", "Chennai", "Tamil Nadu", "Personalised-style resin keychain sample listing.", "Handmade", True),
    ("Hand-painted Gift Tags", "Local and Handmade Products", 199, 16, "Rang Rekha Studio", "Madhubani", "Bihar", "A pack of hand-painted tags for gifts and celebrations.", "Handmade", True),
    ("Upcycled Fabric Pouch", "Local and Handmade Products", 399, 11, "Little Loom Studio", "Chennai", "Tamil Nadu", "Small reusable pouch stitched from fabric offcuts.", "Handmade", True),
    ("Kitchen Herb Seed Starter Kit", "Agriculture and Natural Products", 349, 21, "Mitti Garden", "Nashik", "Maharashtra", "Demo starter kit with common kitchen-garden seeds.", "Garden", False),
    ("Neem Garden Care Spray", "Agriculture and Natural Products", 299, 18, "Mitti Garden", "Nashik", "Maharashtra", "Illustrative garden-care listing; follow product label.", "Garden", False),
    ("Coir Planting Pots Set", "Agriculture and Natural Products", 199, 32, "Mitti Garden", "Coimbatore", "Tamil Nadu", "Biodegradable-style coir pots for seedlings.", "Garden", False),
    ("Organic Compost Sample Pack", "Agriculture and Natural Products", 249, 14, "Mitti Garden", "Nashik", "Maharashtra", "Demo sample pack for home gardening.", "Garden", False),
    ("Rangoli Stencil Collection", "Festival and Gift Collections", 299, 17, "Utsav Box", "Ahmedabad", "Gujarat", "Reusable stencil set for colourful festive rangoli.", "Festive", False),
    ("Diwali Lights Gift Set", "Festival and Gift Collections", 899, 9, "Utsav Box", "Ahmedabad", "Gujarat", "Decorative lights shown as sample catalogue content.", "Festive", False),
    ("Pooja Thali Decor Kit", "Festival and Gift Collections", 649, 11, "Utsav Box", "Varanasi", "Uttar Pradesh", "Decorative pooja accessories for a festive table.", "Festive", False),
    ("India Postcard Gift Box", "Festival and Gift Collections", 499, 14, "Rang Rekha Studio", "Madhubani", "Bihar", "Illustrated postcard assortment for thoughtful gifting.", "Festive", True)
]

STATUSES = [
    "Order Placed", "Confirmed", "Preparing", "Shipped",
    "Out for delivery", "Delivered", "Cancelled",
    "Processing", "Packed", "Out for Delivery"
]


def connect():
    db = sqlite3.connect(app.config.get("DATABASE", DB))
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    return db


def init_db():
    db = connect()
    db.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'customer',
        phone TEXT DEFAULT ''
    );

    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        price REAL NOT NULL,
        image TEXT,
        stock INTEGER NOT NULL DEFAULT 0,
        description TEXT DEFAULT '',
        seller_id INTEGER,
        seller_name TEXT NOT NULL DEFAULT 'Aikya Demo Store',
        seller_city TEXT DEFAULT '',
        seller_state TEXT DEFAULT '',
        source TEXT NOT NULL DEFAULT 'demo',
        active INTEGER NOT NULL DEFAULT 1,
        rating REAL DEFAULT 0,
        rating_count INTEGER DEFAULT 0,
        badge TEXT DEFAULT '',
        attributes TEXT DEFAULT '{}',
        FOREIGN KEY(seller_id) REFERENCES users(id)
    );

    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        customer_name TEXT NOT NULL,
        phone TEXT NOT NULL,
        address TEXT NOT NULL,
        city TEXT DEFAULT '',
        state TEXT DEFAULT '',
        pin_code TEXT DEFAULT '',
        total REAL NOT NULL,
        status TEXT NOT NULL DEFAULT 'Order Placed',
        created_at TEXT NOT NULL,
        eta TEXT NOT NULL,
        FOREIGN KEY(user_id) REFERENCES users(id)
    );

    CREATE TABLE IF NOT EXISTS order_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        product_name TEXT NOT NULL,
        price REAL NOT NULL,
        quantity INTEGER NOT NULL,
        seller_id INTEGER,
        FOREIGN KEY(order_id) REFERENCES orders(id),
        FOREIGN KEY(product_id) REFERENCES products(id),
        FOREIGN KEY(seller_id) REFERENCES users(id)
    );

    CREATE TABLE IF NOT EXISTS tracking_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER NOT NULL,
        status TEXT NOT NULL,
        event_time TEXT NOT NULL,
        FOREIGN KEY(order_id) REFERENCES orders(id)
    );
    CREATE TABLE IF NOT EXISTS sellers (
        user_id INTEGER PRIMARY KEY,
        phone TEXT NOT NULL,
        shop_name TEXT NOT NULL,
        city TEXT NOT NULL,
        state TEXT NOT NULL,
        description TEXT DEFAULT '',
        status TEXT NOT NULL DEFAULT 'pending',
        created_at TEXT NOT NULL,
        FOREIGN KEY(user_id) REFERENCES users(id)
    );
    CREATE TABLE IF NOT EXISTS seller_order_status (
        order_id INTEGER NOT NULL,
        seller_id INTEGER NOT NULL,
        status TEXT NOT NULL DEFAULT 'Order Placed',
        updated_at TEXT NOT NULL,
        PRIMARY KEY(order_id, seller_id),
        FOREIGN KEY(order_id) REFERENCES orders(id),
        FOREIGN KEY(seller_id) REFERENCES users(id)
    );
    """)

    migrations = {
        "users": {"phone": "TEXT DEFAULT ''"},
        "products": {
            "seller_id": "INTEGER",
            "seller_name": "TEXT NOT NULL DEFAULT 'Aikya Demo Store'",
            "seller_city": "TEXT DEFAULT ''",
            "seller_state": "TEXT DEFAULT ''",
            "source": "TEXT NOT NULL DEFAULT 'demo'",
            "active": "INTEGER NOT NULL DEFAULT 1",
            "rating": "REAL DEFAULT 0",
            "rating_count": "INTEGER DEFAULT 0",
            "badge": "TEXT DEFAULT ''",
            "attributes": "TEXT DEFAULT '{}'"
        },
        "orders": {
            "city": "TEXT DEFAULT ''",
            "state": "TEXT DEFAULT ''",
            "pin_code": "TEXT DEFAULT ''"
        },
        "order_items": {"seller_id": "INTEGER"}
    }
    for table, columns in migrations.items():
        existing = {
            row["name"] for row in db.execute(f"PRAGMA table_info({table})")
        }
        for column, column_type in columns.items():
            if column not in existing:
                db.execute(f"ALTER TABLE {table} ADD COLUMN {column} {column_type}")

    legacy_categories = {
        "Dresses": "Clothing and Ethnic Wear",
        "Accessories": "Jewellery and Accessories",
        "Healthcare": "Healthcare and Wellness",
        "Facial Care": "Beauty and Personal Care",
        "Chocolates": "Chocolates and Sweets",
        "Namkeen & Snacks": "Snacks and Namkeen",
        "Shoes": "Footwear",
        "Handcrafted": "Indian Handicrafts",
        "Home & Living": "Home and Kitchen",
        "Wellness": "Healthcare and Wellness"
    }
    for old_category, new_category in legacy_categories.items():
        db.execute(
            "UPDATE products SET category = ? WHERE category = ?",
            (new_category, old_category)
        )
    db.execute("""
        UPDATE products SET active = 0
        WHERE source = 'seller' AND seller_id IS NULL
    """)

    count = db.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    if count == 0:
        category_map = {
            "Dresses": "Clothing and Ethnic Wear",
            "Accessories": "Jewellery and Accessories",
            "Healthcare": "Healthcare and Wellness",
            "Facial Care": "Beauty and Personal Care",
            "Chocolates": "Chocolates and Sweets",
            "Namkeen & Snacks": "Snacks and Namkeen",
            "Shoes": "Footwear"
        }
        for name, category, price, image, stock in PRODUCTS:
            db.execute("""
                INSERT INTO products(
                    name, category, price, image, stock, description,
                    seller_name, source, badge
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 'demo', 'Demo listing')
            """, (
                name, category_map.get(category, category), price,
                image, stock, "Demo catalogue item; not a claim of real-store stock.",
                "Aikya Demo Store"
            ))

    for item in DEMO_CATALOG:
        name, category, price, stock, seller, city, state, description = item[:8]
        handmade = item[9]
        exists = db.execute(
            "SELECT 1 FROM products WHERE name = ? AND category = ?",
            (name, category)
        ).fetchone()
        if not exists:
            image_ids = {
                "Clothing and Ethnic Wear": "photo-1515372039744-b8f02a3ae446",
                "Electronics": "photo-1505740420928-5e560c06d30e",
                "Jewellery and Accessories": "photo-1584917865442-de89df76afd3",
                "Beauty and Personal Care": "photo-1601049541289-9b1b7bbbfe19",
                "Healthcare and Wellness": "photo-1603398938378-e54eab446dde",
                "Indian Handicrafts": "photo-1578749556568-bc2c40e68b61",
                "Home and Kitchen": "photo-1505693416388-ac5ce068fe85",
                "Footwear": "photo-1542291026-7eec264c27ff",
                "Snacks and Namkeen": "photo-1566478989037-eec170784d0b",
                "Chocolates and Sweets": "photo-1481391319762-47dff72954d9",
                "Books and Stationery": "photo-1455390582262-044cdead277a",
                "Local and Handmade Products": "photo-1452860606245-08befc0ff44b",
                "Agriculture and Natural Products": "photo-1416879595882-3373a0480b5b",
                "Festival and Gift Collections": "photo-1512909006721-3d6018887383"
            }
            image = (
                f"https://images.unsplash.com/{image_ids.get(category, 'photo-1512909006721-3d6018887383')}"
                "?auto=format&fit=crop&w=700&q=80"
            )
            db.execute("""
                INSERT INTO products(
                    name, category, price, image, stock, description,
                    seller_name, seller_city, seller_state, source, badge,
                    attributes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'demo', ?, ?)
            """, (
                name, category, price, image, stock,
                description + " Demo catalogue item; not a real-store stock claim.",
                seller, city, state, "Handmade" if handmade else "",
                json.dumps({
                    "is_demo": True,
                    "handmade": handmade,
                    "condition": "handmade" if handmade else "new"
                })
            ))

    admin = db.execute(
        "SELECT id FROM users WHERE email = ?",
        ("admin@example.com",)
    ).fetchone()
    if not admin:
        db.execute("""
            INSERT INTO users(name, email, password, role)
            VALUES (?, ?, ?, ?)
        """, (
            "Aikya Admin",
            "admin@example.com",
            generate_password_hash("Admin@12345"),
            "admin"
        ))

    db.commit()
    db.close()


def current_user():
    if not session.get("user_id"):
        return None
    db = connect()
    user = db.execute(
        "SELECT id, name, email, role FROM users WHERE id = ?",
        (session["user_id"],)
    ).fetchone()
    db.close()
    return dict(user) if user else None


def seller_is_approved(user_id):
    db = connect()
    seller = db.execute(
        "SELECT status FROM sellers WHERE user_id = ?", (user_id,)
    ).fetchone()
    db.close()
    return bool(seller and seller["status"] == "approved")


def product_payload(row):
    product = dict(row)
    product["available"] = product.get("stock", 0) > 0
    if product.get("attributes"):
        try:
            product["attributes"] = json.loads(product["attributes"])
        except (TypeError, ValueError):
            product["attributes"] = {}
    return product


def error(message, status=400):
    return jsonify({"error": message}), status


@app.get("/")
def home():
    return render_template("index.html")


@app.get("/api/categories")
def categories():
    db = connect()
    counts = {
        row["category"]: row["count"]
        for row in db.execute("""
            SELECT products.category, COUNT(*) AS count FROM products
            LEFT JOIN sellers ON sellers.user_id = products.seller_id
            WHERE products.active = 1 AND products.stock > 0
              AND (products.seller_id IS NULL OR sellers.status = 'approved')
            GROUP BY products.category
        """).fetchall()
    }
    db.close()
    return jsonify([
        {
            "name": category,
            "description": CATEGORY_DESCRIPTIONS[category],
            "count": counts.get(category, 0)
        }
        for category in CATEGORIES
    ])


@app.get("/api/products")
def products():
    category = request.args.get("category", "All")
    search = request.args.get("search", "").strip()
    sort = request.args.get("sort", "popular")
    available_only = request.args.get("available", "false").lower() == "true"
    min_price = request.args.get("min_price", type=float)
    max_price = request.args.get("max_price", type=float)
    seller_id = request.args.get("seller_id", type=int)
    page = request.args.get("page", type=int)
    limit = min(max(request.args.get("limit", 12, type=int), 1), 48)
    if (min_price is not None and not math.isfinite(min_price)) or (
        max_price is not None and not math.isfinite(max_price)
    ):
        return error("Price filters must be valid finite amounts.")
    if min_price is not None and max_price is not None and min_price > max_price:
        return error("Minimum price cannot exceed maximum price.")
    db = connect()
    sql = """
        SELECT p.* FROM products p
        LEFT JOIN sellers s ON s.user_id = p.seller_id
        WHERE p.active = 1
          AND (p.seller_id IS NULL OR s.status = 'approved')
    """
    args = []

    if category and category != "All":
        if category not in CATEGORIES:
            db.close()
            return error("Unknown category.")
        sql += " AND category = ?"
        args.append(category)

    if search:
        sql += " AND (p.name LIKE ? OR p.category LIKE ? OR p.description LIKE ? OR p.seller_name LIKE ?)"
        args.extend([f"%{search}%"] * 4)
    if available_only:
        sql += " AND p.stock > 0"
    if min_price is not None:
        sql += " AND p.price >= ?"
        args.append(max(min_price, 0))
    if max_price is not None:
        sql += " AND p.price <= ?"
        args.append(max(max_price, 0))
    if seller_id is not None:
        if seller_id < 1:
            db.close()
            return error("Invalid seller.")
        sql += " AND p.seller_id = ?"
        args.append(seller_id)

    order_by = {
        "popular": "p.rating DESC, p.rating_count DESC, p.id",
        "price_asc": "p.price ASC, p.id",
        "price_desc": "p.price DESC, p.id",
        "newest": "p.id DESC"
    }.get(sort)
    if not order_by:
        db.close()
        return error("Invalid product sort order.")
    sql += " ORDER BY " + order_by
    count = db.execute(
        "SELECT COUNT(*) FROM (" + sql + ")", args
    ).fetchone()[0]
    if page is not None:
        page = max(page, 1)
        sql += " LIMIT ? OFFSET ?"
        args.extend((limit, (page - 1) * limit))
    rows = db.execute(sql, args).fetchall()
    db.close()
    result = [product_payload(row) for row in rows]
    if page is None:
        return jsonify(result)
    return jsonify({
        "products": result,
        "total": count,
        "page": page,
        "pages": math.ceil(count / limit)
    })


@app.get("/api/products/<int:product_id>")
def product_detail(product_id):
    db = connect()
    row = db.execute("""
        SELECT p.* FROM products p
        LEFT JOIN sellers s ON s.user_id = p.seller_id
        WHERE p.id = ? AND p.active = 1
          AND (p.seller_id IS NULL OR s.status = 'approved')
    """, (product_id,)).fetchone()
    db.close()
    if not row:
        return error("Product not found.", 404)
    return jsonify(product_payload(row))


@app.get("/api/sellers/<int:seller_id>")
def seller_storefront(seller_id):
    db = connect()
    seller = db.execute("""
        SELECT s.user_id, s.shop_name, s.city, s.state, s.description
        FROM sellers s
        WHERE s.user_id = ? AND s.status = 'approved'
    """, (seller_id,)).fetchone()
    if not seller:
        db.close()
        return error("Seller storefront not found.", 404)
    product_count = db.execute("""
        SELECT COUNT(*) FROM products
        WHERE seller_id = ? AND active = 1 AND stock > 0
    """, (seller_id,)).fetchone()[0]
    db.close()
    return jsonify({**dict(seller), "available_products": product_count})


@app.get("/api/me")
def me():
    user = current_user()
    if user and user["role"] == "seller":
        db = connect()
        seller = db.execute(
            "SELECT status FROM sellers WHERE user_id = ?", (user["id"],)
        ).fetchone()
        db.close()
        user["seller_status"] = seller["status"] if seller else None
    return jsonify({"user": user})


@app.post("/api/register")
def register():
    data = request.get_json(silent=True) or {}
    name = str(data.get("name", "")).strip()
    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", ""))

    if not name or "@" not in email or len(password) < 6:
        return error("Enter a name, valid email, and password of at least 6 characters.")

    db = connect()
    try:
        cursor = db.execute("""
            INSERT INTO users(name, email, password)
            VALUES (?, ?, ?)
        """, (name, email, generate_password_hash(password)))
        db.commit()
        session.clear()
        session["user_id"] = cursor.lastrowid
    except sqlite3.IntegrityError:
        db.close()
        return error("That email is already registered.")
    db.close()
    return jsonify({"message": "Account created.", "user": current_user()})


@app.post("/api/login")
def login():
    data = request.get_json(silent=True) or {}
    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", ""))

    db = connect()
    user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    db.close()

    if not user or not check_password_hash(user["password"], password):
        return error("Incorrect email or password.", 401)

    session["user_id"] = user["id"]
    return jsonify({"message": "Logged in.", "user": current_user()})


@app.post("/api/logout")
def logout():
    session.clear()
    return jsonify({"message": "Logged out."})


def save_product_image(upload):
    if not upload or not upload.filename:
        return ""
    filename = secure_filename(upload.filename)
    extension = os.path.splitext(filename)[1].lower()
    if extension not in app.config["ALLOWED_IMAGE_EXTENSIONS"]:
        raise ValueError("Upload a JPG, PNG, or WebP image.")
    content = upload.stream.read(16)
    upload.stream.seek(0)
    valid_signatures = {
        ".jpg": content.startswith(b"\xff\xd8\xff"),
        ".jpeg": content.startswith(b"\xff\xd8\xff"),
        ".png": content.startswith(b"\x89PNG\r\n\x1a\n"),
        ".webp": content.startswith(b"RIFF") and content[8:12] == b"WEBP"
    }
    if not valid_signatures[extension]:
        raise ValueError("The uploaded file is not a valid image.")
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    saved_name = f"{uuid.uuid4().hex}{extension}"
    upload.save(os.path.join(app.config["UPLOAD_FOLDER"], saved_name))
    return f"/static/uploads/{saved_name}"


def product_form_values(data, existing=None):
    name = str(data.get("name", "")).strip()
    category = str(data.get("category", "")).strip()
    description = str(data.get("description", "")).strip()
    price = float(data.get("price", 0))
    stock = int(data.get("stock", 0))
    image = str(data.get("image", "")).strip()
    badge = str(data.get("badge", "")).strip()
    condition = str(data.get("condition", "new")).strip().lower()
    city = str(data.get("seller_city", "")).strip()
    state = str(data.get("seller_state", "")).strip()

    if not name or len(name) > 120 or category not in CATEGORIES:
        raise ValueError("Enter a product name and choose a valid category.")
    if not math.isfinite(price) or price <= 0 or price > 10000000:
        raise ValueError("Enter a valid price greater than ₹0.")
    if stock < 0 or stock > 1000000:
        raise ValueError("Enter a valid stock quantity.")
    if condition not in {"new", "handmade"}:
        raise ValueError("Choose a valid product condition.")
    if image and not image.startswith(("http://", "https://", "/static/uploads/")):
        raise ValueError("Use an http(s) image URL or upload an image file.")
    uploaded = request.files.get("image_file")
    if uploaded and uploaded.filename:
        image = save_product_image(uploaded)
    elif existing and not image:
        image = existing["image"] or ""
    handmade = condition == "handmade" or data.get("handmade") == "on"
    made_in_india = data.get("made_in_india") == "on"
    attributes = {
        "brand": str(data.get("brand", "")).strip()[:80],
        "size": str(data.get("size", "")).strip()[:40],
        "color": str(data.get("color", "")).strip()[:40],
        "condition": condition,
        "handmade": handmade,
        "made_in_india": made_in_india
    }
    if handmade:
        badge = "Handmade"
    elif made_in_india:
        badge = "Made in India"
    else:
        badge = ""
    return (
        name, category, price, stock, image, description,
        badge, city, state, attributes
    )


@app.post("/api/seller/register")
def register_seller():
    user = current_user()
    if not user:
        return error("Create an account or log in before applying to sell.", 401)
    if user["role"] == "admin":
        return error("Administrator accounts cannot register as sellers.")
    data = request.get_json(silent=True) or {}
    phone = str(data.get("phone", "")).strip()
    shop_name = str(data.get("shop_name", "")).strip()
    city = str(data.get("city", "")).strip()
    state = str(data.get("state", "")).strip()
    description = str(data.get("description", "")).strip()
    digits = "".join(character for character in phone if character.isdigit())
    if not phone or not 7 <= len(digits) <= 15 or not shop_name or not city or not state:
        return error("Enter a valid phone number, shop name, city, and state.")

    db = connect()
    existing = db.execute(
        "SELECT status FROM sellers WHERE user_id = ?", (user["id"],)
    ).fetchone()
    if existing:
        db.close()
        return error("Your seller application has already been submitted.")
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    db.execute("""
        INSERT INTO sellers(user_id, phone, shop_name, city, state, description, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, 'pending', ?)
    """, (user["id"], phone, shop_name, city, state, description, now))
    db.execute("UPDATE users SET role = 'seller', phone = ? WHERE id = ?",
               (phone, user["id"]))
    db.commit()
    db.close()
    return jsonify({"message": "Seller application submitted for admin approval.", "status": "pending"}), 201


@app.get("/api/seller/dashboard")
def seller_dashboard():
    user = current_user()
    if not user or user["role"] != "seller":
        return error("Seller account required.", 403)
    db = connect()
    seller = db.execute(
        "SELECT * FROM sellers WHERE user_id = ?", (user["id"],)
    ).fetchone()
    if not seller:
        db.close()
        return error("Seller profile not found.", 404)
    listings = [
        product_payload(row) for row in db.execute(
            "SELECT * FROM products WHERE seller_id = ? ORDER BY id DESC",
            (user["id"],)
        ).fetchall()
    ]
    orders = db.execute("""
        SELECT o.id, o.created_at, oi.product_name, oi.quantity, oi.price,
               sos.status AS seller_status
        FROM order_items oi
        JOIN orders o ON o.id = oi.order_id
        LEFT JOIN seller_order_status sos
          ON sos.order_id = o.id AND sos.seller_id = oi.seller_id
        WHERE oi.seller_id = ?
        ORDER BY o.id DESC
    """, (user["id"],)).fetchall()
    summary = db.execute("""
        SELECT COUNT(DISTINCT o.id) AS orders,
               COALESCE(SUM(oi.price * oi.quantity), 0) AS sales
        FROM order_items oi JOIN orders o ON o.id = oi.order_id
        WHERE oi.seller_id = ? AND o.status != 'Cancelled'
    """, (user["id"],)).fetchone()
    db.close()
    return jsonify({
        "seller": dict(seller),
        "products": listings,
        "orders": [dict(row) for row in orders],
        "summary": dict(summary)
    })


@app.post("/api/seller/products")
def create_seller_product():
    user = current_user()
    if not user or user["role"] != "seller" or not seller_is_approved(user["id"]):
        return error("An approved seller account is required to list products.", 403)
    try:
        values = product_form_values(request.form)
        name, category, price, stock, image, description, badge, city, state, attributes = values
        seller = connect()
        profile = seller.execute(
            "SELECT shop_name, city, state FROM sellers WHERE user_id = ?",
            (user["id"],)
        ).fetchone()
        seller.close()
        if not profile:
            return error("Seller profile not found.", 404)
        db = connect()
        cursor = db.execute("""
            INSERT INTO products(
                name, category, price, image, stock, description, seller_id,
                seller_name, seller_city, seller_state, source, active, badge, attributes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'seller', 1, ?, ?)
        """, (
            name, category, price, image, stock, description, user["id"],
            profile["shop_name"], city or profile["city"], state or profile["state"],
            badge, json.dumps(attributes)
        ))
        db.commit()
        product_id = cursor.lastrowid
        db.close()
        return jsonify({"message": "Product listing created.", "id": product_id}), 201
    except (TypeError, ValueError) as exc:
        return error(str(exc) or "Enter valid product details.")


@app.put("/api/seller/products/<int:product_id>")
def edit_seller_product(product_id):
    user = current_user()
    if not user or user["role"] != "seller" or not seller_is_approved(user["id"]):
        return error("An approved seller account is required.", 403)
    db = connect()
    existing = db.execute(
        "SELECT * FROM products WHERE id = ? AND seller_id = ?",
        (product_id, user["id"])
    ).fetchone()
    db.close()
    if not existing:
        return error("Product not found.", 404)
    try:
        values = product_form_values(request.form, existing)
        name, category, price, stock, image, description, badge, city, state, attributes = values
        db = connect()
        db.execute("""
            UPDATE products SET name = ?, category = ?, price = ?, stock = ?,
                image = ?, description = ?, badge = ?, seller_city = ?,
                seller_state = ?, attributes = ?
            WHERE id = ? AND seller_id = ?
        """, (
            name, category, price, stock, image, description, badge,
            city or existing["seller_city"], state or existing["seller_state"],
            json.dumps(attributes), product_id, user["id"]
        ))
        db.commit()
        db.close()
        return jsonify({"message": "Product listing updated."})
    except (TypeError, ValueError) as exc:
        return error(str(exc) or "Enter valid product details.")


@app.delete("/api/seller/products/<int:product_id>")
def delete_seller_product(product_id):
    user = current_user()
    if not user or user["role"] != "seller" or not seller_is_approved(user["id"]):
        return error("An approved seller account is required.", 403)
    db = connect()
    cursor = db.execute(
        "UPDATE products SET active = 0 WHERE id = ? AND seller_id = ?",
        (product_id, user["id"])
    )
    db.commit()
    changed = cursor.rowcount
    db.close()
    if not changed:
        return error("Product not found.", 404)
    return jsonify({"message": "Product listing deactivated."})


@app.get("/api/seller/products/<int:product_id>")
def get_seller_product(product_id):
    user = current_user()
    if not user or user["role"] != "seller":
        return error("Seller account required.", 403)
    db = connect()
    product = db.execute(
        "SELECT * FROM products WHERE id = ? AND seller_id = ?",
        (product_id, user["id"])
    ).fetchone()
    db.close()
    if not product:
        return error("Product not found.", 404)
    return jsonify(product_payload(product))


@app.patch("/api/seller/products/<int:product_id>")
def toggle_seller_product(product_id):
    user = current_user()
    if not user or user["role"] != "seller" or not seller_is_approved(user["id"]):
        return error("An approved seller account is required.", 403)
    active = (request.get_json(silent=True) or {}).get("active")
    if not isinstance(active, bool):
        return error("Listing active status must be true or false.")
    db = connect()
    cursor = db.execute(
        "UPDATE products SET active = ? WHERE id = ? AND seller_id = ?",
        (int(active), product_id, user["id"])
    )
    db.commit()
    db.close()
    if not cursor.rowcount:
        return error("Product not found.", 404)
    return jsonify({"message": "Listing status updated.", "active": active})


@app.patch("/api/seller/orders/<int:order_id>")
def update_seller_order(order_id):
    user = current_user()
    if not user or user["role"] != "seller" or not seller_is_approved(user["id"]):
        return error("An approved seller account is required.", 403)
    status = (request.get_json(silent=True) or {}).get("status")
    seller_statuses = {"Order Placed", "Confirmed", "Preparing", "Ready to Ship"}
    if status not in seller_statuses:
        return error("Sellers may set an order to Confirmed, Preparing, or Ready to Ship.")
    db = connect()
    owns_items = db.execute(
        "SELECT 1 FROM order_items WHERE order_id = ? AND seller_id = ? LIMIT 1",
        (order_id, user["id"])
    ).fetchone()
    if not owns_items:
        db.close()
        return error("Order not found.", 404)
    db.execute("""
        INSERT INTO seller_order_status(order_id, seller_id, status, updated_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(order_id, seller_id) DO UPDATE SET
            status = excluded.status, updated_at = excluded.updated_at
    """, (
        order_id, user["id"], status, datetime.now().strftime("%Y-%m-%d %H:%M")
    ))
    db.commit()
    db.close()
    return jsonify({"message": "Your order preparation status was updated."})


@app.post("/api/orders")
def create_order():
    user = current_user()
    if not user:
        return error("Please log in before placing an order.", 401)

    data = request.get_json(silent=True) or {}
    name = str(data.get("name", "")).strip()
    phone = str(data.get("phone", "")).strip()
    address = str(data.get("address", "")).strip()
    city = str(data.get("city", "")).strip()
    state = str(data.get("state", "")).strip()
    pin_code = str(data.get("pin_code", "")).strip()
    items = data.get("items", [])

    digits = "".join(character for character in phone if character.isdigit())
    if not name or not 7 <= len(digits) <= 15 or not address:
        return error("Enter a recipient name, valid phone number, and delivery address.")
    if not city or not state or len(pin_code) != 6 or not pin_code.isdigit():
        return error("Enter a city, state, and valid 6-digit PIN code.")
    if not isinstance(items, list) or not items:
        return error("Your cart is empty.")

    quantities = {}
    try:
        for item in items:
            product_id = int(item["id"])
            quantity = int(item["quantity"])
            if quantity < 1 or quantity > 20:
                return error("Each item quantity must be between 1 and 20.")
            quantities[product_id] = quantities.get(product_id, 0) + quantity
    except (KeyError, TypeError, ValueError):
        return error("Invalid cart data.")

    db = connect()
    try:
        db.execute("BEGIN IMMEDIATE")
        total = 0
        selected = []

        for product_id, quantity in quantities.items():
            product = db.execute(
                "SELECT * FROM products WHERE id = ? AND active = 1", (product_id,)
            ).fetchone()

            if not product:
                raise ValueError("A product in your cart no longer exists.")
            if product["stock"] < quantity:
                raise ValueError(f"Not enough stock for {product['name']}.")

            selected.append((product, quantity))
            total += product["price"] * quantity

        shipping = 0 if total >= 999 else 49
        total += shipping
        now = datetime.now()
        eta = now + timedelta(days=3)

        cursor = db.execute("""
            INSERT INTO orders(
                user_id, customer_name, phone, address, city, state, pin_code, total,
                status, created_at, eta
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user["id"], name, phone, address, city, state, pin_code, total,
            "Order Placed", now.strftime("%Y-%m-%d %H:%M"),
            eta.strftime("%Y-%m-%d")
        ))
        order_id = cursor.lastrowid

        for product, quantity in selected:
            db.execute("""
                INSERT INTO order_items(
                    order_id, product_id, product_name, price, quantity, seller_id
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                order_id, product["id"], product["name"],
                product["price"], quantity, product["seller_id"]
            ))
            db.execute(
                "UPDATE products SET stock = stock - ? WHERE id = ?",
                (quantity, product["id"])
            )

        for seller_id in {
            product["seller_id"] for product, _ in selected
            if product["seller_id"] is not None
        }:
            db.execute("""
                INSERT INTO seller_order_status(order_id, seller_id, status, updated_at)
                VALUES (?, ?, 'Order Placed', ?)
            """, (order_id, seller_id, now.strftime("%Y-%m-%d %H:%M")))

        db.execute("""
            INSERT INTO tracking_events(order_id, status, event_time)
            VALUES (?, ?, ?)
        """, (order_id, "Order Placed", now.strftime("%Y-%m-%d %H:%M")))

        db.commit()
        return jsonify({
            "message": "Order placed successfully!",
            "order_id": order_id,
            "total": round(total, 2),
            "shipping": shipping,
            "eta": eta.strftime("%Y-%m-%d")
        }), 201

    except ValueError as exc:
        db.rollback()
        return error(str(exc))
    except Exception:
        db.rollback()
        app.logger.exception("Checkout failed")
        return error("Could not place order. Please try again.", 500)
    finally:
        db.close()


@app.get("/api/orders")
def my_orders():
    user = current_user()
    if not user:
        return error("Please log in.", 401)

    db = connect()
    orders = db.execute("""
        SELECT * FROM orders WHERE user_id = ? ORDER BY id DESC
    """, (user["id"],)).fetchall()

    result = []
    for order in orders:
        row = dict(order)
        row["items"] = [
            dict(item) for item in db.execute("""
                SELECT oi.product_name, oi.price, oi.quantity,
                       COALESCE(p.seller_name, 'Aikya Demo Store') AS seller_name,
                       COALESCE(sos.status, o.status) AS seller_status
                FROM order_items oi
                LEFT JOIN products p ON p.id = oi.product_id
                LEFT JOIN seller_order_status sos
                  ON sos.order_id = oi.order_id AND sos.seller_id = oi.seller_id
                JOIN orders o ON o.id = oi.order_id
                WHERE oi.order_id = ?
            """, (order["id"],)).fetchall()
        ]
        row["events"] = [
            dict(event) for event in db.execute("""
                SELECT status, event_time FROM tracking_events
                WHERE order_id = ? ORDER BY id
            """, (order["id"],)).fetchall()
        ]
        result.append(row)

    db.close()
    return jsonify(result)


@app.get("/api/orders/<int:order_id>")
def track_order(order_id):
    user = current_user()
    if not user:
        return error("Please log in.", 401)

    db = connect()
    order = db.execute(
        "SELECT * FROM orders WHERE id = ?", (order_id,)
    ).fetchone()

    if not order or (
        user["role"] != "admin" and order["user_id"] != user["id"]
    ):
        db.close()
        return error("Order not found.", 404)

    result = dict(order)
    result["items"] = [
        dict(row) for row in db.execute("""
            SELECT oi.product_name, oi.price, oi.quantity,
                   COALESCE(p.seller_name, 'Aikya Demo Store') AS seller_name,
                   COALESCE(sos.status, o.status) AS seller_status
            FROM order_items oi
            LEFT JOIN products p ON p.id = oi.product_id
            LEFT JOIN seller_order_status sos
              ON sos.order_id = oi.order_id AND sos.seller_id = oi.seller_id
            JOIN orders o ON o.id = oi.order_id
            WHERE oi.order_id = ?
        """, (order_id,)).fetchall()
    ]
    result["events"] = [
        dict(row) for row in db.execute("""
            SELECT status, event_time FROM tracking_events
            WHERE order_id = ? ORDER BY id
        """, (order_id,)).fetchall()
    ]
    db.close()
    return jsonify(result)


@app.get("/api/admin/summary")
def admin_summary():
    user = current_user()
    if not user or user["role"] != "admin":
        return error("Admin access required.", 403)

    db = connect()
    result = {
        "products": db.execute("SELECT COUNT(*) FROM products").fetchone()[0],
        "sellers": db.execute("SELECT COUNT(*) FROM sellers WHERE status = 'approved'").fetchone()[0],
        "total_sellers": db.execute("SELECT COUNT(*) FROM sellers").fetchone()[0],
        "pending_sellers": db.execute("SELECT COUNT(*) FROM sellers WHERE status = 'pending'").fetchone()[0],
        "low_stock": db.execute(
            "SELECT COUNT(*) FROM products WHERE active = 1 AND stock <= 5"
        ).fetchone()[0],
        "orders": db.execute("SELECT COUNT(*) FROM orders").fetchone()[0],
        "customers": db.execute(
            "SELECT COUNT(*) FROM users WHERE role = 'customer'"
        ).fetchone()[0],
        "revenue": db.execute(
            "SELECT COALESCE(SUM(total), 0) FROM orders WHERE status != 'Cancelled'"
        ).fetchone()[0],
        "sellers_list": [
            dict(row) for row in db.execute("""
                SELECT s.user_id, u.name, u.email, s.phone, s.shop_name,
                       s.city, s.state, s.description, s.status, s.created_at
                FROM sellers s JOIN users u ON u.id = s.user_id
                ORDER BY CASE s.status WHEN 'pending' THEN 0 ELSE 1 END, s.created_at DESC
            """).fetchall()
        ],
        "low_stock_list": [
            dict(row) for row in db.execute("""
                SELECT id, name, stock, category FROM products
                WHERE active = 1 AND stock <= 5 ORDER BY stock, name
            """).fetchall()
        ],
        "orders_list": [
            dict(row) for row in db.execute("""
                SELECT id, customer_name, total, status, created_at
                FROM orders ORDER BY id DESC
            """).fetchall()
        ],
        "order_statuses": {
            row["status"]: row["count"] for row in db.execute("""
                SELECT status, COUNT(*) AS count FROM orders GROUP BY status
            """).fetchall()
        },
        "products_list": [
            dict(row) for row in db.execute("""
                SELECT id, name, category, stock, active, source
                FROM products ORDER BY id DESC
            """).fetchall()
        ]
    }
    db.close()
    return jsonify(result)


@app.patch("/api/admin/sellers/<int:seller_id>")
def update_seller_status(seller_id):
    user = current_user()
    if not user or user["role"] != "admin":
        return error("Admin access required.", 403)
    status = (request.get_json(silent=True) or {}).get("status")
    if status not in {"approved", "rejected", "suspended"}:
        return error("Seller status must be approved, rejected, or suspended.")
    db = connect()
    seller = db.execute(
        "SELECT user_id FROM sellers WHERE user_id = ?", (seller_id,)
    ).fetchone()
    if not seller:
        db.close()
        return error("Seller application not found.", 404)
    db.execute("UPDATE sellers SET status = ? WHERE user_id = ?", (status, seller_id))
    db.execute("UPDATE users SET role = 'seller' WHERE id = ?", (seller_id,))
    db.commit()
    db.close()
    return jsonify({"message": f"Seller {status}.", "status": status})


@app.patch("/api/admin/products/<int:product_id>")
def moderate_product(product_id):
    user = current_user()
    if not user or user["role"] != "admin":
        return error("Admin access required.", 403)
    data = request.get_json(silent=True) or {}
    active = data.get("active")
    if not isinstance(active, bool):
        return error("Product active status must be true or false.")
    db = connect()
    cursor = db.execute(
        "UPDATE products SET active = ? WHERE id = ?",
        (int(active), product_id)
    )
    db.commit()
    db.close()
    if not cursor.rowcount:
        return error("Product not found.", 404)
    return jsonify({"message": "Product listing updated.", "active": active})


@app.patch("/api/admin/orders/<int:order_id>")
def update_order(order_id):
    user = current_user()
    if not user or user["role"] != "admin":
        return error("Admin access required.", 403)

    data = request.get_json(silent=True) or {}
    status = data.get("status")
    if status not in STATUSES:
        return error("Invalid order status.")

    db = connect()
    order = db.execute(
        "SELECT id, status FROM orders WHERE id = ?", (order_id,)
    ).fetchone()

    if not order:
        db.close()
        return error("Order not found.", 404)

    if order["status"] == "Cancelled" and status != "Cancelled":
        db.close()
        return error("Cancelled orders cannot be reopened.")

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    db.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))
    db.execute("""
        INSERT INTO tracking_events(order_id, status, event_time)
        VALUES (?, ?, ?)
    """, (order_id, status, now))
    db.commit()
    db.close()
    return jsonify({"message": "Order status updated.", "status": status})


@app.post("/api/admin/products")
def add_product():
    user = current_user()
    if not user or user["role"] != "admin":
        return error("Admin access required.", 403)

    data = request.get_json(silent=True) or {}
    try:
        name = str(data["name"]).strip()
        category = str(data["category"])
        price = float(data["price"])
        stock = int(data["stock"])
        image = str(data.get("image", "")).strip()

        if (not name or category not in CATEGORIES or not math.isfinite(price)
                or price <= 0 or price > 10000000 or stock < 0 or stock > 1000000):
            return error("Check the product name, category, price, and stock.")

        db = connect()
        cursor = db.execute("""
            INSERT INTO products(
                name, category, price, image, stock, description,
                seller_name, source, badge
            ) VALUES (?, ?, ?, ?, ?, ?, 'Aikya Admin', 'admin', 'Aikya curated')
        """, (
            name, category, price, image, stock,
            "Admin-added catalogue product."
        ))
        db.commit()
        product_id = cursor.lastrowid
        db.close()
        return jsonify({"message": "Product added.", "id": product_id}), 201
    except (KeyError, TypeError, ValueError):
        return error("Enter valid product details.")


if __name__ == "__main__":
    init_db()
    app.run(debug=False, port=5000)
