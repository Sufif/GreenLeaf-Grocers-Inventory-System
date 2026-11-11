import json
from app.models import Product, Sale, SaleItem
from app import db


def test_billing_page(cashier_client):
    r = cashier_client.get('/billing/')
    assert r.status_code == 200
    assert b'New Bill' in r.data or b'Billing' in r.data


def test_create_sale_and_stock_deduction(cashier_client, app):
    with app.app_context():
        p = Product.query.filter_by(name='Test Apple').first()
        old_stock = p.stock_qty
        pid = p.product_id
    
    payload = {
        'items': [{'product_id': pid, 'quantity': 3}],
        'discount': 5,
        'payment_method': 'cash',
        'notes': 'test bill'
    }
    r = cashier_client.post('/billing/create', data=json.dumps(payload), content_type='application/json')
    assert r.status_code == 200
    data = r.get_json()
    assert data['success'] is True
    assert 'sale_id' in data
    
    with app.app_context():
        p = Product.query.get(pid)
        assert p.stock_qty == old_stock - 3
        sale = Sale.query.get(data['sale_id'])
        assert sale is not None
        assert sale.total_amount == 50 * 3 - 5  # 145
        assert len(sale.items) == 1


def test_cannot_oversell(cashier_client, app):
    with app.app_context():
        p = Product.query.filter_by(name='Test Milk').first()  # stock 5
        pid = p.product_id
    
    payload = {
        'items': [{'product_id': pid, 'quantity': 10}],
        'discount': 0,
        'payment_method': 'cash'
    }
    r = cashier_client.post('/billing/create', data=json.dumps(payload), content_type='application/json')
    data = r.get_json()
    assert data['success'] is False
    assert 'stock' in data['error'].lower() or 'Insufficient' in data['error']


def test_reject_negative_qty(cashier_client, app):
    with app.app_context():
        p = Product.query.filter_by(name='Test Apple').first()
        pid = p.product_id
    payload = {
        'items': [{'product_id': pid, 'quantity': -1}],
        'discount': 0
    }
    r = cashier_client.post('/billing/create', data=json.dumps(payload), content_type='application/json')
    data = r.get_json()
    assert data['success'] is False


def test_empty_bill(cashier_client):
    r = cashier_client.post('/billing/create', data=json.dumps({'items': []}), content_type='application/json')
    data = r.get_json()
    assert data['success'] is False
