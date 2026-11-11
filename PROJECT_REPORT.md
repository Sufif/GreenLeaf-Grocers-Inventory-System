# Project Report: Inventory & Sales Management System for GreenLeaf Grocers

## 1. Design Overview

3-tier structure:
- **Presentation**: Jinja2 + Bootstrap 5 + Chart.js
- **Application**: Flask blueprints (auth, products, billing, reports, main)
- **Data**: SQLite via SQLAlchemy ORM (3NF)

ER diagram available at `app/static/er_diagram.png`.

## 2. Implemented Requirements Checklist

| Requirement | Status |
|-------------|--------|
| Flask application | Done |
| SQLite + 5 tables (users, products, suppliers, sales, sale_items) | Done |
| Admin / cashier login | Done |
| Product CRUD + search | Done |
| Multi-product billing | Done |
| Automatic stock deduction | Done |
| CSV import / export | Done |
| Low-stock & near-expiry alerts | Done |
| Pandas analytics | Done |
| Daily revenue analysis | Done |
| **Monthly revenue analysis** | Done |
| Top 10 products | Done |
| Category analysis | Done |
| Slow-moving products | Done |
| **Stock Turnover KPI** | Done |
| All 5 required KPIs | Done |
| PDF receipt generation | Done |
| Automated tests (17) | Done |
| ER diagram image | Done |
| Test report document | Done |

## 3. KPIs Implemented

1. **Total Revenue** — sum of sale totals in date range  
2. **Average Bill Value** — revenue ÷ bill count  
3. **Stock Turnover** — COGS (sum of line totals) ÷ current inventory value  
4. **Low-Stock Items Count** — products at or below reorder level  
5. **Top Category Share (%)** — best category revenue as % of total  

## 4. Challenges & Solutions

| Challenge | Solution |
|-----------|----------|
| Concurrent stock updates | Single DB transaction for sale + stock deduction |
| Preventing oversell | Pre-validate stock before creating Sale/SaleItem |
| Role separation | `admin_required` decorator + Flask-Login |
| Realistic analytics data | Seed script (71 products, 550 sales over ~4 months) |
| Charts | Aggregated dicts passed to Chart.js |

## 5. Testing

- 17 tests covering auth, products, billing + stock, validation, model helpers  
- Separate in-memory test database  
- Formal report: `tests/TEST_REPORT.md`  
- Last full run: **17 passed, 0 failed**

## 6. How to Run

```bash
pip install -r requirements.txt
python seed_data.py
python run.py
```

Logins: `admin` / `admin123` · `cashier1` / `cash123`

## 7. Conclusion

The application covers the full cycle requested by the project brief: database design, backend logic, validation, testing, reporting, and documentation. It is suitable as a medium-level Python portfolio project. For production use, additional security hardening and deployment configuration would be required.
