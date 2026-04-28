from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel

from app.api.v1.router import api_router
from app.db.session import engine

# Import models so SQLModel.metadata is populated before create_all
import app.models.base       # noqa: F401
import app.models.inventory  # noqa: F401
import app.models.sales      # noqa: F401


@asynccontextmanager
async def lifespan(_app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield


app = FastAPI(
    title="Restaurant API Multi-sucursal",
    description="API para gestión de restaurantes con inventario por recetas y facturación electrónica (Chile)",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/", tags=["Health"])
async def root():
    return {
        "message": "Restaurant API is running",
        "status": "healthy",
        "docs": "/docs",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
