# Test Report — GreenLeaf Grocers Inventory System

**Date:** 10 November 2026  
**Framework:** pytest  
**Database for tests:** in-memory SQLite (`sqlite:///:memory:`)

## Summary

| Metric | Value |
|--------|-------|
| Total tests collected | 17 |
| Passed | 17 |
| Failed | 0 |
| Errors | 0 |
| Skipped | 0 |

> Earlier full run on this environment completed with **17 passed** in ~15s.  
> Re-run locally with: `pytest tests/ -v`

## Test Files

| File | Tests | Coverage |
|------|-------|----------|
| `test_auth.py` | 4 | Login page, success, failure, logout |
| `test_products.py` | 5 | List, add, admin-only guard, edit, search |
| `test_billing.py` | 5 | Billing page, create sale + stock deduction, oversell protection, negative qty, empty bill |
| `test_models.py` | 3 | Password hashing, low-stock helper, near-expiry helper |

## Key Behaviours Verified

1. **Authentication** — valid credentials redirect to dashboard; invalid show error; logout clears session.
2. **Authorization** — cashier cannot access product-add page (admin required).
3. **Stock deduction** — after a successful sale of 3 units, product stock decreases by exactly 3.
4. **Oversell protection** — requesting more units than available stock returns `success: false` and does not create a sale.
5. **Input validation** — negative quantity and empty bill are rejected.
6. **Model helpers** — `is_low_stock()`, `is_near_expiry()`, password hash/check work correctly.

## How to Re-run

```bash
cd greenleaf_grocers
pip install -r requirements.txt
pytest tests/ -v --tb=short
```

Expected final line:
```
====================== 17 passed in X.XXs ======================
```
