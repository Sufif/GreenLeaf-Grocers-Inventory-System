from app.models import Product, User
from datetime import date, timedelta


def test_password_hash(app):
    with app.app_context():
        u = User(username='testuser', role='cashier')
        u.set_password('secret')
        assert u.password_hash != 'secret'
        assert u.check_password('secret')
        assert not u.check_password('wrong')


def test_low_stock(app):
    with app.app_context():
        p = Product.query.filter_by(name='Test Milk').first()
        assert p.is_low_stock() is True  # stock 5 <= reorder 10


def test_near_expiry(app):
    with app.app_context():
        p = Product(name='Expiring', category='Dairy', unit_price=10, stock_qty=5, reorder_level=2,
                    expiry_date=date.today() + timedelta(days=5))
        assert p.is_near_expiry(15) is True
        assert p.is_expired() is False
