from collections import defaultdict
from datetime import date, datetime, timedelta

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.base import Branch, Shift
from app.models.sales import Order
from app.schemas.reports import (
    BranchAverages,
    BranchLastShift,
    BranchMonthlyTrend,
    BranchTrend,
    BranchWeekday,
    DailySalesPoint,
    GlobalAverages,
    GlobalLastShift,
    GlobalMonthlyTrend,
    GlobalTrend,
    GlobalWeekday,
    MonthlyTrendPoint,
    WeekdaySales,
)

WEEKDAY_NAMES = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
MONTH_LABELS = ["", "ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]


async def _get_active_branches(session: AsyncSession) -> list[Branch]:
    result = await session.exec(select(Branch).where(Branch.is_active == True))
    return list(result.all())


async def get_global_last_shift(session: AsyncSession) -> GlobalLastShift:
    branches = await _get_active_branches(session)

    # Last shift per branch in one query, then group in Python
    all_shifts_result = await session.exec(select(Shift).order_by(Shift.opened_at.desc()))  # type: ignore[attr-defined]
    all_shifts = all_shifts_result.all()

    last_shift_by_branch: dict[int, Shift] = {}
    for s in all_shifts:
        if s.branch_id not in last_shift_by_branch:
            last_shift_by_branch[s.branch_id] = s

    shift_ids = [s.id for s in last_shift_by_branch.values() if s.id is not None]
    orders_by_shift: dict[int, list[Order]] = defaultdict(list)
    if shift_ids:
        orders_result = await session.exec(
            select(Order).where(Order.shift_id.in_(shift_ids), Order.status == "paid")  # type: ignore[attr-defined]
        )
        for o in orders_result.all():
            orders_by_shift[o.shift_id].append(o)

    branch_map = {b.id: b for b in branches}
    by_branch: list[BranchLastShift] = []
    global_sales = 0.0
    global_tips = 0.0
    global_count = 0

    for branch in branches:
        shift = last_shift_by_branch.get(branch.id)
        orders = orders_by_shift.get(shift.id, []) if shift else []
        total_sales = sum(o.total for o in orders)
        total_tips = sum(o.tip for o in orders)
        count = len(orders)

        global_sales += total_sales
        global_tips += total_tips
        global_count += count

        by_branch.append(BranchLastShift(
            branch_id=branch.id,
            branch_name=branch.name,
            shift_id=shift.id if shift else None,
            opened_at=shift.opened_at if shift else None,
            closed_at=shift.closed_at if shift else None,
            is_active=shift.is_active if shift else False,
            total_sales=total_sales,
            total_tips=total_tips,
            order_count=count,
            average_order=round(total_sales / count, 2) if count else 0.0,
        ))

    return GlobalLastShift(
        global_total_sales=round(global_sales, 2),
        global_total_tips=round(global_tips, 2),
        global_order_count=global_count,
        global_average_order=round(global_sales / global_count, 2) if global_count else 0.0,
        by_branch=by_branch,
    )


async def get_global_averages(days: int, session: AsyncSession) -> GlobalAverages:
    branches = await _get_active_branches(session)
    since = datetime.utcnow() - timedelta(days=days)

    orders_result = await session.exec(
        select(Order).where(Order.status == "paid", Order.created_at >= since)
    )
    all_orders = orders_result.all()

    # Group by branch
    orders_by_branch: dict[int, list[Order]] = defaultdict(list)
    for o in all_orders:
        orders_by_branch[o.branch_id].append(o)

    by_branch: list[BranchAverages] = []
    global_by_day: dict[date, float] = defaultdict(float)

    for branch in branches:
        orders = orders_by_branch.get(branch.id, [])
        by_day: dict[date, float] = defaultdict(float)
        for o in orders:
            d = o.created_at.date()
            by_day[d] += o.total
            global_by_day[d] += o.total

        total = sum(by_day.values())
        daily_avg = total / days
        by_branch.append(BranchAverages(
            branch_id=branch.id,
            branch_name=branch.name,
            daily_average=round(daily_avg, 2),
            weekly_average=round(daily_avg * 7, 2),
            monthly_average=round(daily_avg * 30, 2),
            total_days_with_sales=len(by_day),
        ))

    global_total = sum(global_by_day.values())
    global_daily = global_total / days

    return GlobalAverages(
        daily_average=round(global_daily, 2),
        weekly_average=round(global_daily * 7, 2),
        monthly_average=round(global_daily * 30, 2),
        period_days=days,
        by_branch=by_branch,
    )


async def get_global_trend(days: int, session: AsyncSession) -> GlobalTrend:
    branches = await _get_active_branches(session)
    since = datetime.utcnow() - timedelta(days=days)

    orders_result = await session.exec(
        select(Order).where(Order.status == "paid", Order.created_at >= since)
    )
    all_orders = orders_result.all()

    global_by_day: dict[date, list[float]] = defaultdict(list)
    branch_by_day: dict[int, dict[date, list[float]]] = defaultdict(lambda: defaultdict(list))

    for o in all_orders:
        d = o.created_at.date()
        global_by_day[d].append(o.total)
        branch_by_day[o.branch_id][d].append(o.total)

    def build_trend(by_day: dict[date, list[float]]) -> list[DailySalesPoint]:
        return [
            DailySalesPoint(date=d, total=round(sum(totals), 2), order_count=len(totals))
            for d, totals in sorted(by_day.items())
        ]

    by_branch = [
        BranchTrend(
            branch_id=branch.id,
            branch_name=branch.name,
            trend=build_trend(branch_by_day.get(branch.id, {})),
        )
        for branch in branches
    ]

    return GlobalTrend(
        global_trend=build_trend(global_by_day),
        by_branch=by_branch,
    )


async def get_global_by_weekday(days: int, session: AsyncSession) -> GlobalWeekday:
    branches = await _get_active_branches(session)
    since = datetime.utcnow() - timedelta(days=days)

    orders_result = await session.exec(
        select(Order).where(Order.status == "paid", Order.created_at >= since)
    )
    all_orders = orders_result.all()

    global_wd: dict[int, list[float]] = defaultdict(list)
    branch_wd: dict[int, dict[int, list[float]]] = defaultdict(lambda: defaultdict(list))

    for o in all_orders:
        wd = o.created_at.weekday()
        global_wd[wd].append(o.total)
        branch_wd[o.branch_id][wd].append(o.total)

    def build_weekdays(wd_data: dict[int, list[float]]) -> list[WeekdaySales]:
        result = []
        for wd in range(7):
            totals = wd_data.get(wd, [])
            total = sum(totals)
            count = len(totals)
            result.append(WeekdaySales(
                weekday=wd,
                weekday_name=WEEKDAY_NAMES[wd],
                total=round(total, 2),
                order_count=count,
                average_order=round(total / count, 2) if count else 0.0,
            ))
        return result

    by_branch = [
        BranchWeekday(
            branch_id=branch.id,
            branch_name=branch.name,
            weekdays=build_weekdays(branch_wd.get(branch.id, {})),
        )
        for branch in branches
    ]

    return GlobalWeekday(
        global_weekdays=build_weekdays(global_wd),
        by_branch=by_branch,
    )


async def get_global_monthly_trend(months: int, session: AsyncSession) -> GlobalMonthlyTrend:
    branches = await _get_active_branches(session)
    since = datetime.utcnow() - timedelta(days=months * 31)

    paid_result = await session.exec(
        select(Order).where(Order.status == "paid", Order.created_at >= since)
    )
    cancelled_result = await session.exec(
        select(Order).where(Order.status == "cancelled", Order.created_at >= since)
    )

    # {branch_id: {(year, month): {gross, tips, losses, count}}}
    branch_data: dict[int, dict[tuple[int, int], dict]] = defaultdict(
        lambda: defaultdict(lambda: {"gross": 0.0, "tips": 0.0, "losses": 0.0, "count": 0})
    )
    global_data: dict[tuple[int, int], dict] = defaultdict(
        lambda: {"gross": 0.0, "tips": 0.0, "losses": 0.0, "count": 0}
    )

    for o in paid_result.all():
        key = (o.created_at.year, o.created_at.month)
        for d in (branch_data[o.branch_id][key], global_data[key]):
            d["gross"] += o.total
            d["tips"] += o.tip
            d["count"] += 1

    for o in cancelled_result.all():
        key = (o.created_at.year, o.created_at.month)
        branch_data[o.branch_id][key]["losses"] += o.total
        global_data[key]["losses"] += o.total

    def build_monthly(data: dict[tuple[int, int], dict]) -> list[MonthlyTrendPoint]:
        points = []
        for (year, month) in sorted(data.keys()):
            d = data[(year, month)]
            gross = round(d["gross"], 2)
            tips = round(d["tips"], 2)
            points.append(MonthlyTrendPoint(
                year=year,
                month=month,
                month_label=MONTH_LABELS[month],
                gross_sales=gross,
                net_sales=round(gross - tips, 2),
                tips=tips,
                net_losses=round(d["losses"], 2),
                order_count=d["count"],
            ))
        return points

    by_branch = [
        BranchMonthlyTrend(
            branch_id=branch.id,
            branch_name=branch.name,
            trend=build_monthly(branch_data.get(branch.id, {})),
        )
        for branch in branches
    ]

    return GlobalMonthlyTrend(
        global_trend=build_monthly(global_data),
        by_branch=by_branch,
    )
