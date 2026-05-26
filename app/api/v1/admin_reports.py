from fastapi import APIRouter, Query

from app.core.deps import AdminDep, SessionDep
from app.schemas.reports import GlobalAverages, GlobalLastShift, GlobalMonthlyTrend, GlobalTrend, GlobalWeekday
from app.services.admin_report_service import (
    get_global_averages,
    get_global_by_weekday,
    get_global_last_shift,
    get_global_monthly_trend,
    get_global_trend,
)

router = APIRouter(prefix="/reports", tags=["Reports (Admin)"])


@router.get("/last-shift", response_model=GlobalLastShift)
async def global_last_shift(session: SessionDep, _: AdminDep):
    """Ventas de la última sesión de cada sucursal + total consolidado."""
    return await get_global_last_shift(session)


@router.get("/averages", response_model=GlobalAverages)
async def global_averages(
    session: SessionDep,
    _: AdminDep,
    days: int = Query(default=30, ge=1, le=365, description="Ventana de análisis en días"),
):
    """Promedios diario/semanal/mensual por sucursal + total consolidado."""
    return await get_global_averages(days, session)


@router.get("/trend", response_model=GlobalTrend)
async def global_trend(
    session: SessionDep,
    _: AdminDep,
    days: int = Query(default=30, ge=1, le=365, description="Días hacia atrás"),
):
    """Tendencia diaria de ventas por sucursal + curva global consolidada."""
    return await get_global_trend(days, session)


@router.get("/by-weekday", response_model=GlobalWeekday)
async def global_by_weekday(
    session: SessionDep,
    _: AdminDep,
    days: int = Query(default=90, ge=1, le=365, description="Ventana de análisis en días"),
):
    """Distribución por día de semana por sucursal + distribución global consolidada."""
    return await get_global_by_weekday(days, session)


@router.get("/monthly-trend", response_model=GlobalMonthlyTrend)
async def global_monthly_trend(
    session: SessionDep,
    _: AdminDep,
    months: int = Query(default=6, ge=1, le=24, description="Número de meses hacia atrás"),
):
    """Tendencia mensual consolidada + desglose por sucursal: brutas, netas, propinas y pérdidas."""
    return await get_global_monthly_trend(months, session)
