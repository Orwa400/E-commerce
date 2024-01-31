from flask import Flask, render_template, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, FloatField, IntegerField, PasswordField
from wtforms.validators import DataRequired, Length
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
import os
from paypalrestsdk import Payment
from datetime import datetime
from flask_paginate import Pagination

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager =LoginManager(app)
login_manager.login_view = 'login'

# Database Models
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    orders = db.relationship('Order', backref='user', lazy=True)


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, nullable=False)
    orders = db.relationship('OrderItem', backref='product', lazy=True)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', nullable=False))
    items = db.relationship('OrderItem', backref='order', lazy=True)
    total_price = db.Column(db.DateTime, default=datetime.utcnow)
    products = db.relationship('OrderProduct', backref='order', lazy=True)

class OrderProduct(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

    product = db.relationship('Product', backref='order_products')


class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)

    product = db.relationship('Product', backref='carts')
    user = db.relationship('User', backref='carts')

    
# Forms
class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Length(min=5, max=120)])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Sign Up')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Length(min=5, max=120)])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class ProductForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    description = TextAreaField('Description')
    price = FloatField('Price', validators=[DataRequired()])
    submit = SubmitField('Add Product')

class OrderForm(FlaskForm):
    product_id = IntegerField('Product ID', validators=[DataRequired()])
    quantity = IntegerField('Quantity', validators=[DataRequired()])
    submit = SubmitField('Add to Cart')

# Routes
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data, method='sha256')
        new_user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('Your account has been created! You can now log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user, remember=False)
            flash('Login successful!', 'succcess')
            return redirect(url_for('home'))
        else:
            flash('Login unsuccessful. Please check email and password', 'danger')

    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))



@app.route('/products', method=['GET', 'POST'])
def products():
    form = ProductForm()
    if form.validate_on_submit():
        new_product = Product(
            name = form.name.data,
            description = form.description.data,
            price = form.price.data
        )
        db.session.add(new_product)
        db.session.commit()
        return redirect(url_for('products'))

    products = Product.query.all()
    return render_template('products.html', products=products, form=form)


@app.route('/cart', methods=['GET', 'POST'])
def cart():
    if request.method == 'POST':
        form = OrderForm()
        if form.validate_on_submit():
            product_id = form.product_id.data
            quantity =form.quantity.data

            product = Product.query.get(product_id)
            if product:
                order_item = OrderItem(product=product, quantity=quantity)
                db.session.add(order_item)
                db.session.commit()
                return redirect(url_for('cart'))
    
    elif request.method == 'GET':
        form = OrderForm()
        cart_items = OrderItem.query.all()
        return render_template('cart.html', cart_items, form=form)

    
@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    product =Product.query.get_or_400(product_id)
    cart_item = Cart.query.filter_by(user_id=current_user.id, product_id=product.id).first()

    if cart_item:
        cart_item.quantity += 1
    else:
        new_cart_item = Cart(user_id=current_user.id, product_id=product.id)
        db.session.add(new_cart_item)

    db.session.commit()
    flash('Product added to cart successfully!', 'success')
    return redirect(url_for('products'))

@app.route('/remove_from_cart/<int:cart_id>', methods=['POST'])
@login_required
def remove_from_cart(cart_id):
    cart_item.quantity = Cart.query.get_or404(cart_id)


    if cart_item.quantity > 1:
        cart_item.quantity -= 1
    else:
        db.session.delete(cart_item)

    db.session.commit()
    flash('Product removed from cart successfully!', 'success')
    return redirect (url_for('view_cart'))

@app.route('/review_order')
@login_required
def review_order():
    user_cart = Cart.query.filter_by(user_id=current_user.id)
    total_price = sum(item.product.price * item.quantity for item in user_cart)
    return render_template('review_order.html', cart=user_cart, totla_price=total_price)

@app.route('/confirm_order', methods=['POST'])
@login_required
def confirm_order():
    user_cart = Cart.query.filter_by(user_id=current_user.id)
    if not user_cart:
        flash('Your cart is empty. Add products before confirming the order.', 'warning')
        return redirect(url_for('view_cart'))

    total_price = sum(item.product.price * item.quantity for item in user.cart)

    # To Create an order
    new_order = Order(user_id=current_user.id, total_price=total_price)
    db.session.add(new_order)

    # Move items from Cart to order
    for item in user_cart:
        order_product = OrderProduct(order=new_order, product=item.product, quantity=item.quantity)
        db.session.add(order_product)

    # Clear the user's cart
    Cart.query.filter_by(user_id=current_user.id).delete()

    db.session.commit()
    flash('Order confirmed successfully! You will recieve an email with order details.' 'success')
    return redirect(url_for('index'))

@app.route('/checkout', methods=['POST'])
def initiate_payment():
    # Set up the payment details using paypal SDK
    payment = Payment({
        "intent": "sale",
        "payer": {
            "payment_method": "paypal",
        },
        "redirect_urls": {
            "return_url": url_for('payment_success', _external=True),
            "cancel_url": url_for('payment_cancel', _external=True),
        },
        "transactions": [{
            "item_list": {
                "items": [{
                    "name": "Product Name",
                    "sku": str(item.product.id),
                    "price": str(item.product.price),
                    "currency": "USD",
                    "quantity": item.quantity
                } for item in user_cart]
            },
            "amount": {
                "total": str(total_price),
                "currency" : "USD"
            },
            "description": "Payment for products"
        }]
    })

    if payment.create():
        # Redirect the user to PayPAl for approval
        for link in payment.links:
            if link.method == "REDIRECT":
                redirect_url = str(link.href)
                return jsonify({'redirect_url': redirect_url})

    else:
        flash('Failed to create Paypal payment.', 'danger')

    return redirect(url_for('view_cart'))

@app.route('/payment/success')
@login_required
def payment_cancel():
    flash('Payment canceled. Your order has not been processed.')
    return redirect(url_for('view_cart'))
    





@app.route('/add_product', methods=['GET', 'POST'])
def add_product():
    form = ProductForm()

    if form.validate_on_submit():
        new_product = Product(
            name = form.name.data,
            description = form.description.data,
            price = form.price.data
        )

        db.session.add(new_product)
        db.session.commit()

        flash('Product added succesfully!', 'success')
        return redirect(url_for('home'))

    return render_template('add_product.html', form=form)

@app.route('/product/new', methods['GET', 'POST'])
@login_required
def new_product():
    form = ProductForm()
    if form.validate_on_submit():
        new_product = Product(name=form.name.data, description=form.description.data, price=form.price.data)
        db.session.add(new_product)
        db.session.commit()
        flash('Producct has been added successfully!', 'success')
        return redirect(url_for('products'))

    return render_template('new_product.html', form=form)

@app.route('/product/delete/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    flash('Product has been deleted successfully!', 'success')
    return redirect(url_for('products'))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))




if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)

