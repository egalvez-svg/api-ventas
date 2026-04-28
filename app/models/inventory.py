from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship

class Category(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)
    description: Optional[str] = None

class Ingredient(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    unit: str # gr, ml, un, kg
    cost_per_unit: float = 0.0

class Product(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    description: Optional[str] = None
    price: float
    category_id: int = Field(foreign_key="category.id")
    is_active: bool = Field(default=True)
    
    # Receta (Relación muchos a muchos con ingredientes a través de Recipe)
    ingredients: List["Recipe"] = Relationship(back_populates="product", sa_relationship_kwargs={"lazy": "raise"})

class Recipe(SQLModel, table=True):
    product_id: int = Field(foreign_key="product.id", primary_key=True)
    ingredient_id: int = Field(foreign_key="ingredient.id", primary_key=True)
    quantity: float # Cantidad necesaria por cada unidad de producto
    
    product: Product = Relationship(back_populates="ingredients", sa_relationship_kwargs={"lazy": "raise"})
    ingredient: Ingredient = Relationship(sa_relationship_kwargs={"lazy": "raise"})

class BranchStock(SQLModel, table=True):
    branch_id: int = Field(foreign_key="branch.id", primary_key=True)
    ingredient_id: int = Field(foreign_key="ingredient.id", primary_key=True)
    quantity: float = 0.0 # Stock actual en esta sucursal
    min_stock: float = 0.0 # Alerta de stock crítico
