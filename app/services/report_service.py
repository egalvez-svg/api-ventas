from collections import defaultdict
from datetime import date, datetime, timedelta

from fastapi import HTTPException, status
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.base import Shift
from app.models.inventory import Product
from app.models.sales import Order, OrderItem
from app.schemas.reports import DailySalesPoint, LastShiftSummary, MonthlyTrendPoint, PeriodAverages, ProductRankingPoint, WeekdaySales

WEEKDAY_NAMES = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
MONTH_LABELS = ["", "ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]


async def get_last_shift_summary(branch_id: int, session: AsyncSession) -> LastShiftSummary:
    result = await session.exec(
        select(Shift)
        .where(Shift.branch_id == branch_id)
        .order_by(Shift.opened_at.desc())  # type: ignore[attr-defined]
        .limit(1)
    )
    shift = result.first()
    if not shift:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No se encontró ninguna sesión para esta sucursal")

    orders_result = await session.exec(
        select(Order).where(Order.shift_id == shift.id, Order.status == "paid")
    )
    orders = orders_result.all()

    total_sales = sum(o.total for o in orders)
    total_tips = sum(o.tip for o in orders)
    order_count = len(orders)

    return LastShiftSummary(
        shift_id=shift.id,
        opened_at=shift.opened_at,
        closed_at=shift.closed_at,
        is_active=shift.is_active,
        total_sales=total_sales,
        total_tips=total_tips,
        order_count=order_count,
        average_order=total_sales / order_count if order_count else 0.0,
    )


async def get_period_averages(branch_id: int, days: int, session: AsyncSession) -> PeriodAverages:
    since = datetime.utcnow() - timedelta(days=days)
    orders_result = await session.exec(
        select(Order).where(
            Order.branch_id == branch_id,
            Order.status == "paid",
            Order.created_at >= since,
        )
    )
    orders = orders_result.all()

    # Aggregate totals per calendar day
    by_day: dict[date, float] = defaultdict(float)
    for o in orders:
        by_day[o.created_at.date()] += o.total

    days_with_sales = len(by_day)
    total = sum(by_day.values())

    daily_avg = total / days if days else 0.0
    weekly_avg = daily_avg * 7
    monthly_avg = daily_avg * 30

    return PeriodAverages(
        daily_average=round(daily_avg, 2),
        weekly_average=round(weekly_avg, 2),
        monthly_average=round(monthly_avg, 2),
        total_days_with_sales=days_with_sales,
        period_days=days,
    )


async def get_sales_trend(branch_id: int, days: int, session: AsyncSession) -> list[DailySalesPoint]:
    since = datetime.utcnow() - timedelta(days=days)
    orders_result = await session.exec(
        select(Order).where(
            Order.branch_id == branch_id,
            Order.status == "paid",
            Order.created_at >= since,
        )
    )
    orders = orders_result.all()

    by_day: dict[date, list] = defaultdict(list)
    for o in orders:
        by_day[o.created_at.date()].append(o.total)

    trend = [
        DailySalesPoint(date=d, total=round(sum(totals), 2), order_count=len(totals))
        for d, totals in sorted(by_day.items())
    ]
    return trend


async def get_sales_by_weekday(branch_id: int, days: int, session: AsyncSession) -> list[WeekdaySales]:
    since = datetime.utcnow() - timedelta(days=days)
    orders_result = await session.exec(
        select(Order).where(
            Order.branch_id == branch_id,
            Order.status == "paid",
            Order.created_at >= since,
        )
    )
    orders = orders_result.all()

    # weekday() returns 0=Monday … 6=Sunday
    by_weekday: dict[int, list[float]] = defaultdict(list)
    for o in orders:
        by_weekday[o.created_at.weekday()].append(o.total)

    result = []
    for wd in range(7):
        totals = by_weekday[wd]
        total = sum(totals)
        count = len(totals)
        result.append(
            WeekdaySales(
                weekday=wd,
                weekday_name=WEEKDAY_NAMES[wd],
                total=round(total, 2),
                order_count=count,
                average_order=round(total / count, 2) if count else 0.0,
            )
        )
    return result


async def get_top_products(
    branch_id: int, days: int, limit: int, session: AsyncSession
) -> list[ProductRankingPoint]:
    since = datetime.utcnow() - timedelta(days=days)

    orders_result = await session.exec(
        select(Order).where(
            Order.branch_id == branch_id,
            Order.status == "paid",
            Order.created_at >= since,
        )
    )
    order_ids = [o.id for o in orders_result.all()]

    if not order_ids:
        return []

    items_result = await session.exec(
        select(OrderItem).where(OrderItem.order_id.in_(order_ids))
    )
    items = items_result.all()

    # Agregación en memoria: {product_id: {quantity, revenue, order_ids}}
    agg: dict[int, dict] = defaultdict(lambda: {"quantity": 0, "revenue": 0.0, "orders": set()})
    for item in items:
        agg[item.product_id]["quantity"] += item.quantity
        agg[item.product_id]["revenue"] += item.quantity * item.price
        agg[item.product_id]["orders"].add(item.order_id)

    # Cargar nombres de productos en una sola pasada
    product_ids = list(agg.keys())
    products_result = await session.exec(select(Product).where(Product.id.in_(product_ids)))
    product_names = {p.id: p.name for p in products_result.all()}

    ranking = sorted(agg.items(), key=lambda x: x[1]["quantity"], reverse=True)[:limit]

    return [
        ProductRankingPoint(
            rank=i + 1,
            product_id=pid,
            product_name=product_names.get(pid, "—"),
            total_quantity=data["quantity"],
            total_revenue=round(data["revenue"], 2),
            order_count=len(data["orders"]),
        )
        for i, (pid, data) in enumerate(ranking)
    ]


async def get_monthly_sales_trend(branch_id: int, months: int, session: AsyncSession) -> list[MonthlyTrendPoint]:
    since = datetime.utcnow() - timedelta(days=months * 31)

    paid_result = await session.exec(
        select(Order).where(
            Order.branch_id == branch_id,
            Order.status == "paid",
            Order.created_at >= since,
        )
    )
    cancelled_result = await session.exec(
        select(Order).where(
            Order.branch_id == branch_id,
            Order.status == "cancelled",
            Order.created_at >= since,
        )
    )

    by_month: dict[tuple[int, int], dict] = defaultdict(lambda: {"gross": 0.0, "tips": 0.0, "losses": 0.0, "count": 0})

    for o in paid_result.all():
        key = (o.created_at.year, o.created_at.month)
        by_month[key]["gross"] += o.total
        by_month[key]["tips"] += o.tip
        by_month[key]["count"] += 1

    for o in cancelled_result.all():
        key = (o.created_at.year, o.created_at.month)
        by_month[key]["losses"] += o.total

    trend = []
    for (year, month) in sorted(by_month.keys()):
        data = by_month[(year, month)]
        gross = round(data["gross"], 2)
        tips = round(data["tips"], 2)
        trend.append(MonthlyTrendPoint(
            year=year,
            month=month,
            month_label=MONTH_LABELS[month],
            gross_sales=gross,
            net_sales=round(gross - tips, 2),
            tips=tips,
            net_losses=round(data["losses"], 2),
            order_count=data["count"],
        ))
    return trend
