import os
import sqlite3
import tempfile
import unittest

import app as marketplace


class MarketplaceTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database = os.path.join(self.temp_dir.name, "marketplace.db")
        marketplace.app.config.update(
            TESTING=True,
            DATABASE=self.database,
            UPLOAD_FOLDER=os.path.join(self.temp_dir.name, "uploads"),
            SECRET_KEY="test-only-secret"
        )
        marketplace.init_db()
        self.client = marketplace.app.test_client()

    def tearDown(self):
        self.temp_dir.cleanup()

    def post_json(self, path, payload):
        return self.client.post(path, json=payload)

    def register(self, name, email):
        response = self.post_json("/api/register", {
            "name": name, "email": email, "password": "test-password"
        })
        self.assertEqual(response.status_code, 200, response.get_json())
        return response.get_json()["user"]

    def login_admin(self):
        response = self.post_json("/api/login", {
            "email": "admin@example.com", "password": "Admin@12345"
        })
        self.assertEqual(response.status_code, 200, response.get_json())

    def approve_seller(self, email):
        db = sqlite3.connect(self.database)
        seller_id = db.execute(
            "SELECT id FROM users WHERE email = ?", (email,)
        ).fetchone()[0]
        db.close()
        self.login_admin()
        response = self.client.patch(
            f"/api/admin/sellers/{seller_id}", json={"status": "approved"}
        )
        self.assertEqual(response.status_code, 200, response.get_json())
        self.client.post("/api/logout")
        return seller_id

    def apply_seller(self, email, shop_name):
        self.register(shop_name, email)
        response = self.post_json("/api/seller/register", {
            "phone": "9876543210",
            "shop_name": shop_name,
            "city": "Jaipur",
            "state": "Rajasthan",
            "description": "A test seller profile"
        })
        self.assertEqual(response.status_code, 201, response.get_json())

    def test_catalog_has_all_categories_and_paginated_demo_products(self):
        categories = self.client.get("/api/categories").get_json()
        catalog = self.client.get(
            "/api/products?category=All&page=1&limit=48"
        ).get_json()
        self.assertEqual(len(categories), 14)
        self.assertGreaterEqual(catalog["total"], 60)
        self.assertEqual(catalog["page"], 1)
        self.assertGreaterEqual(catalog["pages"], 2)
        self.assertTrue(all(category["description"] for category in categories))

    def test_seller_approval_listing_ownership_and_order_preparation(self):
        self.apply_seller("seller-one@example.test", "Mitti Studio")
        pending = self.client.post("/api/seller/products", data={
            "name": "Handmade bowl",
            "category": "Indian Handicrafts",
            "description": "A small handmade bowl.",
            "price": "500",
            "stock": "4",
            "condition": "handmade"
        })
        self.assertEqual(pending.status_code, 403)

        seller_id = self.approve_seller("seller-one@example.test")
        self.client.post("/api/login", json={
            "email": "seller-one@example.test", "password": "test-password"
        })
        created = self.client.post("/api/seller/products", data={
            "name": "Handmade bowl",
            "category": "Indian Handicrafts",
            "description": "A small handmade bowl.",
            "price": "500",
            "stock": "4",
            "condition": "handmade",
            "made_in_india": "on"
        })
        self.assertEqual(created.status_code, 201, created.get_json())
        product_id = created.get_json()["id"]
        product = self.client.get(f"/api/products/{product_id}").get_json()
        self.assertEqual(product["seller_id"], seller_id)
        self.assertEqual(product["seller_name"], "Mitti Studio")
        self.assertEqual(product["badge"], "Handmade")

        self.client.post("/api/logout")
        self.apply_seller("seller-two@example.test", "Second Shop")
        second_seller_id = self.approve_seller("seller-two@example.test")
        self.client.post("/api/login", json={
            "email": "seller-two@example.test", "password": "test-password"
        })
        denied = self.client.get(f"/api/seller/products/{product_id}")
        self.assertEqual(denied.status_code, 404)
        denied_edit = self.client.put(f"/api/seller/products/{product_id}", data={
            "name": "Stolen listing",
            "category": "Indian Handicrafts",
            "price": "1",
            "stock": "1"
        })
        self.assertEqual(denied_edit.status_code, 404)
        self.assertNotEqual(seller_id, second_seller_id)

    def test_checkout_uses_database_price_and_updates_stock(self):
        customer = self.register("Buyer", "buyer@example.test")
        db = sqlite3.connect(self.database)
        product_id, price, stock = db.execute(
            "SELECT id, price, stock FROM products WHERE name = ?",
            ("Cotton Anarkali Kurta",)
        ).fetchone()
        db.close()
        response = self.post_json("/api/orders", {
            "name": customer["name"],
            "phone": "9876543210",
            "address": "12 Demo Road",
            "city": "Jaipur",
            "state": "Rajasthan",
            "pin_code": "302001",
            "items": [{"id": product_id, "quantity": 1, "price": 0.01}]
        })
        self.assertEqual(response.status_code, 201, response.get_json())
        self.assertEqual(response.get_json()["total"], price)
        db = sqlite3.connect(self.database)
        updated_stock = db.execute(
            "SELECT stock FROM products WHERE id = ?", (product_id,)
        ).fetchone()[0]
        db.close()
        self.assertEqual(updated_stock, stock - 1)
        orders = self.client.get("/api/orders").get_json()
        self.assertEqual(orders[0]["pin_code"], "302001")
        self.assertEqual(orders[0]["items"][0]["seller_name"], "Nila Textiles")

    def test_legacy_schema_migrates_without_erasing_customer_data(self):
        legacy_path = os.path.join(self.temp_dir.name, "legacy.db")
        db = sqlite3.connect(legacy_path)
        db.executescript("""
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL, email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL, role TEXT NOT NULL DEFAULT 'customer'
            );
            CREATE TABLE products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL, category TEXT NOT NULL, price REAL NOT NULL,
                image TEXT, stock INTEGER NOT NULL DEFAULT 0,
                description TEXT DEFAULT ''
            );
            CREATE TABLE orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
                customer_name TEXT NOT NULL, phone TEXT NOT NULL,
                address TEXT NOT NULL, total REAL NOT NULL,
                status TEXT NOT NULL DEFAULT 'Order Placed',
                created_at TEXT NOT NULL, eta TEXT NOT NULL
            );
            CREATE TABLE order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT, order_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL, product_name TEXT NOT NULL,
                price REAL NOT NULL, quantity INTEGER NOT NULL
            );
            CREATE TABLE tracking_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT, order_id INTEGER NOT NULL,
                status TEXT NOT NULL, event_time TEXT NOT NULL
            );
            INSERT INTO users(name, email, password) VALUES
                ('Legacy Buyer', 'legacy@example.test', 'hashed-password');
            INSERT INTO products(name, category, price, stock) VALUES
                ('Legacy Kurta', 'Dresses', 799, 3);
        """)
        db.commit()
        db.close()
        marketplace.app.config["DATABASE"] = legacy_path
        marketplace.init_db()
        db = sqlite3.connect(legacy_path)
        customer = db.execute(
            "SELECT name FROM users WHERE email = 'legacy@example.test'"
        ).fetchone()
        product = db.execute(
            "SELECT category, stock FROM products WHERE name = 'Legacy Kurta'"
        ).fetchone()
        db.close()
        self.assertEqual(customer[0], "Legacy Buyer")
        self.assertEqual(product, ("Clothing and Ethnic Wear", 3))


if __name__ == "__main__":
    unittest.main()
