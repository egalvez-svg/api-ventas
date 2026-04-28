from fastapi import APIRouter

from app.api.v1 import auth, branches, categories, ingredients, orders, products, shifts, stock, tables, users

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(branches.router)
api_router.include_router(users.router)
api_router.include_router(categories.router)
api_router.include_router(ingredients.router)
api_router.include_router(products.router)
api_router.include_router(stock.router)
api_router.include_router(tables.router)
api_router.include_router(orders.router)
api_router.include_router(shifts.router)
