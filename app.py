# app.py
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import re

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['UPLOAD_FOLDER'] = 'static/uploads/'  # Specify upload folder
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
db = SQLAlchemy(app)

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}  # Define allowed extensions
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)


    # Establish a relationship with Product
    products = db.relationship('Product', backref='category', lazy=True)


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(255), nullable=False)
    is_hero_product = db.Column(db.Boolean, default=False)  # New attribute
    file_path = db.Column(db.String(255), nullable=False)
    # Define the foreign key
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)


@app.route('/')
def index():
    products = Product.query.all()  # Fetch all images for trending products
    categories = Category.query.all()  # Fetch all categories
    hero_products = Product.query.filter_by(is_hero_product=True).all()  # Get hero products
    return render_template('index.html', products=products, categories=categories, hero_products=hero_products)

@app.route('/product')
def product():
    products = Product.query.all()
    return render_template('product.html', products = products)

@app.route('/category')
def category():
    categories = Category.query.all()
    return render_template('category.html', categories = categories)

@app.route('/Addproduct', methods=['GET', 'POST'])
def Addproduct():
    if request.method == 'POST':
        # Get form data
        name = request.form['name']  # Corrected to 'name'
        description = request.form['description']
        price = request.form['price']
        category_id = request.form['category']  # Get selected category
        is_hero_product = 'is_hero_product' in request.form  # Check if checkbox is checked
        
        # Handle the file upload
        file = request.files['file']
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

        # Create a new Product record
        new_product = Product(name=name, description=description, file_path=filename,
        price=price, category_id=category_id, is_hero_product=is_hero_product)

        # Add to the session and commit
        db.session.add(new_product)
        db.session.commit()
        
        return redirect(url_for('index'))
    
    # Fetch all categories for the dropdown
    categories = Category.query.all()
    return render_template('Addproduct.html', categories=categories) 

@app.route('/Addcategory', methods=['GET', 'POST'])
def Addcategory():
    if request.method == 'POST':
        # Get form data
        name = request.form['name']
        description = request.form['description']    
     # Handle the file upload
        file = request.files['file']
        
        if file and allowed_file (file.filename):  # Check if the file is valid
            # Secure the filename
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)  # Save the file to the specified path 
        # Create a new Image record
        new_category = Category(name=name, description=description, 
                             file_path=filename)
        
        # Add to the session and commit
        db.session.add(new_category)
        db.session.commit()
        
        
        flash('Category added successfully!', 'success')
        
        return redirect(url_for('index'))  # Redirect to a success page or home

    return render_template('Addcategory.html')  # Render the upload form


@app.route('/product/<int:product_id>', methods=['GET'])
def product_detail(product_id):
    # Get the product by ID
    product = Product.query.get(product_id)
    
    # Check if the product exists
    if not product:
        flash('Product not found.', 'error')  # Flash a message if product is not found
        return redirect(url_for('index'))  # Redirect to a valid page (e.g., index)

    # Get suggested products from the same category
    suggested_products = Product.query.filter(Product.category_id == product.category_id, Product.id != product.id).all()
    
    return render_template('product_details.html', product=product, suggested_products=suggested_products)

@app.route('/delete_product/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    product = Product.query.get(product_id)
    if product:
        # Construct the file path
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], product.file_path)
        
        # Remove the file from the filesystem
        # if os.path.exists(file_path):
        #     os.remove(file_path)

        # Remove the image record from the database
        db.session.delete(product)
        db.session.commit()
        
        flash('Image deleted successfully', 'success')
    else:
        flash('Image not found', 'danger')
    return redirect(url_for('index'))  # Redirect back to the index page

# Routes
# @app.route('/')
# def index():
#     return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Validate email format
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            flash('Invalid email format', 'danger')
            return redirect(url_for('signup'))
        
        # Validate password length
        if len(password) < 8:
            flash('Password must be at least 8 characters', 'danger')
            return redirect(url_for('signup'))

        # Check for duplicate username
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'danger')
            return redirect(url_for('signup'))

        # Check for duplicate email
        if User.query.filter_by(email=email).first():
            flash('Email already exists', 'danger')
            return redirect(url_for('signup'))
        
        # Create a new user
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password)
        )
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful!', 'success')
        return redirect(url_for('login'))
        
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            flash('Logged in successfully!')
            return redirect(url_for('index'))
        flash('Invalid username or password', 'danger')
        
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Logged out successfully')
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
