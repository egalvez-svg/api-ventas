from datetime import date, datetime
from pydantic import BaseModel


# ── Per-branch endpoints ──────────────────────────────────────────────────────

class LastShiftSummary(BaseModel):
    shift_id: int
    opened_at: datetime
    closed_at: datetime | None
    is_active: bool
    total_sales: float
    total_tips: float
    order_count: int
    average_order: float


class PeriodAverages(BaseModel):
    daily_average: float
    weekly_average: float
    monthly_average: float
    total_days_with_sales: int
    period_days: int


class DailySalesPoint(BaseModel):
    date: date
    total: float
    order_count: int


class WeekdaySales(BaseModel):
    weekday: int        # 0=Monday … 6=Sunday
    weekday_name: str
    total: float
    order_count: int
    average_order: float


# ── Global admin endpoints ────────────────────────────────────────────────────

class BranchLastShift(BaseModel):
    branch_id: int
    branch_name: str
    shift_id: int | None
    opened_at: datetime | None
    closed_at: datetime | None
    is_active: bool
    total_sales: float
    total_tips: float
    order_count: int
    average_order: float


class GlobalLastShift(BaseModel):
    global_total_sales: float
    global_total_tips: float
    global_order_count: int
    global_average_order: float
    by_branch: list[BranchLastShift]


class BranchAverages(BaseModel):
    branch_id: int
    branch_name: str
    daily_average: float
    weekly_average: float
    monthly_average: float
    total_days_with_sales: int


class GlobalAverages(BaseModel):
    daily_average: float
    weekly_average: float
    monthly_average: float
    period_days: int
    by_branch: list[BranchAverages]


class BranchTrend(BaseModel):
    branch_id: int
    branch_name: str
    trend: list[DailySalesPoint]


class GlobalTrend(BaseModel):
    global_trend: list[DailySalesPoint]
    by_branch: list[BranchTrend]


class BranchWeekday(BaseModel):
    branch_id: int
    branch_name: str
    weekdays: list[WeekdaySales]


class GlobalWeekday(BaseModel):
    global_weekdays: list[WeekdaySales]
    by_branch: list[BranchWeekday]


class CoProductPoint(BaseModel):
    product_id: int
    product_name: str
    co_order_count: int     # órdenes donde aparecieron juntos
    percentage: float       # co_order_count / órdenes del producto principal * 100


class ProductRankingPoint(BaseModel):
    rank: int
    product_id: int
    product_name: str
    category_id: int | None
    category_name: str | None
    total_quantity: int
    total_revenue: float
    order_count: int                            # en cuántas órdenes distintas apareció
    frequently_bought_with: list[CoProductPoint] = []


class MonthlyTrendPoint(BaseModel):
    year: int
    month: int
    month_label: str       # "ene", "feb", …, "dic"
    gross_sales: float     # sum total órdenes paid
    net_sales: float       # gross_sales − tips
    tips: float            # sum tip órdenes paid
    net_losses: float      # sum total órdenes cancelled
    order_count: int


class BranchMonthlyTrend(BaseModel):
    branch_id: int
    branch_name: str
    trend: list[MonthlyTrendPoint]


class GlobalMonthlyTrend(BaseModel):
    global_trend: list[MonthlyTrendPoint]
    by_branch: list[BranchMonthlyTrend]
