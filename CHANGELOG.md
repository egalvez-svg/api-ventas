# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Endpoint `GET /branches/{branch_id}/reports/payment-methods` con distribución de ventas por método de pago (efectivo, tarjeta, transferencia), incluyendo total, cantidad de transacciones y porcentaje sobre el período
- Endpoint admin `GET /reports/payment-methods` con la misma distribución consolidada globalmente y desglosada por sucursal
- Modelo `Payment` para registrar métodos de pago (efectivo, tarjeta, transferencia) asociados a una orden
- Endpoint `POST /branches/{branch_id}/orders/{order_id}/payments` para pagar una orden con uno o más métodos de pago
- Validación de montos: el total de los pagos debe cubrir el valor de la orden más propina
- Soporte de pagos mixtos en el pago de mesa (`POST /tables/{table_id}/pay`) vía campo `payments`
- Campo `payments` en `OrderRead` con el detalle de los pagos realizados
- Campo `payments` en la pre-boleta (`GET /orders/{order_id}/invoice`) con el detalle de los métodos de pago
- Migración Alembic `31ba31a40681` — crea la tabla `payment`
- Campo `waiter_name` en `OrderRead` con el nombre completo del mesero que tomó la orden, visible en vistas de mesa y cocina
- Campos `category_id` y `category_name` en `ProductRankingPoint` del endpoint de top-products
- Campo `frequently_bought_with` en `ProductRankingPoint` con los productos más comprados junto a cada producto del top (análisis de co-compra); configurable vía parámetro `co_limit` en el endpoint
- Datos completos del cupón (`code`, `description`, `discount_type`, `discount_value`) en facturas de orden y de mesa, reemplazando el campo `coupon_id` crudo
- Campo `product_name` en `OrderItemRead` para evitar lookups adicionales desde el cliente
- Endpoint `GET /branches/{branch_id}/reports/top-products` con ranking de productos más vendidos por cantidad, filtrable por días y límite de resultados
- Endpoint `GET /branches/{branch_id}/shifts` para listar el historial de turnos paginado (manager/admin)
- Endpoint `GET /branches/{branch_id}/shifts/current/orders` para ver las órdenes del turno activo (cajero/manager/admin)
- Endpoint `GET /branches/{branch_id}/shifts/{shift_id}/orders` para ver las órdenes de un turno específico (manager/admin)
- Dependencia `CashierDep` para restringir endpoints al rol cajero y superiores
- Campo `coupon_code` en `OrderStatusUpdate` para aplicar un cupón al momento del pago (no solo en la creación de la orden)
- Modelo `Coupon` con soporte de descuento por porcentaje y monto fijo, límite de usos, fecha de vencimiento y alcance por sucursal o global
- Endpoints CRUD de cupones en `/branches/{branch_id}/coupons` (requiere rol `manager` o superior)
- Endpoint `GET /branches/{branch_id}/coupons/validate` para validar un cupón antes de aplicarlo a una orden
- Campo `coupon_code` en `OrderCreate` para aplicar un cupón al crear una orden
- Campos `discount` y `coupon_id` en `Order` y `OrderRead` para registrar el descuento aplicado
- Incremento automático de `used_count` al pagar una orden con cupón asociado
- Soporte de `discount` en `TableInvoiceRead` y en el servicio de facturación (`invoice_service`)
- Migración Alembic `aa679333cc5e` — agrega tablas `coupon` y columnas `coupon_id`, `discount` en `order`

### Changed
- Permisos de gestión de usuarios extendidos al rol `manager`: puede listar, crear, ver, editar y desactivar usuarios de su propia sucursal
- Manager no puede asignar el rol `admin` ni gestionar membresías de otras sucursales (prevención de escalación de privilegios)

### Fixed
- Reemplazado `passlib` por `bcrypt` directo para resolver incompatibilidad con `bcrypt >= 4.0.0` en Python 3.14 (ValueError al verificar contraseñas)

### Changed
- Endpoint `PATCH /branches/{branch_id}/stock/{ingredient_name}` ahora recibe el nombre del ingrediente en lugar del ID
- Refactorizada la lógica de pre-vuelo en `alembic/env.py` para usar conexiones separadas al sellar y migrar

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
