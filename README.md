# GreenLeaf Grocers — Inventory & Sales Management System

Flask + SQLite web application for product inventory, billing, stock management, and sales analytics.

**Level:** Medium | **Stack:** Python, Flask, SQLAlchemy, Flask-Login, Pandas, Chart.js, Bootstrap 5

---

## Features

- **Role-based access**: Admin (full access) vs Cashier (billing only)
- **Product management**: CRUD, search, filter, low-stock indicators, CSV import/export
- **Billing**: Multi-item cart, live search, discount, auto stock deduction, HTML + **PDF receipt**
- **Alerts**: Low stock and near-expiry (≤15 days) on dashboard
- **Reports & Analytics**:
  - Daily revenue trend (line chart)
  - **Monthly revenue** table + bar chart + CSV export
  - Top 10 products by quantity
  - Category-wise sales share
  - Slow-moving products (no sales in 30 days)
  - **KPIs**: Total Revenue, Average Bill Value, **Stock Turnover**, Low-Stock Count, Top Category Share %
- **Validation**: No overselling, no negative quantities, expired product blocking
- **Tests**: 17 unit/integration tests (pytest) — see `tests/TEST_REPORT.md`
- **ER Diagram**: `app/static/er_diagram.png`

---

## Quick Start

```bash
cd greenleaf_grocers

# Recommended: use a virtual environment
python -m venv venv
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate

pip install -r requirements.txt
python seed_data.py          # 71 products + 550 sales
python run.py
```

Open **http://127.0.0.1:5000**

### Demo Logins

| Username   | Password  | Role    |
|------------|-----------|---------|
| admin      | admin123  | Admin   |
| cashier1   | cash123   | Cashier |
| cashier2   | cash123   | Cashier |

---

## Project Structure

```
greenleaf_grocers/
├── app/
│   ├── __init__.py          # App factory
│   ├── config.py
│   ├── models.py            # User, Product, Supplier, Sale, SaleItem
│   ├── routes/
│   │   ├── auth.py
│   │   ├── main.py          # Dashboard
│   │   ├── products.py      # CRUD + CSV
│   │   ├── billing.py       # POS + stock logic + PDF receipt
│   │   └── reports.py       # Pandas analytics, monthly, KPIs
│   ├── templates/
│   └── static/
│       └── er_diagram.png   # Entity-relationship diagram
├── data/                    # SQLite DB (created by seed)
├── tests/                   # pytest suite + TEST_REPORT.md
├── seed_data.py
├── run.py
├── requirements.txt
├── README.md
└── PROJECT_REPORT.md
```

---

## Database Schema (3NF)

| Table       | Purpose |
|-------------|---------|
| users       | Admin / cashier accounts (hashed passwords) |
| suppliers   | Optional supplier master |
| products    | Inventory with stock, reorder level, expiry, barcode |
| sales       | Bill header (date, cashier, total, discount) |
| sale_items  | Line items (qty + price frozen at sale time) |

See `app/static/er_diagram.png` for the visual ER diagram.

---

## Key KPIs

| KPI | Description |
|-----|-------------|
| Total Revenue | Sum of sale totals in selected period |
| Average Bill Value | Revenue ÷ number of bills |
| Stock Turnover | COGS (line totals) ÷ current inventory value |
| Low-Stock Items Count | Products where stock ≤ reorder level |
| Top Category Share % | Highest category revenue as % of total |

---

## Running Tests

```bash
pytest tests/ -v
```

See `tests/TEST_REPORT.md` for the formal test report (17 passed).

---

## Notes

- Passwords are hashed with Werkzeug (pbkdf2).
- Stock is deducted inside the same database transaction as the sale.
- This is a **learning / portfolio project**. For real deployment you would add HTTPS, stronger secret key management, rate limiting, and a production WSGI server (e.g. Gunicorn) behind a reverse proxy.

---

## Optional Extensions

- Sales forecasting (7-day)
- Email / WhatsApp low-stock alerts
- Docker Compose deployment
- Hardware barcode scanner integration (barcode field already supported)
