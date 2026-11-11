"""
Seed script for GreenLeaf Grocers
Generates 50+ products and 500+ sales records across several months.
Run: python seed_data.py
"""
import random
from datetime import datetime, date, timedelta, time
from faker import Faker
from app import create_app, db
from app.models import User, Supplier, Product, Sale, SaleItem

fake = Faker()
Faker.seed(42)
random.seed(42)

CATEGORIES = [
    'Fruits', 'Vegetables', 'Dairy', 'Bakery', 'Beverages',
    'Snacks', 'Grains', 'Spices', 'Personal Care', 'Household',
    'Frozen', 'Meat & Seafood', 'Organic', 'Condiments'
]

PRODUCT_TEMPLATES = [
    # Fruits
    ('Apple', 'Fruits', 80, 150, 20, 'kg'),
    ('Banana', 'Fruits', 40, 200, 30, 'kg'),
    ('Orange', 'Fruits', 60, 120, 25, 'kg'),
    ('Mango', 'Fruits', 120, 80, 15, 'kg'),
    ('Grapes', 'Fruits', 90, 60, 10, 'kg'),
    ('Papaya', 'Fruits', 50, 40, 8, 'pcs'),
    ('Watermelon', 'Fruits', 40, 30, 5, 'pcs'),
    ('Pomegranate', 'Fruits', 150, 50, 10, 'kg'),
    # Vegetables
    ('Tomato', 'Vegetables', 30, 180, 40, 'kg'),
    ('Potato', 'Vegetables', 25, 250, 50, 'kg'),
    ('Onion', 'Vegetables', 35, 200, 40, 'kg'),
    ('Carrot', 'Vegetables', 45, 90, 20, 'kg'),
    ('Cabbage', 'Vegetables', 30, 70, 15, 'pcs'),
    ('Cauliflower', 'Vegetables', 40, 60, 12, 'pcs'),
    ('Spinach', 'Vegetables', 20, 50, 10, 'bunch'),
    ('Cucumber', 'Vegetables', 25, 80, 15, 'kg'),
    ('Capsicum', 'Vegetables', 60, 45, 10, 'kg'),
    ('Brinjal', 'Vegetables', 35, 55, 12, 'kg'),
    # Dairy
    ('Milk 1L', 'Dairy', 60, 100, 30, 'pcs'),
    ('Curd 500g', 'Dairy', 35, 80, 20, 'pcs'),
    ('Butter 100g', 'Dairy', 55, 60, 15, 'pcs'),
    ('Cheese Slice', 'Dairy', 120, 40, 10, 'pcs'),
    ('Paneer 200g', 'Dairy', 90, 50, 12, 'pcs'),
    ('Ghee 500ml', 'Dairy', 350, 30, 8, 'pcs'),
    # Bakery
    ('Bread', 'Bakery', 40, 70, 20, 'pcs'),
    ('Bun Pack', 'Bakery', 30, 50, 15, 'pcs'),
    ('Cookies', 'Bakery', 50, 80, 20, 'pcs'),
    ('Cake Slice', 'Bakery', 80, 25, 8, 'pcs'),
    # Beverages
    ('Mineral Water 1L', 'Beverages', 20, 150, 40, 'pcs'),
    ('Cola 750ml', 'Beverages', 40, 100, 25, 'pcs'),
    ('Orange Juice', 'Beverages', 70, 60, 15, 'pcs'),
    ('Green Tea', 'Beverages', 120, 40, 10, 'pcs'),
    ('Coffee Powder', 'Beverages', 250, 35, 8, 'pcs'),
    # Snacks
    ('Potato Chips', 'Snacks', 20, 120, 30, 'pcs'),
    ('Namkeen Mix', 'Snacks', 40, 90, 25, 'pcs'),
    ('Biscuits Pack', 'Snacks', 30, 100, 25, 'pcs'),
    ('Chocolate Bar', 'Snacks', 50, 80, 20, 'pcs'),
    # Grains
    ('Rice 5kg', 'Grains', 350, 40, 10, 'pcs'),
    ('Wheat Flour 5kg', 'Grains', 220, 50, 12, 'pcs'),
    ('Toor Dal 1kg', 'Grains', 140, 60, 15, 'pcs'),
    ('Moong Dal 1kg', 'Grains', 130, 55, 12, 'pcs'),
    # Spices
    ('Turmeric Powder', 'Spices', 80, 70, 15, 'pcs'),
    ('Chilli Powder', 'Spices', 90, 65, 15, 'pcs'),
    ('Cumin Seeds', 'Spices', 120, 40, 10, 'pcs'),
    ('Garam Masala', 'Spices', 100, 50, 12, 'pcs'),
    # Personal Care
    ('Toothpaste', 'Personal Care', 80, 60, 15, 'pcs'),
    ('Soap Bar', 'Personal Care', 30, 100, 25, 'pcs'),
    ('Shampoo 200ml', 'Personal Care', 150, 40, 10, 'pcs'),
    # Household
    ('Dish Wash', 'Household', 90, 50, 12, 'pcs'),
    ('Floor Cleaner', 'Household', 120, 35, 8, 'pcs'),
    ('Tissue Pack', 'Household', 50, 70, 15, 'pcs'),
    # Extra to reach 50+
    ('Eggs (12)', 'Dairy', 70, 80, 20, 'pcs'),
    ('Yogurt Drink', 'Dairy', 25, 90, 25, 'pcs'),
    ('Honey 250g', 'Condiments', 180, 30, 8, 'pcs'),
    ('Pickle Jar', 'Condiments', 110, 40, 10, 'pcs'),
    ('Soy Sauce', 'Condiments', 95, 35, 8, 'pcs'),
    ('Olive Oil 500ml', 'Condiments', 450, 25, 6, 'pcs'),
    ('Frozen Peas', 'Frozen', 80, 40, 10, 'pcs'),
    ('Ice Cream Tub', 'Frozen', 200, 30, 8, 'pcs'),
    ('Chicken (1kg)', 'Meat & Seafood', 220, 25, 6, 'kg'),
    ('Fish Fillet', 'Meat & Seafood', 350, 20, 5, 'kg'),
]


def create_users():
    users = [
        ('admin', 'admin123', 'admin'),
        ('cashier1', 'cash123', 'cashier'),
        ('cashier2', 'cash123', 'cashier'),
        ('manager', 'mgr123', 'admin'),
    ]
    created = []
    for username, password, role in users:
        if not User.query.filter_by(username=username).first():
            u = User(username=username, role=role)
            u.set_password(password)
            db.session.add(u)
            created.append(username)
    db.session.commit()
    print(f'Users created: {created}')
    return User.query.all()


def create_suppliers():
    names = [
        'FreshFarm Supplies', 'Green Valley Traders', 'Daily Dairy Co.',
        'Spice Route India', 'Organic Harvest', 'City Wholesale Mart',
        'Coastal Seafoods', 'Bakery Delights Ltd'
    ]
    for name in names:
        if not Supplier.query.filter_by(name=name).first():
            s = Supplier(
                name=name,
                phone=fake.phone_number()[:15],
                email=fake.company_email(),
                address=fake.address()[:200]
            )
            db.session.add(s)
    db.session.commit()
    print(f'Suppliers: {Supplier.query.count()}')
    return Supplier.query.all()


def create_products(suppliers):
    products = []
    for i, (name, cat, price, stock, reorder, unit) in enumerate(PRODUCT_TEMPLATES):
        # Vary price and stock a bit
        unit_price = round(price * random.uniform(0.9, 1.15), 2)
        stock_qty = int(stock * random.uniform(0.7, 1.3))
        
        # Some products near expiry or low stock
        expiry = None
        if cat in ['Dairy', 'Bakery', 'Meat & Seafood', 'Fruits', 'Vegetables', 'Frozen']:
            days = random.randint(-5, 60)  # some expired or near
            expiry = date.today() + timedelta(days=days)
        
        # Force some low stock
        if i % 7 == 0:
            stock_qty = random.randint(0, reorder)
        
        p = Product(
            name=name,
            category=cat,
            unit_price=unit_price,
            stock_qty=max(0, stock_qty),
            reorder_level=reorder,
            expiry_date=expiry,
            supplier_id=random.choice(suppliers).supplier_id if suppliers else None,
            unit=unit,
            barcode=f'890{1000000000 + i}'
        )
        db.session.add(p)
        products.append(p)
    
    # Add a few more random products
    for _ in range(10):
        cat = random.choice(CATEGORIES)
        name = f'{fake.word().title()} {cat.split()[0]}'
        p = Product(
            name=name,
            category=cat,
            unit_price=round(random.uniform(20, 400), 2),
            stock_qty=random.randint(5, 150),
            reorder_level=random.randint(5, 25),
            expiry_date=date.today() + timedelta(days=random.randint(10, 180)) if random.random() > 0.3 else None,
            supplier_id=random.choice(suppliers).supplier_id if suppliers else None,
            unit=random.choice(['pcs', 'kg', 'litre', 'pack']),
            barcode=f'890{random.randint(1000000000, 9999999999)}'
        )
        db.session.add(p)
        products.append(p)
    
    db.session.commit()
    print(f'Products created: {Product.query.count()}')
    return Product.query.all()


def create_sales(users, products, num_sales=550):
    cashiers = [u for u in users if u.role == 'cashier'] or users
    start_date = date.today() - timedelta(days=120)  # ~4 months
    
    created = 0
    for i in range(num_sales):
        # Random date in range, more recent sales denser
        days_ago = int(random.triangular(0, 120, 20))
        sale_date = date.today() - timedelta(days=days_ago)
        sale_time = time(random.randint(8, 20), random.randint(0, 59))
        
        # 1-6 items per bill
        n_items = random.randint(1, 6)
        chosen = random.sample(products, min(n_items, len(products)))
        
        sale = Sale(
            sale_date=sale_date,
            sale_time=sale_time,
            user_id=random.choice(cashiers).user_id,
            discount=round(random.choice([0, 0, 0, 5, 10, 15, 20]), 2),
            payment_method=random.choice(['cash', 'cash', 'upi', 'card']),
            notes=''
        )
        db.session.add(sale)
        db.session.flush()
        
        subtotal = 0.0
        for prod in chosen:
            # Don't oversell current stock in seed (we ignore real stock for historical)
            qty = random.randint(1, 4)
            # Use a slightly varied historical price
            price = round(prod.unit_price * random.uniform(0.95, 1.05), 2)
            item = SaleItem(
                sale_id=sale.sale_id,
                product_id=prod.product_id,
                quantity=qty,
                price=price
            )
            db.session.add(item)
            subtotal += qty * price
        
        sale.total_amount = max(0, subtotal - sale.discount)
        created += 1
        
        if created % 100 == 0:
            db.session.commit()
            print(f'  ... {created} sales')
    
    db.session.commit()
    print(f'Sales created: {Sale.query.count()}')
    print(f'Sale items: {SaleItem.query.count()}')


def main():
    app = create_app()
    with app.app_context():
        print('Dropping and recreating tables...')
        db.drop_all()
        db.create_all()
        
        print('Seeding users...')
        users = create_users()
        
        print('Seeding suppliers...')
        suppliers = create_suppliers()
        
        print('Seeding products...')
        products = create_products(suppliers)
        
        print('Seeding sales (this may take a moment)...')
        create_sales(users, products, num_sales=550)
        
        print('\n=== Seed complete ===')
        print(f'Users: {User.query.count()}')
        print(f'Suppliers: {Supplier.query.count()}')
        print(f'Products: {Product.query.count()}')
        print(f'Sales: {Sale.query.count()}')
        print(f'Sale Items: {SaleItem.query.count()}')
        print('\nLogin credentials:')
        print('  admin / admin123  (admin)')
        print('  cashier1 / cash123  (cashier)')
        print('  cashier2 / cash123  (cashier)')


if __name__ == '__main__':
    main()
