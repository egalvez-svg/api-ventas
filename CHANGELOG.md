# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Catálogo por local: `Category`, `Ingredient` y `Product` ahora tienen `branch_id` — cada local gestiona su propio menú e ingredientes de forma independiente
- Endpoints de catálogo movidos a `/branches/{branch_id}/categories`, `/branches/{branch_id}/ingredients` y `/branches/{branch_id}/products`
- Validación de pertenencia al local en get, update, delete y set_recipe — un local no puede acceder al catálogo de otro
- Validación de pertenencia al local en `BranchStock.upsert` — el ingrediente debe ser del mismo local
- Migración Alembic `f3c8a2e1b7d4` — agrega `branch_id` a tablas `category`, `ingredient` y `product`; reemplaza el unique global de `category.name` por un unique compuesto `(branch_id, name)`
- Endpoint `GET /branches/{branch_id}/reports/monthly-trend` con tendencia mensual de ventas brutas, netas, propinas y pérdidas netas
- Endpoint `GET /reports/monthly-trend` (admin) con tendencia mensual consolidada y desglose por sucursal
- Schema `MonthlyTrendPoint`, `BranchMonthlyTrend` y `GlobalMonthlyTrend` en `schemas/reports.py`
- Función `get_monthly_sales_trend` en `report_service` y `get_global_monthly_trend` en `admin_report_service`

### Fixed
- Corregido error de migración inicial en despliegues automatizados (e.g. Render) cuando las tablas ya existen en la base de datos detectándolas en env.py y sellando la versión de Alembic
- Incluido estado `delivered` en los filtros de órdenes activas para liberación de mesa y pago consolidado por mesa

### Added
- Endpoints de reportes globales para admin: `GET /reports/last-shift`, `/averages`, `/trend` y `/by-weekday` — retornan total consolidado + desglose por sucursal
- Servicio `admin_report_service` con lógica de agregación multi-sucursal
- Schemas globales `GlobalLastShift`, `GlobalAverages`, `GlobalTrend`, `GlobalWeekday` y schemas de desglose `BranchLastShift`, `BranchAverages`, `BranchTrend`, `BranchWeekday` en `schemas/reports.py`
- Endpoints de reportes de ventas por sucursal: `GET /branches/{branch_id}/reports/last-shift`, `/averages`, `/trend` y `/by-weekday`
- Servicio `report_service` con lógica de agregación para última sesión, promedios y tendencia
- Schemas `LastShiftSummary`, `PeriodAverages`, `DailySalesPoint` y `WeekdaySales` en `schemas/reports.py`
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
