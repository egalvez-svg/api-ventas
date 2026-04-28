# La lógica de descuento de stock fue migrada a StockService.
# Usar: from app.services.stock_service import stock_service
# Método: await stock_service.deduct_order_stock(session, branch_id, order_items)
