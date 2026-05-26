from typing import Optional
from sqlmodel import SQLModel


class CategoryCreate(SQLModel):
    name: str
    description: Optional[str] = None


class CategoryRead(SQLModel):
    id: int
    branch_id: int
    name: str
    description: Optional[str] = None


class CategoryUpdate(SQLModel):
    name: Optional[str] = None
    description: Optional[str] = None


class IngredientCreate(SQLModel):
    name: str
    unit: str  # gr, ml, un, kg
    cost_per_unit: float = 0.0


class IngredientRead(SQLModel):
    id: int
    branch_id: int
    name: str
    unit: str
    cost_per_unit: float


class IngredientUpdate(SQLModel):
    name: Optional[str] = None
    unit: Optional[str] = None
    cost_per_unit: Optional[float] = None


class RecipeItemCreate(SQLModel):
    ingredient_id: int
    quantity: float


class RecipeItemRead(SQLModel):
    ingredient_id: int
    ingredient_name: str
    unit: str
    quantity: float


class ProductCreate(SQLModel):
    name: str
    description: Optional[str] = None
    price: float
    category_id: int
    is_active: bool = True


class ProductRead(SQLModel):
    id: int
    branch_id: int
    name: str
    description: Optional[str] = None
    price: float
    category_id: int
    is_active: bool


class ProductReadWithRecipe(ProductRead):
    recipe: list[RecipeItemRead] = []


class ProductUpdate(SQLModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    category_id: Optional[int] = None
    is_active: Optional[bool] = None


class BranchStockRead(SQLModel):
    branch_id: int
    ingredient_id: int
    ingredient_name: str
    unit: str
    quantity: float
    min_stock: float
    is_critical: bool


class BranchStockUpdate(SQLModel):
    quantity: Optional[float] = None
    min_stock: Optional[float] = None
