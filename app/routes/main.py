from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from datetime import date, timedelta
from app.models import Product, Sale, SaleItem
from app import db
from sqlalchemy import func

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('auth.login'))


@main_bp.route('/dashboard')
@login_required
def dashboard():
    today = date.today()
    
    # Today's sales
    today_sales = Sale.query.filter(Sale.sale_date == today).all()
    today_revenue = sum(s.total_amount for s in today_sales)
    today_bills = len(today_sales)
    
    # Low stock count
    low_stock = Product.query.filter(Product.stock_qty <= Product.reorder_level).count()
    
    # Near expiry (within 15 days)
    near_expiry = Product.query.filter(
        Product.expiry_date != None,
        Product.expiry_date <= today + timedelta(days=15),
        Product.expiry_date >= today
    ).count()
    
    # Total products
    total_products = Product.query.count()
    
    # Recent sales (last 5)
    recent_sales = Sale.query.order_by(Sale.created_at.desc()).limit(5).all()
    
    # Alerts list
    low_stock_items = Product.query.filter(Product.stock_qty <= Product.reorder_level).limit(10).all()
    near_expiry_items = Product.query.filter(
        Product.expiry_date != None,
        Product.expiry_date <= today + timedelta(days=15),
        Product.expiry_date >= today
    ).order_by(Product.expiry_date).limit(10).all()
    
    return render_template(
        'dashboard.html',
        today_revenue=today_revenue,
        today_bills=today_bills,
        low_stock=low_stock,
        near_expiry=near_expiry,
        total_products=total_products,
        recent_sales=recent_sales,
        low_stock_items=low_stock_items,
        near_expiry_items=near_expiry_items,
        is_admin=current_user.is_admin()
    )
