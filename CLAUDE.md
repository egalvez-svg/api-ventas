# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

FastAPI REST API for multi-branch restaurant management in Chile. Handles inventory via recipe-based ingredient tracking, real-time kitchen/order flow, and electronic invoicing (facturación electrónica SII). Designed to be consumed by multiple device types: waiter tablets, kitchen screens, and cashier stations.

## Running the Project

```bash
# Install dependencies
pip install -r requirements.txt

# Run development server (auto-reload enabled)
python main.py
# or directly:
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

API docs available at `http://localhost:8000/docs` (Swagger) and `/redoc`.

## Database Migrations

```bash
# Initialize Alembic (first time only)
alembic init alembic

# Create a migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head
```

## Architecture

```
app/
├── api/v1/          # Route handlers (not yet implemented)
├── core/            # Settings, security, JWT (not yet implemented)
├── db/              # Database session/engine (not yet implemented)
├── models/          # SQLModel ORM models
│   ├── base.py      # Branch, User (with roles)
│   ├── inventory.py # Category, Ingredient, Product, Recipe (join table), BranchStock
│   └── sales.py     # Table, Order, OrderItem
├── schemas/         # Pydantic request/response schemas (not yet implemented)
└── services/
    └── inventory_service.py  # Stock deduction logic
```

## Key Design Decisions

### Multi-branch (Multi-tenant)
- All data (stock, tables, orders) is scoped by `branch_id` — filter every query by it.
- **Products and catalog are global** (defined once, shared across branches).
- **Stock, prices, and tables are local** (per-branch). `BranchStock` holds inventory per branch.

### User Roles
Five roles with different access scopes:
- `admin` — Global access across all branches
- `manager` — Single branch management
- `waiter` — Takes and manages orders
- `kitchen` — Views and updates order preparation status
- `cashier` — Processes payments and invoicing

JWT tokens must encode the user's `branch_id` and `role` so the API can enforce branch isolation and permission checks without extra DB queries.

### Recipe-based Inventory
- `Ingredient` = raw material (e.g. "Queso Gauda 1kg").
- `Recipe` (join table) = links a `Product` to its `Ingredient`s with quantities.
- `Extras` on `OrderItem` also deduct stock proportionally — treat them the same as recipe ingredients.
- When an order is paid, `inventory_service.deduct_order_stock()` traces `OrderItem → Product → Recipe → Ingredient` and decrements `BranchStock` for the relevant branch.
- Stock alerts should trigger when `BranchStock.quantity` falls below a configurable `critical_threshold`.

### Order & Kitchen Flow
- **Order status**: `pending` → `cooking` → `served` → `paid` | `cancelled`
- **Table status**: `available` → `occupied` | `reserved`
- The kitchen screen polls or subscribes to orders in `cooking` status filtered by `branch_id`.

### Electronic Invoicing (Chile)
- **Default mode**: Internal pre-boleta (ticket) — system works without SII integration.
- **DTE integration**: Connect via LibreDTE or OpenFactura when the client provides a digital certificate. Design invoicing endpoints to be provider-agnostic behind a service interface so the provider can be swapped.

## Implementation Roadmap

### Phase 1 — Foundation (current)
- [ ] Configure Alembic and run first migration
- [ ] `app/core/config.py` — Settings via pydantic-settings (DATABASE_URL, SECRET_KEY, etc.)
- [ ] `app/core/security.py` — JWT creation/verification encoding `user_id`, `branch_id`, `role`
- [ ] `app/db/session.py` — SQLModel engine + `get_session` FastAPI dependency
- [ ] OAuth2 password flow + RBAC middleware for branch isolation

### Phase 2 — Menu & Inventory API
- [ ] `app/schemas/` — Request/response Pydantic models (separate from ORM models)
- [ ] CRUD routers: products, categories, ingredients, recipes
- [ ] `BranchStock` management endpoints + critical stock alerts

### Phase 3 — Orders
- [ ] Order creation and status management routers
- [ ] Extras support on `OrderItem` (also deduct stock)
- [ ] Kitchen view: orders filtered by branch in `cooking` status

### Phase 4 — Invoicing & Reporting
- [ ] Pre-boleta / internal ticket generation
- [ ] Branch cash-close logic
- [ ] SII DTE mockup (provider-agnostic interface for LibreDTE / OpenFactura)

### Phase 5 — Admin UI
- [ ] Refine or React Admin integration
- [ ] Sales and critical-stock reports

## Environment Variables

```
DATABASE_URL=postgresql://user:password@localhost:5432/api_ventas
SECRET_KEY=your-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | FastAPI + Uvicorn |
| ORM | SQLModel (SQLAlchemy + Pydantic) |
| Database | PostgreSQL via psycopg2-binary |
| Auth | python-jose (JWT) + passlib/bcrypt |
| Migrations | Alembic |
| Config | python-dotenv |
| Admin UI (planned) | Refine or React Admin |
| Invoicing (planned) | LibreDTE / OpenFactura (SII Chile) |
