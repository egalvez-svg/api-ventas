# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed
- Incluido estado `delivered` en los filtros de órdenes activas para liberación de mesa y pago consolidado por mesa

### Added
- Endpoint `GET /branches/{branch_id}/tables/{table_id}/invoice` para obtener factura consolidada de todos los pedidos activos de una mesa
- Endpoint `POST /branches/{branch_id}/tables/{table_id}/pay` para cobrar todos los pedidos activos de una mesa en un solo pago, aplicar propina y liberar la mesa
- Método `generate_table_invoice` en `InvoiceService` para resumir ítems de múltiples órdenes por mesa
- Método `pay_table_orders` en `OrderService` para transicionar todas las órdenes activas a `paid` y descontar stock en bloque
- Schemas `TablePayRequest` y `TableInvoiceRead` en `schemas/sales.py`
- Campo `tip` (propina) en `Order` — se envía al marcar `status: paid` en `PATCH /orders/{id}/status`
- Migración Alembic `add_tip_to_order` para columna `tip` en tabla `order`
- Boleta (`GET .../invoice`) devuelve `subtotal`, `tip` y `total` (subtotal + propina)

### Added
- Estado `delivered` en el ciclo de vida de órdenes: `cooking → delivered → paid | cancelled` y `served → delivered`

### Fixed
- `order_service.update_status`: la mesa ya no se libera al pagar una orden individual si la mesa tiene otras órdenes activas

### Changed
- `stock_service.py` y `table_service.py` — type hints de `User` a `AuthContext` en métodos de acceso por sucursal

### Added
- `PATCH /users/{id}` para actualizar email, nombre, contraseña y membresías de sucursal/rol (admin o el propio usuario; solo admin puede cambiar membresías)
- `DELETE /users/{id}` soft delete de usuario via `is_active=False` (solo admin, no puede desactivarse a sí mismo)
- Schema `UserUpdate` con campos opcionales
- Endpoints de logout: `POST /auth/logout` revoca el refresh token actual, `POST /auth/logout-all` revoca todos los tokens del usuario
- CRUD completo de sucursales: `GET /branches`, `GET /branches/{id}`, `POST /branches`, `PATCH /branches/{id}`, `DELETE /branches/{id}`
- Schemas `BranchCreate` y `BranchUpdate` agregados a `schemas/branch.py`
- Delete es soft delete (desactiva `is_active`), write operations requieren rol `admin`

## [0.2.0] - 2026-04-28

### Added
- Endpoint `GET /api/v1/branches` para listar sucursales activas
- Schema `BranchRead` para respuesta de sucursales
- `InvoiceService` con generación de pre-boleta interna (`generate_pre_boleta`)
- Gestión de turnos de caja: apertura y cierre con montos inicial y final
- Migración Alembic `add_shift_cash_management` para campos de caja en turnos

### Changed
- `shift_service.py` — lógica extendida de apertura/cierre de turno con validaciones de caja
- `order_service.py` — ciclo de vida completo de órdenes con soporte de extras
- `schemas/shift.py` — campos `initial_cash`, `final_cash` y `cash_difference` agregados
- `models/base.py` — modelo Branch y User extendidos
- `models/sales.py` — relación Order → Shift agregada
- `router.py` — registrado el router de sucursales

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
