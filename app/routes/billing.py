from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, session, send_file
from flask_login import login_required, current_user
from datetime import datetime, date
from app.models import Product, Sale, SaleItem
from app import db

billing_bp = Blueprint('billing', __name__)


@billing_bp.route('/')
@login_required
def index():
    """Billing page - start a new bill"""
    products = Product.query.filter(Product.stock_qty > 0).order_by(Product.name).all()
    categories = db.session.query(Product.category).distinct().order_by(Product.category).all()
    categories = [c[0] for c in categories]
    return render_template('billing/index.html', products=products, categories=categories)


@billing_bp.route('/search')
@login_required
def search_products():
    q = request.args.get('q', '').strip()
    if not q:
        return jsonify([])
    products = Product.query.filter(
        Product.name.ilike(f'%{q}%') | (Product.barcode == q)
    ).filter(Product.stock_qty > 0).limit(15).all()
    return jsonify([{
        'id': p.product_id,
        'name': p.name,
        'price': p.unit_price,
        'stock': p.stock_qty,
        'unit': p.unit,
        'category': p.category
    } for p in products])


@billing_bp.route('/create', methods=['POST'])
@login_required
def create_sale():
    try:
        data = request.get_json()
        if not data or 'items' not in data or not data['items']:
            return jsonify({'success': False, 'error': 'No items in bill'}), 400
        
        items = data['items']
        discount = float(data.get('discount', 0) or 0)
        payment_method = data.get('payment_method', 'cash')
        notes = data.get('notes', '')
        
        if discount < 0:
            return jsonify({'success': False, 'error': 'Discount cannot be negative'}), 400
        
        # Validate all items first
        sale_items_data = []
        subtotal = 0.0
        
        for item in items:
            product_id = int(item['product_id'])
            qty = int(item['quantity'])
            
            if qty <= 0:
                return jsonify({'success': False, 'error': f'Quantity must be positive for product {product_id}'}), 400
            
            product = Product.query.get(product_id)
            if not product:
                return jsonify({'success': False, 'error': f'Product {product_id} not found'}), 404
            
            if product.stock_qty < qty:
                return jsonify({
                    'success': False,
                    'error': f'Insufficient stock for {product.name}. Available: {product.stock_qty}'
                }), 400
            
            if product.is_expired():
                return jsonify({'success': False, 'error': f'{product.name} is expired'}), 400
            
            line_total = qty * product.unit_price
            subtotal += line_total
            sale_items_data.append({
                'product': product,
                'quantity': qty,
                'price': product.unit_price
            })
        
        total = max(0.0, subtotal - discount)
        
        # Create sale
        sale = Sale(
            sale_date=date.today(),
            sale_time=datetime.now().time(),
            user_id=current_user.user_id,
            total_amount=total,
            discount=discount,
            payment_method=payment_method,
            notes=notes
        )
        db.session.add(sale)
        db.session.flush()  # get sale_id
        
        for item_data in sale_items_data:
            product = item_data['product']
            qty = item_data['quantity']
            
            sale_item = SaleItem(
                sale_id=sale.sale_id,
                product_id=product.product_id,
                quantity=qty,
                price=item_data['price']
            )
            db.session.add(sale_item)
            
            # Deduct stock
            product.stock_qty -= qty
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'sale_id': sale.sale_id,
            'total': total,
            'message': f'Bill #{sale.sale_id} created successfully. Total: ₹{total:.2f}'
        })
    
    except ValueError as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': f'Invalid data: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@billing_bp.route('/receipt/<int:sale_id>')
@login_required
def receipt(sale_id):
    sale = Sale.query.get_or_404(sale_id)
    return render_template('billing/receipt.html', sale=sale)


@billing_bp.route('/history')
@login_required
def history():
    page = request.args.get('page', 1, type=int)
    query = Sale.query.order_by(Sale.created_at.desc())
    
    # Cashiers see only their own sales unless admin
    if not current_user.is_admin():
        query = query.filter(Sale.user_id == current_user.user_id)
    
    pagination = query.paginate(page=page, per_page=20, error_out=False)
    return render_template('billing/history.html', sales=pagination.items, pagination=pagination)


@billing_bp.route('/receipt/<int:sale_id>/pdf')
@login_required
def receipt_pdf(sale_id):
    """Generate a simple PDF receipt for a sale"""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas
    from reportlab.lib.colors import HexColor
    import io as _io

    sale = Sale.query.get_or_404(sale_id)
    buffer = _io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    green = HexColor("#2d6a4f")
    y = height - 40

    c.setFillColor(green)
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width/2, y, "GreenLeaf Grocers")
    y -= 18
    c.setFillColor(HexColor("#333333"))
    c.setFont("Helvetica", 9)
    c.drawCentredString(width/2, y, "Inventory & Sales System")
    y -= 14
    c.setStrokeColor(green)
    c.line(50, y, width-50, y)
    y -= 22

    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, y, f"Bill #{sale.sale_id}")
    y -= 14
    c.setFont("Helvetica", 9)
    c.drawString(50, y, f"Date: {sale.sale_date}  {sale.sale_time.strftime('%H:%M') if sale.sale_time else ''}")
    y -= 12
    c.drawString(50, y, f"Cashier: {sale.cashier.username if sale.cashier else ''}")
    y -= 12
    c.drawString(50, y, f"Payment: {sale.payment_method or 'cash'}")
    y -= 18

    # Header
    c.setFont("Helvetica-Bold", 9)
    c.drawString(50, y, "Item")
    c.drawString(280, y, "Qty")
    c.drawString(330, y, "Price")
    c.drawString(400, y, "Total")
    y -= 4
    c.setStrokeColor(HexColor("#cccccc"))
    c.line(50, y, width-50, y)
    y -= 14

    c.setFont("Helvetica", 9)
    for item in sale.items:
        name = item.product.name if item.product else "Product"
        if len(name) > 35:
            name = name[:32] + "..."
        c.drawString(50, y, name)
        c.drawRightString(310, y, str(item.quantity))
        c.drawRightString(370, y, f"{item.price:.2f}")
        c.drawRightString(460, y, f"{item.line_total:.2f}")
        y -= 13
        if y < 80:
            c.showPage()
            y = height - 40

    y -= 6
    c.setStrokeColor(HexColor("#cccccc"))
    c.line(50, y, width-50, y)
    y -= 16

    c.setFont("Helvetica", 9)
    if sale.discount:
        c.drawString(300, y, "Discount:")
        c.drawRightString(460, y, f"-{sale.discount:.2f}")
        y -= 14

    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(green)
    c.drawString(300, y, "TOTAL:")
    c.drawRightString(460, y, f"Rs. {sale.total_amount:.2f}")
    y -= 24

    c.setFillColor(HexColor("#666666"))
    c.setFont("Helvetica", 8)
    c.drawCentredString(width/2, y, "Thank you for shopping with GreenLeaf Grocers!")
    y -= 12
    c.drawCentredString(width/2, y, "This is a computer-generated receipt.")

    c.save()
    buffer.seek(0)
    return send_file(
        buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'receipt_{sale.sale_id}.pdf'
    )
