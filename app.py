import os
import sqlite3
import json
import hashlib
import time
from flask import Flask, request, jsonify, send_from_directory, Response

app = Flask(__name__, static_folder=".")

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "greenleaf.db")

# -------------------------------------------------------------
# Database Setup & Initial Seeding
# -------------------------------------------------------------
def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    # Admins Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    """)

    # Plants Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS plants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            price REAL NOT NULL,
            oldPrice REAL NOT NULL,
            discount INTEGER DEFAULT 0,
            rating REAL DEFAULT 4.8,
            reviews INTEGER DEFAULT 50,
            image TEXT NOT NULL,
            description TEXT,
            type TEXT,
            light TEXT,
            water TEXT,
            suitable TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Orders Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_number TEXT UNIQUE NOT NULL,
            customer_name TEXT NOT NULL,
            customer_phone TEXT NOT NULL,
            customer_email TEXT,
            customer_pincode TEXT,
            customer_address TEXT NOT NULL,
            customer_city TEXT,
            customer_state TEXT,
            payment_method TEXT NOT NULL,
            total_amount REAL NOT NULL,
            status TEXT DEFAULT 'Pending',
            items_json TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Contacts Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            subject TEXT,
            message TEXT NOT NULL,
            is_read INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Default Admin (admin / admin123)
    cursor.execute("SELECT id FROM admins WHERE username = 'admin'")
    if not cursor.fetchone():
        pwd_hash = hashlib.sha256("admin123".encode("utf-8")).hexdigest()
        cursor.execute("INSERT INTO admins (username, password_hash) VALUES (?, ?)", ("admin", pwd_hash))

    # Seed Initial 26 Plants if table is empty
    cursor.execute("SELECT COUNT(*) as count FROM plants")
    count = cursor.fetchone()["count"]

    if count == 0:
        initial_plants = [
            {"name": "Snake Plant", "category": "indoor", "price": 399, "oldPrice": 499, "discount": 20, "rating": 4.8, "reviews": 128, "image": "https://wallpapers.com/images/file/snake-plant-pictures-3389-x-3390-jxv4jggvch0js7g8.jpg", "description": "A hardy indoor plant that is easy to maintain and perfect for modern homes.", "type": "Indoor Plant", "light": "Low to Bright", "water": "Low", "suitable": "Home & Office"},
            {"name": "Monstera", "category": "indoor", "price": 699, "oldPrice": 899, "discount": 22, "rating": 4.9, "reviews": 214, "image": "https://i.pinimg.com/originals/b2/13/5b/b2135b481652017433accd3d5a6ab327.jpg", "description": "A tropical plant with beautiful split leaves that creates a fresh indoor atmosphere.", "type": "Tropical", "light": "Indirect", "water": "Medium", "suitable": "Living Room"},
            {"name": "Peace Lily", "category": "flowering", "price": 499, "oldPrice": 649, "discount": 23, "rating": 4.7, "reviews": 164, "image": "https://images.unsplash.com/photo-1593482892290-f54927ae1bf6?auto=format&fit=crop&w=800&q=80", "description": "An elegant flowering plant known for its beautiful white flowers and green leaves.", "type": "Flowering", "light": "Medium", "water": "Medium", "suitable": "Indoor"},
            {"name": "Aloe Vera", "category": "succulent", "price": 299, "oldPrice": 399, "discount": 25, "rating": 4.8, "reviews": 191, "image": "https://images.unsplash.com/photo-1596547609652-9cf5d8d76921?auto=format&fit=crop&w=800&q=80", "description": "A useful succulent plant that requires minimal care and plenty of natural light.", "type": "Succulent", "light": "Bright", "water": "Low", "suitable": "Home"},
            {"name": "Areca Palm", "category": "indoor", "price": 899, "oldPrice": 1199, "discount": 25, "rating": 4.6, "reviews": 94, "image": "https://th.bing.com/th/id/OIP.5T8T115Myw5ye1CmVgl44wHaHa?w=184&h=184&c=7&r=0&o=7&dpr=1.3&pid=1.7&rm=3", "description": "A graceful palm that adds a tropical green touch to large indoor spaces.", "type": "Palm", "light": "Bright", "water": "Medium", "suitable": "Living Room"},
            {"name": "Money Plant", "category": "indoor", "price": 349, "oldPrice": 449, "discount": 22, "rating": 4.8, "reviews": 312, "image": "https://images.unsplash.com/photo-1614594975525-e45190c55d0b?auto=format&fit=crop&w=900&q=85", "description": "A popular easy-care plant with attractive trailing vines.", "type": "Climber", "light": "Indirect", "water": "Medium", "suitable": "Home & Office"},
            {"name": "Rose Plant", "category": "flowering", "price": 549, "oldPrice": 699, "discount": 21, "rating": 4.7, "reviews": 183, "image": "https://www.bing.com/th/id/OIP.VGrdXbZzCQZpq-np3mzgmAHaHa?w=193&h=193&c=8&rs=1&qlt=90&o=6&dpr=1.3&pid=ImgAns&rm=2", "description": "A classic flowering plant that brings colour and fragrance to your garden.", "type": "Flowering", "light": "Bright", "water": "Medium", "suitable": "Garden"},
            {"name": "Jade Plant", "category": "succulent", "price": 449, "oldPrice": 599, "discount": 25, "rating": 4.8, "reviews": 145, "image": "https://hips.hearstapps.com/hmg-prod/images/jade-plant-lucky-plant-money-plant-or-money-tree-royalty-free-image-1691772399.jpg", "description": "A compact succulent with thick green leaves and an attractive appearance.", "type": "Succulent", "light": "Bright", "water": "Low", "suitable": "Desk & Home"},
            {"name": "Rubber Plant", "category": "indoor", "price": 799, "oldPrice": 999, "discount": 20, "rating": 4.7, "reviews": 121, "image": "https://www.bing.com/th/id/OIP.QBPonppWm9l_r9grO_0pHAHaLH?w=193&h=290&c=8&rs=1&qlt=90&o=6&dpr=1.3&pid=ImgAns&rm=2", "description": "A bold indoor plant with large glossy leaves and a modern appearance.", "type": "Indoor", "light": "Indirect", "water": "Medium", "suitable": "Living Room"},
            {"name": "Lavender", "category": "flowering", "price": 599, "oldPrice": 799, "discount": 25, "rating": 4.9, "reviews": 202, "image": "https://images7.alphacoders.com/992/thumb-1920-992589.jpg", "description": "A fragrant flowering plant that brings a relaxing natural feel to your space.", "type": "Flowering", "light": "Bright", "water": "Low", "suitable": "Balcony"},
            {"name": "Cactus", "category": "succulent", "price": 249, "oldPrice": 349, "discount": 29, "rating": 4.6, "reviews": 109, "image": "https://th.bing.com/th/id/OIP.kUcYRWGvOooeN4veAoaMvQHaE8?w=288&h=192&c=7&r=0&o=7&dpr=1.3&pid=1.7&rm=3", "description": "A small low-maintenance plant suitable for desks and sunny windows.", "type": "Cactus", "light": "Bright", "water": "Very Low", "suitable": "Desk"},
            {"name": "Croton", "category": "outdoor", "price": 699, "oldPrice": 899, "discount": 22, "rating": 4.7, "reviews": 86, "image": "https://th.bing.com/th/id/OIP.XnhhP3s3ddxPmWCCnesEFwHaG_?w=211&h=199&c=7&r=0&o=7&dpr=1.3&pid=1.7&rm=3", "description": "A colourful foliage plant with vibrant leaves that brighten gardens and balconies.", "type": "Foliage", "light": "Bright", "water": "Medium", "suitable": "Garden"},
            {"name": "Hibiscus", "category": "flowering", "price": 499, "oldPrice": 649, "discount": 23, "rating": 4.8, "reviews": 176, "image": "https://images.unsplash.com/photo-1550950158-d0d960dff51b?auto=format&fit=crop&w=800&q=80", "description": "A beautiful flowering plant that produces colourful blooms in sunny locations.", "type": "Flowering", "light": "Bright", "water": "Medium", "suitable": "Garden"},
            {"name": "ZZ Plant", "category": "indoor", "price": 749, "oldPrice": 999, "discount": 25, "rating": 4.8, "reviews": 157, "image": "https://th.bing.com/th/id/OIP.mJNGT0Vj8LmxVNhe6RNOlAHaJQ?w=157&h=197&c=7&r=0&o=7&dpr=1.3&pid=1.7&rm=3", "description": "A highly adaptable indoor plant with attractive glossy foliage.", "type": "Indoor", "light": "Low to Medium", "water": "Low", "suitable": "Office"},
            {"name": "Boston Fern", "category": "outdoor", "price": 599, "oldPrice": 749, "discount": 20, "rating": 4.5, "reviews": 72, "image": "https://th.bing.com/th/id/OIP.NL_EbDXZKPj4j33pwg9F0gHaHa?w=163&h=180&c=7&r=0&o=7&dpr=1.3&pid=1.7&rm=3", "description": "A lush fern that adds a fresh and natural texture to shaded spaces.", "type": "Fern", "light": "Indirect", "water": "High", "suitable": "Balcony"},
            {"name": "Spider Plant", "category": "indoor", "price": 399, "oldPrice": 499, "discount": 20, "rating": 4.9, "reviews": 249, "image": "https://th.bing.com/th/id/OIP.sKjS-C57xwPLPWiVFjmcOAHaHa?w=268&h=201&c=7&r=0&o=7&dpr=1.3&pid=1.7&rm=3", "description": "A popular indoor plant with long arching leaves and easy maintenance.", "type": "Indoor", "light": "Indirect", "water": "Medium", "suitable": "Home & Office"},
            {"name": "Marigold", "category": "flowering", "price": 299, "oldPrice": 399, "discount": 25, "rating": 4.7, "reviews": 131, "image": "https://th.bing.com/th/id/OIP.-CMBMEOzhh7HDb7H3kqHDgHaD1?w=338&h=179&c=7&r=0&o=7&dpr=1.3&pid=1.7&rm=3", "description": "A cheerful flowering plant with bright blooms that looks beautiful in gardens.", "type": "Flowering", "light": "Bright", "water": "Medium", "suitable": "Garden"},
            {"name": "Bamboo Palm", "category": "outdoor", "price": 999, "oldPrice": 1299, "discount": 23, "rating": 4.6, "reviews": 64, "image": "https://images.unsplash.com/photo-1599725427295-6ed7aed89508?auto=format&fit=crop&w=800&q=80", "description": "A graceful palm that creates a refreshing tropical atmosphere.", "type": "Palm", "light": "Indirect", "water": "Medium", "suitable": "Home & Garden"},
            {"name": "Premium Orchid", "category": "flowering", "price": 1299, "oldPrice": 1699, "discount": 24, "rating": 4.9, "reviews": 98, "image": "https://cdnnew.igp.com/f_auto,q_auto,t_pnopt12prodlp/products/p-roses-and-orchid-bloom-arrangement-223307-m.jpg", "description": "A premium orchid with elegant flowers, perfect for interiors and gifting.", "type": "Orchid", "light": "Bright Indirect", "water": "Medium", "suitable": "Home & Gifts"},
            {"name": "Anthurium Red", "category": "flowering", "price": 1499, "oldPrice": 1899, "discount": 21, "rating": 4.8, "reviews": 87, "image": "https://images.unsplash.com/photo-1596547609652-9cf5d8d76921?auto=format&fit=crop&w=800&q=80", "description": "A premium flowering plant with striking red blooms and glossy leaves.", "type": "Flowering", "light": "Indirect", "water": "Medium", "suitable": "Living Room"},
            {"name": "Premium Rose Bush", "category": "flowering", "price": 1199, "oldPrice": 1599, "discount": 25, "rating": 4.7, "reviews": 75, "image": "https://th.bing.com/th/id/OIP.5jOnMdA5f7Xrvf4tNS14fAAAAA?w=132&h=150&c=7&r=0&o=7&dpr=1.3&pid=1.7&rm=3", "description": "A premium rose bush offering colourful blooms and an elegant garden appearance.", "type": "Rose", "light": "Bright", "water": "Medium", "suitable": "Garden"},
            {"name": "White Orchid", "category": "flowering", "price": 1799, "oldPrice": 2299, "discount": 22, "rating": 4.9, "reviews": 116, "image": "https://i.pinimg.com/originals/18/06/9e/18069ee6bd48285c983daaddf452d491.jpg", "description": "A beautiful premium white orchid ideal for elegant homes and special occasions.", "type": "Orchid", "light": "Indirect", "water": "Medium", "suitable": "Home & Gifts"},
            {"name": "Bougainvillea", "category": "flowering", "price": 1099, "oldPrice": 1399, "discount": 21, "rating": 4.6, "reviews": 83, "image": "https://cdn.mos.cms.futurecdn.net/mYt2WmKGT9wUNDoUbdYCqE.jpg", "description": "A colourful flowering plant that creates a vibrant garden display.", "type": "Flowering", "light": "Bright", "water": "Medium", "suitable": "Garden"},
            {"name": "Lucky Bamboo", "category": "indoor", "price": 599, "oldPrice": 799, "discount": 25, "rating": 4.8, "reviews": 224, "image": "https://www.aravalii.com/cdn/shop/files/lb-yo_92393879-477e-4be7-97ad-a96412215e97.jpg?v=1702107062&width=900", "description": "A stylish indoor plant suitable for desks, offices and modern interiors.", "type": "Indoor", "light": "Indirect", "water": "Medium", "suitable": "Office"},
            {"name": "Calathea", "category": "indoor", "price": 899, "oldPrice": 1199, "discount": 25, "rating": 4.7, "reviews": 118, "image": "https://th.bing.com/th/id/OIP.bCwiZToc_4JPZeZwN7rA4AHaJ4?w=137&h=183&c=7&r=0&o=7&dpr=1.3&pid=1.7&rm=3", "description": "A decorative tropical indoor plant with beautiful patterned foliage.", "type": "Tropical", "light": "Indirect", "water": "Medium", "suitable": "Home"},
            {"name": "Aglaonema", "category": "indoor", "price": 799, "oldPrice": 999, "discount": 20, "rating": 4.8, "reviews": 139, "image": "https://static-assets-prod.fnp.com/images/pr/l/v20260515114419/scarlet-aglaonema-plant_1.jpg", "description": "A beautiful low-maintenance foliage plant perfect for indoor spaces.", "type": "Foliage", "light": "Low to Medium", "water": "Medium", "suitable": "Office & Home"}
        ]

        for p in initial_plants:
            cursor.execute("""
                INSERT INTO plants (name, category, price, oldPrice, discount, rating, reviews, image, description, type, light, water, suitable)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (p["name"], p["category"], p["price"], p["oldPrice"], p["discount"], p["rating"], p["reviews"], p["image"], p["description"], p["type"], p["light"], p["water"], p["suitable"]))
    
    conn.commit()
    conn.close()

# -------------------------------------------------------------
# CORS Middleware
# -------------------------------------------------------------
@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    return response

# -------------------------------------------------------------
# Authentication Helper
# -------------------------------------------------------------
ACTIVE_TOKENS = {}

def verify_token(req):
    auth = req.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        token = auth[7:]
        if token in ACTIVE_TOKENS:
            return True
    return False

# -------------------------------------------------------------
# API Routes: Auth
# -------------------------------------------------------------
@app.route("/api/auth/login", methods=["POST", "OPTIONS"])
def admin_login():
    if request.method == "OPTIONS":
        return "", 200

    data = request.json or {}
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    pwd_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM admins WHERE username = ? AND password_hash = ?", (username, pwd_hash))
    admin = cursor.fetchone()
    conn.close()

    if admin:
        token = hashlib.sha256(f"{username}:{time.time()}".encode("utf-8")).hexdigest()
        ACTIVE_TOKENS[token] = username
        return jsonify({"success": True, "token": token, "username": username})
    
    return jsonify({"success": False, "error": "Invalid username or password"}), 401

@app.route("/api/auth/check", methods=["GET"])
def check_auth():
    if verify_token(request):
        return jsonify({"authenticated": True})
    return jsonify({"authenticated": False}), 401

# -------------------------------------------------------------
# API Routes: Plants (Public GET, Admin POST/PUT/DELETE)
# -------------------------------------------------------------
@app.route("/api/plants", methods=["GET"])
def get_plants():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM plants ORDER BY id ASC")
    rows = cursor.fetchall()
    conn.close()

    plants = []
    for r in rows:
        plants.append({
            "id": r["id"],
            "name": r["name"],
            "category": r["category"],
            "price": float(r["price"]),
            "oldPrice": float(r["oldPrice"]),
            "discount": int(r["discount"]),
            "rating": float(r["rating"]),
            "reviews": int(r["reviews"]),
            "image": r["image"],
            "description": r["description"] or "",
            "type": r["type"] or "",
            "light": r["light"] or "",
            "water": r["water"] or "",
            "suitable": r["suitable"] or ""
        })
    return jsonify(plants)

@app.route("/api/plants", methods=["POST", "OPTIONS"])
def add_plant():
    if request.method == "OPTIONS":
        return "", 200

    if not verify_token(request):
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json or {}
    name = data.get("name", "").strip()
    category = data.get("category", "indoor").strip()
    price = float(data.get("price", 0))
    oldPrice = float(data.get("oldPrice", price))
    discount = int(data.get("discount", 0))
    if discount == 0 and oldPrice > price and oldPrice > 0:
        discount = int(round(((oldPrice - price) / oldPrice) * 100))
    rating = float(data.get("rating", 4.8))
    reviews = int(data.get("reviews", 10))
    image = data.get("image", "https://images.unsplash.com/photo-1470058869958-2a77ade41c02?auto=format&fit=crop&w=800&q=80")
    description = data.get("description", "")
    ptype = data.get("type", "Indoor")
    light = data.get("light", "Bright")
    water = data.get("water", "Medium")
    suitable = data.get("suitable", "Home")

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO plants (name, category, price, oldPrice, discount, rating, reviews, image, description, type, light, water, suitable)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (name, category, price, oldPrice, discount, rating, reviews, image, description, ptype, light, water, suitable))
    plant_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return jsonify({"success": True, "id": plant_id, "message": "Plant added successfully"})

@app.route("/api/plants/<int:plant_id>", methods=["PUT", "DELETE", "OPTIONS"])
def manage_plant(plant_id):
    if request.method == "OPTIONS":
        return "", 200

    if not verify_token(request):
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_db()
    cursor = conn.cursor()

    if request.method == "DELETE":
        cursor.execute("DELETE FROM plants WHERE id = ?", (plant_id,))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "Plant deleted successfully"})

    if request.method == "PUT":
        data = request.json or {}
        name = data.get("name", "").strip()
        category = data.get("category", "indoor").strip()
        price = float(data.get("price", 0))
        oldPrice = float(data.get("oldPrice", price))
        discount = int(data.get("discount", 0))
        rating = float(data.get("rating", 4.8))
        reviews = int(data.get("reviews", 10))
        image = data.get("image", "")
        description = data.get("description", "")
        ptype = data.get("type", "")
        light = data.get("light", "")
        water = data.get("water", "")
        suitable = data.get("suitable", "")

        cursor.execute("""
            UPDATE plants 
            SET name = ?, category = ?, price = ?, oldPrice = ?, discount = ?, rating = ?, reviews = ?, image = ?, description = ?, type = ?, light = ?, water = ?, suitable = ?
            WHERE id = ?
        """, (name, category, price, oldPrice, discount, rating, reviews, image, description, ptype, light, water, suitable, plant_id))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "Plant updated successfully"})

# -------------------------------------------------------------
# API Routes: Orders (Public POST, Admin GET/PUT)
# -------------------------------------------------------------
@app.route("/api/orders", methods=["GET", "POST", "OPTIONS"])
def handle_orders():
    if request.method == "OPTIONS":
        return "", 200

    conn = get_db()
    cursor = conn.cursor()

    if request.method == "POST":
        data = request.json or {}
        order_num = "GL-" + str(int(time.time() * 1000))[-8:]
        name = data.get("customer_name", "Anonymous")
        phone = data.get("customer_phone", "")
        email = data.get("customer_email", "")
        pincode = data.get("customer_pincode", "")
        address = data.get("customer_address", "")
        city = data.get("customer_city", "")
        state = data.get("customer_state", "")
        payment = data.get("payment_method", "UPI")
        total = float(data.get("total_amount", 0))
        items = json.dumps(data.get("items", []))

        cursor.execute("""
            INSERT INTO orders (order_number, customer_name, customer_phone, customer_email, customer_pincode, customer_address, customer_city, customer_state, payment_method, total_amount, items_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (order_num, name, phone, email, pincode, address, city, state, payment, total, items))
        order_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return jsonify({"success": True, "order_id": order_num, "id": order_id, "message": "Order created successfully"})

    if request.method == "GET":
        if not verify_token(request):
            conn.close()
            return jsonify({"error": "Unauthorized"}), 401

        cursor.execute("SELECT * FROM orders ORDER BY id DESC")
        rows = cursor.fetchall()
        conn.close()

        orders = []
        for r in rows:
            orders.append({
                "id": r["id"],
                "order_number": r["order_number"],
                "customer_name": r["customer_name"],
                "customer_phone": r["customer_phone"],
                "customer_email": r["customer_email"],
                "customer_pincode": r["customer_pincode"],
                "customer_address": r["customer_address"],
                "customer_city": r["customer_city"],
                "customer_state": r["customer_state"],
                "payment_method": r["payment_method"],
                "total_amount": float(r["total_amount"]),
                "status": r["status"],
                "items": json.loads(r["items_json"]) if r["items_json"] else [],
                "created_at": r["created_at"]
            })
        return jsonify(orders)

@app.route("/api/orders/<int:order_id>/status", methods=["PUT", "OPTIONS"])
def update_order_status(order_id):
    if request.method == "OPTIONS":
        return "", 200

    if not verify_token(request):
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json or {}
    status = data.get("status", "Pending")

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))
    conn.commit()
    conn.close()

    return jsonify({"success": True, "message": "Status updated successfully"})

# -------------------------------------------------------------
# API Routes: Contacts (Public POST, Admin GET/PUT)
# -------------------------------------------------------------
@app.route("/api/contacts", methods=["GET", "POST", "OPTIONS"])
def handle_contacts():
    if request.method == "OPTIONS":
        return "", 200

    conn = get_db()
    cursor = conn.cursor()

    if request.method == "POST":
        data = request.json or {}
        name = data.get("name", "")
        email = data.get("email", "")
        subject = data.get("subject", "")
        message = data.get("message", "")

        cursor.execute("INSERT INTO contacts (name, email, subject, message) VALUES (?, ?, ?, ?)",
                       (name, email, subject, message))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "Inquiry submitted successfully"})

    if request.method == "GET":
        if not verify_token(request):
            conn.close()
            return jsonify({"error": "Unauthorized"}), 401

        cursor.execute("SELECT * FROM contacts ORDER BY id DESC")
        rows = cursor.fetchall()
        conn.close()

        contacts = [dict(r) for r in rows]
        return jsonify(contacts)

@app.route("/api/contacts/<int:contact_id>", methods=["DELETE", "OPTIONS"])
def delete_contact(contact_id):
    if request.method == "OPTIONS":
        return "", 200

    if not verify_token(request):
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM contacts WHERE id = ?", (contact_id,))
    conn.commit()
    conn.close()

    return jsonify({"success": True, "message": "Message deleted"})

# -------------------------------------------------------------
# API Routes: Dashboard Summary Stats (Admin)
# -------------------------------------------------------------
@app.route("/api/dashboard/stats", methods=["GET"])
def dashboard_stats():
    if not verify_token(request):
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) as count FROM plants")
    total_plants = cursor.fetchone()["count"]

    cursor.execute("SELECT COUNT(*) as count, COALESCE(SUM(total_amount), 0) as revenue FROM orders")
    order_data = cursor.fetchone()
    total_orders = order_data["count"]
    total_revenue = order_data["revenue"]

    cursor.execute("SELECT COUNT(*) as count FROM contacts")
    total_contacts = cursor.fetchone()["count"]

    cursor.execute("SELECT COUNT(*) as count FROM orders WHERE status = 'Pending'")
    pending_orders = cursor.fetchone()["count"]

    conn.close()

    return jsonify({
        "total_plants": total_plants,
        "total_orders": total_orders,
        "total_revenue": total_revenue,
        "total_contacts": total_contacts,
        "pending_orders": pending_orders
    })

# -------------------------------------------------------------
# Serve Static Frontend Files & Injected Storefront
# -------------------------------------------------------------
@app.route("/")
@app.route("/index.html")
def serve_index():
    index_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            content = f.read()
        # Non-invasive auto-injection of bridge.js right before </body>
        if "bridge.js" not in content:
            content = content.replace("</body>", '<script src="/bridge.js"></script>\n</body>')
        return Response(content, mimetype="text/html")
    return "GreenLeaf index.html not found.", 404

@app.route("/admin.html")
def serve_admin():
    return send_from_directory(".", "admin.html")

@app.route("/<path:path>")
def serve_static(path):
    return send_from_directory(".", path)

if __name__ == "__main__":
    init_db()
    print("🌱 GreenLeaf Backend Server running at http://localhost:5000")
    print("🌿 Storefront: http://localhost:5000")
    print("🔐 Admin Panel: http://localhost:5000/admin.html (Username: admin | Password: admin123)")
    app.run(host="0.0.0.0", port=5000, debug=False)
