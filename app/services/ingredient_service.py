from app.models.inventory import Ingredient
from app.schemas.inventory import IngredientCreate, IngredientUpdate
from app.services.base import CRUDBase


class IngredientService(CRUDBase[Ingredient, IngredientCreate, IngredientUpdate]):
    pass


ingredient_service = IngredientService(Ingredient)
