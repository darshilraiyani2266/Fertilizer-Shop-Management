from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Required for session handling

# ✅ SQLite Database Path
DB_PATH = "data/shop.db"

# ✅ Connect to SQLite Database
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Enables dictionary-like access
    return conn

# ✅ Initialize SQLite Database
def init_db():
    os.makedirs("data", exist_ok=True)  # Ensure the data folder exists
    conn = get_db()
    cursor = conn.cursor()

    # Create Users Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
    """)

    # Create Orders Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_email TEXT NOT NULL,
        name TEXT NOT NULL,
        address TEXT NOT NULL,
        mobile TEXT NOT NULL,
        total_amount REAL NOT NULL,
        payment_method TEXT NOT NULL,
        order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    

    conn.commit()
    conn.close()

# ✅ Fertilizer Data (Temporary, replace with database fetching later)
fertilizers = [
    {"id": 1, "name": "Urea", "price": 1220, "image": "images/urea.jpg"},
    {"id": 2, "name": "DAP", "price": 1350, "image": "images/DAP.jpg"},
    {"id": 3, "name": "NPK", "price": 1225, "image": "images/npk.jpg"},
    {"id": 4, "name": "Organic Compost", "price": 1575, "image": "images/sakthi.jpg"},
    {"id": 5, "name": "Ammonium Nitrate", "price": 2200, "image": "images/next.jpg"},
    {"id": 6, "name": "Super Phosphate", "price": 2835, "image": "images/super.jpg"},
]

# ✅ Homepage Route
@app.route('/')
def home():
    return render_template('index.html')

# ✅ Product Page Route
@app.route('/products')
def products():
    return render_template('products.html', products=fertilizers)

# ✅ "Buy Now" Route (Redirects to Checkout with Selected Product)
@app.route('/buy_now/<int:product_id>')
def buy_now(product_id):
    for product in fertilizers:
        if product["id"] == product_id:
            session['cart'] = [product]  # Store only this product in cart
            session.modified = True
            return redirect(url_for('checkout'))  # Redirect to checkout page

# ✅ Add to Cart Route
@app.route('/add_to_cart/<int:product_id>')
def add_to_cart(product_id):
    if 'cart' not in session:
        session['cart'] = []
    
    for product in fertilizers:
        if product["id"] == product_id:
            session['cart'].append(product)
            session.modified = True
            flash(f"{product['name']} added to cart!", "success")
            break
    
    return redirect(url_for('cart'))

# ✅ Cart Page Route
@app.route('/cart')
def cart():
    cart_items = session.get('cart', [])
    total_price = sum(item['price'] for item in cart_items)
    return render_template('cart.html', cart_items=cart_items, total_price=total_price)

# ✅ Checkout Page Route
@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    cart_items = session.get('cart', [])
    if not cart_items:
        flash("Your cart is empty!", "warning")
        return redirect(url_for('products'))

    total_price = sum(item['price'] for item in cart_items)

    if request.method == 'POST':
        # Get user details from form
        name = request.form['name']
        address = request.form['address']
        mobile = request.form['mobile']
        payment_method = request.form['payment_method']

        if 'user_email' in session:
            user_email = session['user_email']
        else:
            user_email = "Guest"  # Default for non-logged-in users

        # Save order details in the database
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO orders (user_email, name, address, mobile, total_price, payment_method) VALUES (?, ?, ?, ?, ?, ?)",
            (user_email, name, address, mobile, total_price, payment_method)
)
        db.commit()
        db.close()

        # Clear the cart after order is placed
        session.pop('cart', None)

        return redirect(url_for('thank_you'))  # Redirect to Thank You page

    return render_template('checkout.html', cart_items=cart_items, total_price=total_price)

# ✅ Remove Item from Cart
@app.route('/remove_from_cart/<int:product_id>')
def remove_from_cart(product_id):
    if 'cart' in session:
        session['cart'] = [item for item in session['cart'] if item['id'] != product_id]
        session.modified = True  # Ensure session updates
    return redirect(url_for('cart'))

# ✅ Thank You Page Route
@app.route('/thank-you')
def thank_you():
    return render_template('thank_you.html')  # Render Thank You page

# ✅ Signup Route
@app.route('/signup', methods=['GET', 'POST'])  
def signup():
    if request.method == 'POST':  
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password != confirm_password:
            flash("Passwords do not match!", "danger")
            return render_template('signup.html')

        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        existing_user = cursor.fetchone()

        if existing_user:
            flash("Email already exists! Please login.", "danger")
            db.close()
            return redirect(url_for('login'))

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        cursor.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)", 
                       (username, email, hashed_password))
        db.commit()
        db.close()

        flash("Signup successful! Please log in.", "success")
        return redirect(url_for('login'))

    return render_template('signup.html')

# ✅ Login Route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        db.close()

        if user and check_password_hash(user["password"], password):
            session['user_id'] = user["id"]
            session['username'] = user["username"]
            session['user_email'] = user["email"]
            flash("Login successful!", "success")
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid email or password. Try again!", "danger")

    return render_template('login.html')

# ✅ Dashboard (Protected Page)
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash("Please log in first!", "danger")
        return redirect(url_for('login'))
    return render_template('index.html', username=session['username'])

# ✅ Logout Route
@app.route('/logout')
def logout():
    session.clear()
    flash("You have logged out successfully!", "info")
    return redirect(url_for('login'))

@app.route('/about')
def about():
    return render_template('about.html')


# ✅ Run App
if __name__ == '__main__':
    init_db()  # Ensure tables are created
    app.run(debug=True)
