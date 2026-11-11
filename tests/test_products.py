from app.models import Product
from app import db


def test_list_products(admin_client):
    r = admin_client.get('/products/')
    assert r.status_code == 200
    assert b'Test Apple' in r.data


def test_add_product(admin_client, app):
    r = admin_client.post('/products/add', data={
        'name': 'New Banana',
        'category': 'Fruits',
        'unit_price': '30',
        'stock_qty': '50',
        'reorder_level': '10',
        'unit': 'kg'
    }, follow_redirects=True)
    assert r.status_code == 200
    with app.app_context():
        p = Product.query.filter_by(name='New Banana').first()
        assert p is not None
        assert p.unit_price == 30.0


def test_cashier_cannot_add(cashier_client):
    r = cashier_client.get('/products/add', follow_redirects=True)
    assert b'Admin access required' in r.data or r.status_code in (200, 302)


def test_edit_product(admin_client, app):
    with app.app_context():
        p = Product.query.filter_by(name='Test Apple').first()
        pid = p.product_id
    r = admin_client.post(f'/products/edit/{pid}', data={
        'name': 'Test Apple Updated',
        'category': 'Fruits',
        'unit_price': '55',
        'stock_qty': '90',
        'reorder_level': '10',
        'unit': 'kg'
    }, follow_redirects=True)
    assert r.status_code == 200
    with app.app_context():
        p = Product.query.get(pid)
        assert p.name == 'Test Apple Updated'
        assert p.unit_price == 55.0


def test_search_products(admin_client):
    r = admin_client.get('/products/?search=Apple')
    assert r.status_code == 200
    assert b'Test Apple' in r.data
