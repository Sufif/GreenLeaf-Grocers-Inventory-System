from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, send_file
from flask_login import login_required, current_user
from datetime import datetime, date
from werkzeug.utils import secure_filename
import csv
import io
from app.models import Product, Supplier
from app import db
from functools import wraps

products_bp = Blueprint('products', __name__)


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash('Admin access required.', 'danger')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated_function


@products_bp.route('/')
@login_required
def list_products():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '').strip()
    category = request.args.get('category', '').strip()
    low_stock_only = request.args.get('low_stock') == '1'
    
    query = Product.query
    
    if search:
        query = query.filter(Product.name.ilike(f'%{search}%'))
    if category:
        query = query.filter(Product.category == category)
    if low_stock_only:
        query = query.filter(Product.stock_qty <= Product.reorder_level)
    
    query = query.order_by(Product.name)
    pagination = query.paginate(page=page, per_page=current_app.config['ITEMS_PER_PAGE'], error_out=False)
    products = pagination.items
    
    categories = db.session.query(Product.category).distinct().order_by(Product.category).all()
    categories = [c[0] for c in categories]
    
    return render_template(
        'products/list.html',
        products=products,
        pagination=pagination,
        search=search,
        category=category,
        categories=categories,
        low_stock_only=low_stock_only,
        is_admin=current_user.is_admin()
    )


@products_bp.route('/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_product():
    suppliers = Supplier.query.order_by(Supplier.name).all()
    
    if request.method == 'POST':
        try:
            name = request.form.get('name', '').strip()
            category = request.form.get('category', '').strip()
            unit_price = float(request.form.get('unit_price', 0))
            stock_qty = int(request.form.get('stock_qty', 0))
            reorder_level = int(request.form.get('reorder_level', 10))
            expiry_str = request.form.get('expiry_date', '').strip()
            supplier_id = request.form.get('supplier_id') or None
            unit = request.form.get('unit', 'pcs').strip()
            barcode = request.form.get('barcode', '').strip() or None
            
            if not name or unit_price < 0 or stock_qty < 0:
                flash('Invalid product data. Name required, prices and stock cannot be negative.', 'danger')
                return redirect(url_for('products.add_product'))
            
            expiry_date = None
            if expiry_str:
                expiry_date = datetime.strptime(expiry_str, '%Y-%m-%d').date()
            
            product = Product(
                name=name,
                category=category or 'General',
                unit_price=unit_price,
                stock_qty=stock_qty,
                reorder_level=reorder_level,
                expiry_date=expiry_date,
                supplier_id=int(supplier_id) if supplier_id else None,
                unit=unit,
                barcode=barcode
            )
            db.session.add(product)
            db.session.commit()
            flash(f'Product "{name}" added successfully.', 'success')
            return redirect(url_for('products.list_products'))
        except ValueError as e:
            flash(f'Invalid input: {e}', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding product: {str(e)}', 'danger')
    
    return render_template('products/form.html', product=None, suppliers=suppliers, title='Add Product')


@products_bp.route('/edit/<int:product_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    suppliers = Supplier.query.order_by(Supplier.name).all()
    
    if request.method == 'POST':
        try:
            product.name = request.form.get('name', '').strip()
            product.category = request.form.get('category', '').strip() or 'General'
            product.unit_price = float(request.form.get('unit_price', 0))
            product.stock_qty = int(request.form.get('stock_qty', 0))
            product.reorder_level = int(request.form.get('reorder_level', 10))
            expiry_str = request.form.get('expiry_date', '').strip()
            supplier_id = request.form.get('supplier_id') or None
            product.unit = request.form.get('unit', 'pcs').strip()
            product.barcode = request.form.get('barcode', '').strip() or None
            
            if not product.name or product.unit_price < 0 or product.stock_qty < 0:
                flash('Invalid product data.', 'danger')
                return redirect(url_for('products.edit_product', product_id=product_id))
            
            if expiry_str:
                product.expiry_date = datetime.strptime(expiry_str, '%Y-%m-%d').date()
            else:
                product.expiry_date = None
            
            product.supplier_id = int(supplier_id) if supplier_id else None
            db.session.commit()
            flash(f'Product "{product.name}" updated.', 'success')
            return redirect(url_for('products.list_products'))
        except ValueError as e:
            flash(f'Invalid input: {e}', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating product: {str(e)}', 'danger')
    
    return render_template('products/form.html', product=product, suppliers=suppliers, title='Edit Product')


@products_bp.route('/delete/<int:product_id>', methods=['POST'])
@login_required
@admin_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    name = product.name
    try:
        db.session.delete(product)
        db.session.commit()
        flash(f'Product "{name}" deleted.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Cannot delete product (may have sales history): {str(e)}', 'danger')
    return redirect(url_for('products.list_products'))


@products_bp.route('/import', methods=['GET', 'POST'])
@login_required
@admin_required
def import_csv():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file selected.', 'danger')
            return redirect(url_for('products.import_csv'))
        
        file = request.files['file']
        if file.filename == '':
            flash('No file selected.', 'danger')
            return redirect(url_for('products.import_csv'))
        
        if not file.filename.lower().endswith('.csv'):
            flash('Please upload a CSV file.', 'danger')
            return redirect(url_for('products.import_csv'))
        
        try:
            stream = io.StringIO(file.stream.read().decode('utf-8'))
            reader = csv.DictReader(stream)
            count = 0
            for row in reader:
                name = row.get('name', '').strip()
                if not name:
                    continue
                product = Product(
                    name=name,
                    category=row.get('category', 'General').strip(),
                    unit_price=float(row.get('unit_price', 0)),
                    stock_qty=int(row.get('stock_qty', 0)),
                    reorder_level=int(row.get('reorder_level', 10)),
                    unit=row.get('unit', 'pcs').strip(),
                    barcode=row.get('barcode', '').strip() or None
                )
                expiry = row.get('expiry_date', '').strip()
                if expiry:
                    try:
                        product.expiry_date = datetime.strptime(expiry, '%Y-%m-%d').date()
                    except ValueError:
                        pass
                db.session.add(product)
                count += 1
            db.session.commit()
            flash(f'Successfully imported {count} products.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Import failed: {str(e)}', 'danger')
        
        return redirect(url_for('products.list_products'))
    
    return render_template('products/import.html')


@products_bp.route('/export')
@login_required
@admin_required
def export_csv():
    products = Product.query.order_by(Product.name).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['product_id', 'name', 'category', 'unit_price', 'stock_qty', 'reorder_level', 'expiry_date', 'unit', 'barcode'])
    for p in products:
        writer.writerow([
            p.product_id, p.name, p.category, p.unit_price, p.stock_qty,
            p.reorder_level, p.expiry_date.isoformat() if p.expiry_date else '',
            p.unit, p.barcode or ''
        ])
    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'products_export_{date.today().isoformat()}.csv'
    )
