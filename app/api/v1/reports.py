from fastapi import APIRouter, Query

from app.core.deps import ManagerDep, SessionDep
from app.schemas.reports import DailySalesPoint, LastShiftSummary, MonthlyTrendPoint, PeriodAverages, ProductRankingPoint, WeekdaySales
from app.services.report_service import (
    get_last_shift_summary,
    get_monthly_sales_trend,
    get_period_averages,
    get_sales_by_weekday,
    get_sales_trend,
    get_top_products,
)

router = APIRouter(prefix="/branches/{branch_id}/reports", tags=["Reports"])


@router.get("/last-shift", response_model=LastShiftSummary)
async def last_shift_summary(branch_id: int, session: SessionDep, _: ManagerDep):
    """Ventas de la última sesión (turno) de la sucursal."""
    return await get_last_shift_summary(branch_id, session)


@router.get("/averages", response_model=PeriodAverages)
async def period_averages(
    branch_id: int,
    session: SessionDep,
    _: ManagerDep,
    days: int = Query(default=30, ge=1, le=365, description="Ventana de análisis en días"),
):
    """Promedio de ventas diario, semanal y mensual calculado sobre la ventana indicada."""
    return await get_period_averages(branch_id, days, session)


@router.get("/trend", response_model=list[DailySalesPoint])
async def sales_trend(
    branch_id: int,
    session: SessionDep,
    _: ManagerDep,
    days: int = Query(default=30, ge=1, le=365, description="Número de días hacia atrás"),
):
    """Tendencia de ventas: total diario para cada día del período."""
    return await get_sales_trend(branch_id, days, session)


@router.get("/by-weekday", response_model=list[WeekdaySales])
async def sales_by_weekday(
    branch_id: int,
    session: SessionDep,
    _: ManagerDep,
    days: int = Query(default=90, ge=1, le=365, description="Ventana de análisis en días"),
):
    """Distribución de ventas por día de la semana (0=Lunes … 6=Domingo)."""
    return await get_sales_by_weekday(branch_id, days, session)


@router.get("/top-products", response_model=list[ProductRankingPoint])
async def top_products(
    branch_id: int,
    session: SessionDep,
    _: ManagerDep,
    days: int = Query(default=30, ge=1, le=365, description="Ventana de análisis en días"),
    limit: int = Query(default=10, ge=1, le=50, description="Cantidad de productos a mostrar"),
    co_limit: int = Query(default=5, ge=0, le=20, description="Productos acompañantes a mostrar por cada producto"),
):
    """Ranking de productos más vendidos por cantidad, dentro del período indicado."""
    return await get_top_products(branch_id, days, limit, session, co_limit)


@router.get("/monthly-trend", response_model=list[MonthlyTrendPoint])
async def monthly_sales_trend(
    branch_id: int,
    session: SessionDep,
    _: ManagerDep,
    months: int = Query(default=6, ge=1, le=24, description="Número de meses hacia atrás"),
):
    """Tendencia mensual: ventas brutas, netas, propinas y pérdidas por mes."""
    return await get_monthly_sales_trend(branch_id, months, session)
