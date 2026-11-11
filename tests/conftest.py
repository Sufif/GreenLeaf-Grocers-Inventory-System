import pytest
from app import create_app, db
from app.models import User, Product, Supplier
from app.config import Config


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    SECRET_KEY = 'test-secret'


@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        # seed minimal
        admin = User(username='admin', role='admin')
        admin.set_password('admin123')
        cashier = User(username='cashier', role='cashier')
        cashier.set_password('cash123')
        db.session.add_all([admin, cashier])
        
        supplier = Supplier(name='Test Supplier', phone='123')
        db.session.add(supplier)
        db.session.flush()
        
        p1 = Product(name='Test Apple', category='Fruits', unit_price=50.0, stock_qty=100, reorder_level=10, supplier_id=supplier.supplier_id)
        p2 = Product(name='Test Milk', category='Dairy', unit_price=60.0, stock_qty=5, reorder_level=10)
        db.session.add_all([p1, p2])
        db.session.commit()
        
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def admin_client(client):
    client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)
    return client


@pytest.fixture
def cashier_client(client):
    client.post('/login', data={'username': 'cashier', 'password': 'cash123'}, follow_redirects=True)
    return client
