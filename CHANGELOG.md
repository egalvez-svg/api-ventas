# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Shift cash management: open/close shifts with initial/final cash amounts
- Invoice service for pre-boleta (internal ticket) generation
- Order service with full order lifecycle management
- Shift service with branch-scoped cash management
- Updated order and shift schemas with extended fields

### Changed
- `app/models/base.py` — extended Branch and User models
- `app/models/sales.py` — updated Order, OrderItem with shift relation

---

## [0.1.0] - 2025-01-01

### Added
- Initial project structure with FastAPI + SQLModel
- Multi-branch architecture (`branch_id` scoping on all data)
- User model with five roles: `admin`, `manager`, `waiter`, `kitchen`, `cashier`
- JWT authentication with OAuth2 password flow
- Database models: Branch, User, Category, Ingredient, Product, Recipe, BranchStock, Table, Order, OrderItem
- Alembic migrations setup
- Recipe-based inventory deduction on order payment
- Kitchen view: orders filtered by branch in `cooking` status
- CRUD routers: products, categories, ingredients, recipes, tables
- BranchStock management with critical stock alerts
- Pre-boleta / internal ticket generation
- Branch cash-close (arqueo de caja) logic
