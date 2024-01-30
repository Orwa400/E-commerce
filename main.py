from flask import Flask, render_template, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, FloatField, IntegerField
from wtforms.validators import DataRequired
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_migrate import Migrate


app = Flask(__name__)
app.config['SECRET_KEY'] = '07574674420722653976'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager =LoginManager(app)
login_manager.login_view = 'login'

# Database Models
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(dbString(120), unique=True, nullable=False)
    password = db.column(db.string(60), nullable=False)
    orders = db.relationship('Order', backref='user', lazy=True)


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, nullable=False)
    orders = db.relationship('OrderItem', backref='product', lazy=True)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.COlumn(db.Integer, db.ForeignKey('user.id', nullable=False))
    items = dbrelationship('OrderItem', backref='order', lazy=True)


class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.COlumn(db.Integer, db.FOreignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

    

class ProductForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    description = TextAreaField('Description')
    price = FloatField('Price', validators=[DataRequired()])
    submit = SubmitField('Add Product')

# Forms
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    submit = SubmitField('Login')

class ProductForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    description = TextAreaField('Description')
    price = FloatField('Price', validators=[DataRequired()])
    submit = SubmitField('Add Product')

class OrderForm(FlaskForm):
    product_id = IntegerField('Product ID', validators=[DataRequired()])
    quantity = IntegerField('Quantity', validators=[DataRequired()])
    submit = SubmitField('ADD to Cart')


# Routes
@app.route('/')
def home():
    return render_template('index.html')


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

    cart_items = OrderItem.query.all()
    return render_template('cart.html', cart_items, form=form)
    

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

@app.route('/designer')
@login_required
def designer():
    return render_template('designer.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            login_user(user)
            flash('Login successful!', 'succcess')
            return redirect(url_for("designer"))
        else:
            flash('Login unsuccessful. Please check your username.', 'danger')

    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)

