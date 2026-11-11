from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db, login_manager


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='cashier')  # admin or cashier
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    sales = db.relationship('Sale', backref='cashier', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        return self.role == 'admin'
    
    def get_id(self):
        return str(self.user_id)
    
    def __repr__(self):
        return f'<User {self.username} ({self.role})>'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class Supplier(db.Model):
    __tablename__ = 'suppliers'
    
    supplier_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    address = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    products = db.relationship('Product', backref='supplier', lazy='dynamic')
    
    def __repr__(self):
        return f'<Supplier {self.name}>'


class Product(db.Model):
    __tablename__ = 'products'
    
    product_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False, index=True)
    category = db.Column(db.String(80), nullable=False, index=True)
    unit_price = db.Column(db.Float, nullable=False)
    stock_qty = db.Column(db.Integer, nullable=False, default=0)
    reorder_level = db.Column(db.Integer, nullable=False, default=10)
    expiry_date = db.Column(db.Date, nullable=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.supplier_id'), nullable=True)
    barcode = db.Column(db.String(50), unique=True, nullable=True)
    unit = db.Column(db.String(20), default='pcs')  # pcs, kg, litre etc.
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    sale_items = db.relationship('SaleItem', backref='product', lazy='dynamic')
    
    def is_low_stock(self):
        return self.stock_qty <= self.reorder_level
    
    def is_near_expiry(self, days=15):
        if not self.expiry_date:
            return False
        return (self.expiry_date - date.today()).days <= days and (self.expiry_date - date.today()).days >= 0
    
    def is_expired(self):
        if not self.expiry_date:
            return False
        return self.expiry_date < date.today()
    
    def __repr__(self):
        return f'<Product {self.name} (stock={self.stock_qty})>'


class Sale(db.Model):
    __tablename__ = 'sales'
    
    sale_id = db.Column(db.Integer, primary_key=True)
    sale_date = db.Column(db.Date, nullable=False, default=date.today, index=True)
    sale_time = db.Column(db.Time, nullable=False, default=lambda: datetime.now().time())
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    total_amount = db.Column(db.Float, nullable=False, default=0.0)
    discount = db.Column(db.Float, default=0.0)
    payment_method = db.Column(db.String(30), default='cash')
    notes = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    items = db.relationship('SaleItem', backref='sale', lazy='joined', cascade='all, delete-orphan')
    
    def calculate_total(self):
        subtotal = sum(item.quantity * item.price for item in self.items)
        self.total_amount = max(0, subtotal - (self.discount or 0))
        return self.total_amount
    
    def __repr__(self):
        return f'<Sale {self.sale_id} {self.sale_date} total={self.total_amount}>'


class SaleItem(db.Model):
    __tablename__ = 'sale_items'
    
    sale_item_id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('sales.sale_id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.product_id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)  # unit price at time of sale
    
    @property
    def line_total(self):
        return self.quantity * self.price
    
    def __repr__(self):
        return f'<SaleItem product={self.product_id} qty={self.quantity}>'
