from flask import Blueprint, render_template, request, send_file, jsonify, current_app
from flask_login import login_required, current_user
from datetime import datetime, date, timedelta
from functools import wraps
import pandas as pd
import io

from app.models import Product, Sale, SaleItem, User
from app import db
from sqlalchemy import func

reports_bp = Blueprint('reports', __name__)


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            from flask import flash, redirect, url_for
            flash('Admin access required for reports.', 'danger')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated_function


def get_sales_df(start_date=None, end_date=None):
    """Build a pandas DataFrame of sales + items"""
    query = db.session.query(
        Sale.sale_id,
        Sale.sale_date,
        Sale.sale_time,
        Sale.total_amount,
        Sale.discount,
        Sale.user_id,
        User.username,
        SaleItem.product_id,
        Product.name.label('product_name'),
        Product.category,
        SaleItem.quantity,
        SaleItem.price,
        (SaleItem.quantity * SaleItem.price).label('line_total')
    ).join(SaleItem, Sale.sale_id == SaleItem.sale_id)\
     .join(Product, SaleItem.product_id == Product.product_id)\
     .join(User, Sale.user_id == User.user_id)

    if start_date:
        query = query.filter(Sale.sale_date >= start_date)
    if end_date:
        query = query.filter(Sale.sale_date <= end_date)

    rows = query.all()
    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame([{
        'sale_id': r.sale_id,
        'sale_date': r.sale_date,
        'sale_time': r.sale_time,
        'total_amount': r.total_amount,
        'discount': r.discount,
        'user_id': r.user_id,
        'username': r.username,
        'product_id': r.product_id,
        'product_name': r.product_name,
        'category': r.category,
        'quantity': r.quantity,
        'price': r.price,
        'line_total': r.line_total
    } for r in rows])
    return df


def compute_stock_turnover(start_date, end_date):
    """
    Stock Turnover = Cost of Goods Sold (approx by revenue of units sold)
                     / Average Inventory Value
    We approximate COGS as sum(qty * unit_price at sale) and
    average inventory as mean of current stock value (simplified for SQLite demo).
    Higher = inventory sells faster.
    """
    df = get_sales_df(start_date, end_date)
    if df.empty:
        return 0.0

    cogs = float(df['line_total'].sum())

    # Current inventory value as proxy for average inventory
    products = Product.query.all()
    inv_value = sum(p.stock_qty * p.unit_price for p in products)
    if inv_value <= 0:
        return 0.0
    return round(cogs / inv_value, 2)


@reports_bp.route('/')
@login_required
@admin_required
def index():
    today = date.today()
    start = request.args.get('start', (today - timedelta(days=30)).isoformat())
    end = request.args.get('end', today.isoformat())

    try:
        start_date = datetime.strptime(start, '%Y-%m-%d').date()
        end_date = datetime.strptime(end, '%Y-%m-%d').date()
    except ValueError:
        start_date = today - timedelta(days=30)
        end_date = today

    df = get_sales_df(start_date, end_date)

    # ----- KPIs -----
    total_revenue = 0.0
    avg_bill = 0.0
    bill_count = 0
    top_category = 'N/A'
    top_category_share = 0.0
    low_stock_count = Product.query.filter(
        Product.stock_qty <= Product.reorder_level
    ).count()
    stock_turnover = compute_stock_turnover(start_date, end_date)

    daily_revenue = {}
    monthly_revenue = {}
    top_products = []
    category_share = {}

    if not df.empty:
        sales_summary = df.groupby('sale_id').agg({
            'total_amount': 'first',
            'sale_date': 'first'
        }).reset_index()
        total_revenue = float(sales_summary['total_amount'].sum())
        bill_count = len(sales_summary)
        avg_bill = total_revenue / bill_count if bill_count else 0.0

        # Category share
        cat_sales = df.groupby('category')['line_total'].sum().sort_values(ascending=False)
        if len(cat_sales) > 0:
            top_category = str(cat_sales.index[0])
            top_category_share = float(cat_sales.iloc[0] / cat_sales.sum() * 100) if cat_sales.sum() else 0.0
            category_share = {str(k): float(v) for k, v in cat_sales.items()}

        # Daily revenue
        daily = df.groupby('sale_date')['line_total'].sum().sort_index()
        daily_revenue = {str(k): float(v) for k, v in daily.items()}

        # Monthly revenue (YYYY-MM)
        df2 = df.copy()
        df2['month'] = pd.to_datetime(df2['sale_date']).dt.to_period('M').astype(str)
        monthly = df2.groupby('month')['line_total'].sum().sort_index()
        monthly_revenue = {str(k): float(v) for k, v in monthly.items()}

        # Top 10 products by quantity
        top = df.groupby('product_name')['quantity'].sum().sort_values(ascending=False).head(10)
        top_products = [{'name': str(k), 'qty': int(v)} for k, v in top.items()]

    # Slow moving (no sales in last 30 days)
    thirty_days_ago = today - timedelta(days=30)
    sold_ids = db.session.query(SaleItem.product_id).join(Sale).filter(
        Sale.sale_date >= thirty_days_ago
    ).distinct().all()
    sold_ids = {s[0] for s in sold_ids}
    all_products = Product.query.all()
    slow_moving = [p for p in all_products if p.product_id not in sold_ids][:15]

    low_stock_items = Product.query.filter(
        Product.stock_qty <= Product.reorder_level
    ).order_by(Product.stock_qty).all()

    near_expiry = Product.query.filter(
        Product.expiry_date != None,
        Product.expiry_date <= today + timedelta(days=15),
        Product.expiry_date >= today
    ).order_by(Product.expiry_date).all()

    return render_template(
        'reports/index.html',
        start=start_date.isoformat(),
        end=end_date.isoformat(),
        total_revenue=total_revenue,
        avg_bill=avg_bill,
        bill_count=bill_count,
        top_category=top_category,
        top_category_share=top_category_share,
        low_stock_count=low_stock_count,
        stock_turnover=stock_turnover,
        daily_revenue=daily_revenue,
        monthly_revenue=monthly_revenue,
        top_products=top_products,
        category_share=category_share,
        slow_moving=slow_moving,
        low_stock_items=low_stock_items,
        near_expiry=near_expiry
    )


@reports_bp.route('/daily')
@login_required
@admin_required
def daily_report():
    report_date = request.args.get('date', date.today().isoformat())
    try:
        d = datetime.strptime(report_date, '%Y-%m-%d').date()
    except ValueError:
        d = date.today()

    sales = Sale.query.filter(Sale.sale_date == d).order_by(Sale.sale_time).all()
    total = sum(s.total_amount for s in sales)

    return render_template('reports/daily.html', sales=sales, report_date=d, total=total)


@reports_bp.route('/monthly')
@login_required
@admin_required
def monthly_report():
    """Dedicated monthly revenue view"""
    today = date.today()
    # Default: last 6 months
    start = request.args.get('start', (today - timedelta(days=180)).isoformat())
    end = request.args.get('end', today.isoformat())
    try:
        start_date = datetime.strptime(start, '%Y-%m-%d').date()
        end_date = datetime.strptime(end, '%Y-%m-%d').date()
    except ValueError:
        start_date = today - timedelta(days=180)
        end_date = today

    df = get_sales_df(start_date, end_date)
    monthly_rows = []
    if not df.empty:
        df2 = df.copy()
        df2['month'] = pd.to_datetime(df2['sale_date']).dt.to_period('M').astype(str)
        grouped = df2.groupby('month').agg(
            revenue=('line_total', 'sum'),
            qty=('quantity', 'sum'),
            bills=('sale_id', 'nunique')
        ).sort_index()
        for month, row in grouped.iterrows():
            monthly_rows.append({
                'month': month,
                'revenue': float(row['revenue']),
                'qty': int(row['qty']),
                'bills': int(row['bills']),
                'avg_bill': float(row['revenue'] / row['bills']) if row['bills'] else 0
            })

    return render_template(
        'reports/monthly.html',
        monthly_rows=monthly_rows,
        start=start_date.isoformat(),
        end=end_date.isoformat()
    )


@reports_bp.route('/export/<report_type>')
@login_required
@admin_required
def export_report(report_type):
    today = date.today()
    start = request.args.get('start', (today - timedelta(days=30)).isoformat())
    end = request.args.get('end', today.isoformat())

    try:
        start_date = datetime.strptime(start, '%Y-%m-%d').date()
        end_date = datetime.strptime(end, '%Y-%m-%d').date()
    except ValueError:
        start_date = today - timedelta(days=30)
        end_date = today

    output = io.StringIO()

    if report_type == 'sales':
        df = get_sales_df(start_date, end_date)
        if df.empty:
            df = pd.DataFrame(columns=['sale_id', 'sale_date', 'product_name', 'quantity', 'line_total'])
        df.to_csv(output, index=False)
        filename = f'sales_report_{start}_{end}.csv'

    elif report_type == 'monthly':
        df = get_sales_df(start_date, end_date)
        if df.empty:
            pd.DataFrame(columns=['month', 'revenue', 'qty', 'bills']).to_csv(output, index=False)
        else:
            df2 = df.copy()
            df2['month'] = pd.to_datetime(df2['sale_date']).dt.to_period('M').astype(str)
            grouped = df2.groupby('month').agg(
                revenue=('line_total', 'sum'),
                qty=('quantity', 'sum'),
                bills=('sale_id', 'nunique')
            ).reset_index()
            grouped.to_csv(output, index=False)
        filename = f'monthly_revenue_{start}_{end}.csv'

    elif report_type == 'low_stock':
        products = Product.query.filter(Product.stock_qty <= Product.reorder_level).all()
        writer = pd.DataFrame([{
            'product_id': p.product_id,
            'name': p.name,
            'category': p.category,
            'stock_qty': p.stock_qty,
            'reorder_level': p.reorder_level,
            'unit_price': p.unit_price
        } for p in products])
        writer.to_csv(output, index=False)
        filename = f'low_stock_report_{today.isoformat()}.csv'

    elif report_type == 'expiry':
        products = Product.query.filter(
            Product.expiry_date != None,
            Product.expiry_date <= today + timedelta(days=15)
        ).order_by(Product.expiry_date).all()
        writer = pd.DataFrame([{
            'product_id': p.product_id,
            'name': p.name,
            'expiry_date': p.expiry_date.isoformat() if p.expiry_date else '',
            'stock_qty': p.stock_qty,
            'days_left': (p.expiry_date - today).days if p.expiry_date else ''
        } for p in products])
        writer.to_csv(output, index=False)
        filename = f'expiry_report_{today.isoformat()}.csv'

    else:
        return 'Invalid report type', 400

    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=filename
    )
