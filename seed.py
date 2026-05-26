"""
Seed script — Garage Grill & Garage Sushi

Crea:
  - 2 sucursales: Garage Grill (parrilladas) y Garage Sushi
  - Categorías, ingredientes y productos por sucursal (catálogo independiente)
  - 1 admin con membresía en ambas sucursales
  - 1 gerente, 1 garzón, 1 cocinero, 1 cajero por sucursal
  - Mesas por sucursal
  - Stock inicial por sucursal

Uso:
    python seed.py
"""
import asyncio

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.security import get_password_hash
from app.db.session import engine
from app.models.base import Branch, User, UserBranchRole
from app.models.inventory import BranchStock, Category, Ingredient, Product, Recipe
from app.models.sales import Table

# ─── Sucursales ──────────────────────────────────────────────────────────────

BRANCHES = [
    {
        "name":    "Garage Grill",
        "address": "Av. Providencia 1234, Providencia, Santiago",
        "phone":   "+56 2 2345 6789",
    },
    {
        "name":    "Garage Sushi",
        "address": "Av. Providencia 1236, Providencia, Santiago",
        "phone":   "+56 2 2345 6790",
    },
]

# ─── Catálogo por sucursal ───────────────────────────────────────────────────

CATALOG = {
    "Garage Grill": {
        "categories": [
            {"name": "Carnes",       "description": "Cortes a la parrilla"},
            {"name": "Guarniciones", "description": "Acompañamientos"},
            {"name": "Entradas",     "description": "Entradas y aperitivos"},
            {"name": "Bebidas",      "description": "Bebidas y tragos"},
            {"name": "Postres",      "description": "Postres y dulces"},
        ],
        "ingredients": [
            {"name": "Entraña",             "unit": "kg",  "cost_per_unit": 12000.0},
            {"name": "Lomo vetado",         "unit": "kg",  "cost_per_unit": 18000.0},
            {"name": "Vacío",               "unit": "kg",  "cost_per_unit": 10500.0},
            {"name": "Costillas de cerdo",  "unit": "kg",  "cost_per_unit":  8500.0},
            {"name": "Longaniza",           "unit": "un",  "cost_per_unit":   900.0},
            {"name": "Chorizo parrillero",  "unit": "un",  "cost_per_unit":  1100.0},
            {"name": "Papa",                "unit": "kg",  "cost_per_unit":  1200.0},
            {"name": "Mantequilla",         "unit": "gr",  "cost_per_unit":    12.0},
            {"name": "Lechuga",             "unit": "un",  "cost_per_unit":  1200.0},
            {"name": "Tomate",              "unit": "un",  "cost_per_unit":   400.0},
            {"name": "Sal gruesa",          "unit": "gr",  "cost_per_unit":     1.5},
            {"name": "Chimichurri",         "unit": "gr",  "cost_per_unit":    25.0},
            {"name": "Pan amasado",         "unit": "un",  "cost_per_unit":   350.0},
            {"name": "Agua mineral 500ml",  "unit": "un",  "cost_per_unit":   500.0},
            {"name": "Cerveza 330ml",       "unit": "un",  "cost_per_unit":   900.0},
            {"name": "Limón",               "unit": "un",  "cost_per_unit":   150.0},
        ],
        "products": [
            {"name": "Entraña 300g",               "price":  9900, "category": "Carnes",       "description": "Corte de entraña a la parrilla, 300g"},
            {"name": "Lomo Vetado 300g",            "price": 11900, "category": "Carnes",       "description": "Lomo vetado a la parrilla, 300g"},
            {"name": "Vacío 300g",                  "price":  9400, "category": "Carnes",       "description": "Vacío a la parrilla, 300g"},
            {"name": "Costillas de Cerdo 400g",     "price":  8900, "category": "Carnes",       "description": "Costillas a la parrilla, 400g"},
            {"name": "Mix Parrillada Personal",     "price": 12900, "category": "Carnes",       "description": "Entraña, longaniza, chorizo y vacío"},
            {"name": "Papas Fritas",                "price":  2900, "category": "Guarniciones", "description": "Papas al horno con sal y mantequilla"},
            {"name": "Ensalada Mixta",              "price":  2400, "category": "Guarniciones", "description": "Lechuga, tomate y limón"},
            {"name": "Pan Amasado c/ Mantequilla",  "price":  1900, "category": "Entradas",     "description": "Pan amasado artesanal con mantequilla"},
            {"name": "Agua Mineral 500ml",          "price":  1200, "category": "Bebidas",      "description": "Agua mineral sin gas"},
            {"name": "Cerveza Artesanal 330ml",     "price":  3500, "category": "Bebidas",      "description": "Cerveza artesanal nacional"},
            {"name": "Fruta de la Temporada",       "price":  2800, "category": "Postres",      "description": "Selección de frutas frescas"},
        ],
        "recipes": [
            ("Entraña 300g",              "Entraña",            0.3),
            ("Entraña 300g",              "Sal gruesa",         5.0),
            ("Entraña 300g",              "Chimichurri",       10.0),
            ("Lomo Vetado 300g",          "Lomo vetado",        0.3),
            ("Lomo Vetado 300g",          "Sal gruesa",         5.0),
            ("Lomo Vetado 300g",          "Chimichurri",       10.0),
            ("Vacío 300g",                "Vacío",              0.3),
            ("Vacío 300g",                "Sal gruesa",         5.0),
            ("Vacío 300g",                "Chimichurri",       10.0),
            ("Costillas de Cerdo 400g",   "Costillas de cerdo", 0.4),
            ("Costillas de Cerdo 400g",   "Sal gruesa",         5.0),
            ("Costillas de Cerdo 400g",   "Chimichurri",       15.0),
            ("Mix Parrillada Personal",   "Entraña",            0.15),
            ("Mix Parrillada Personal",   "Vacío",              0.1),
            ("Mix Parrillada Personal",   "Longaniza",          1.0),
            ("Mix Parrillada Personal",   "Chorizo parrillero", 1.0),
            ("Mix Parrillada Personal",   "Sal gruesa",         8.0),
            ("Mix Parrillada Personal",   "Chimichurri",       20.0),
            ("Papas Fritas",              "Papa",               0.2),
            ("Papas Fritas",              "Mantequilla",       20.0),
            ("Papas Fritas",              "Sal gruesa",         3.0),
            ("Ensalada Mixta",            "Lechuga",            0.25),
            ("Ensalada Mixta",            "Tomate",             1.0),
            ("Ensalada Mixta",            "Limón",              1.0),
            ("Pan Amasado c/ Mantequilla","Pan amasado",        1.0),
            ("Pan Amasado c/ Mantequilla","Mantequilla",       30.0),
            ("Agua Mineral 500ml",        "Agua mineral 500ml", 1.0),
            ("Cerveza Artesanal 330ml",   "Cerveza 330ml",      1.0),
        ],
        "stock": [
            # (ingrediente, cantidad, mínimo)
            ("Entraña",            15.0,   2.0),
            ("Lomo vetado",        10.0,   2.0),
            ("Vacío",              12.0,   2.0),
            ("Costillas de cerdo", 10.0,   2.0),
            ("Longaniza",          40.0,   5.0),
            ("Chorizo parrillero", 40.0,   5.0),
            ("Papa",               20.0,   3.0),
            ("Mantequilla",      1000.0, 200.0),
            ("Lechuga",            10.0,   2.0),
            ("Tomate",             20.0,   5.0),
            ("Sal gruesa",       3000.0, 500.0),
            ("Chimichurri",      1000.0, 200.0),
            ("Pan amasado",        30.0,   5.0),
            ("Agua mineral 500ml", 100.0,  12.0),
            ("Cerveza 330ml",       80.0,  12.0),
            ("Limón",               30.0,   5.0),
        ],
        "tables": 15,
    },
    "Garage Sushi": {
        "categories": [
            {"name": "Nigiris",  "description": "Nigiris de distintas variedades"},
            {"name": "Rolls",    "description": "Rolls y makis variados"},
            {"name": "Entradas", "description": "Entradas y aperitivos"},
            {"name": "Bebidas",  "description": "Bebidas y tragos"},
            {"name": "Postres",  "description": "Postres y dulces"},
        ],
        "ingredients": [
            {"name": "Arroz para sushi",    "unit": "gr", "cost_per_unit":  0.006},
            {"name": "Alga nori",           "unit": "un", "cost_per_unit":  150.0},
            {"name": "Salmón fresco",       "unit": "gr", "cost_per_unit":   28.0},
            {"name": "Atún fresco",         "unit": "gr", "cost_per_unit":   35.0},
            {"name": "Palta",               "unit": "gr", "cost_per_unit":   10.0},
            {"name": "Queso crema",         "unit": "gr", "cost_per_unit":    8.0},
            {"name": "Pepino japonés",      "unit": "gr", "cost_per_unit":    4.0},
            {"name": "Camarón",             "unit": "gr", "cost_per_unit":   22.0},
            {"name": "Langostino",          "unit": "gr", "cost_per_unit":   30.0},
            {"name": "Surimi",              "unit": "gr", "cost_per_unit":    6.0},
            {"name": "Vinagre de arroz",    "unit": "ml", "cost_per_unit":    3.0},
            {"name": "Semillas de sésamo",  "unit": "gr", "cost_per_unit":   40.0},
            {"name": "Edamame",             "unit": "gr", "cost_per_unit":    5.0},
            {"name": "Agua mineral 500ml",  "unit": "un", "cost_per_unit":  500.0},
            {"name": "Cerveza 330ml",       "unit": "un", "cost_per_unit":  900.0},
            {"name": "Limón",               "unit": "un", "cost_per_unit":  150.0},
        ],
        "products": [
            {"name": "Nigiri Salmón x2",             "price":  2600, "category": "Nigiris", "description": "2 piezas de nigiri de salmón fresco"},
            {"name": "Nigiri Atún x2",               "price":  2800, "category": "Nigiris", "description": "2 piezas de nigiri de atún fresco"},
            {"name": "Nigiri Camarón x2",            "price":  2400, "category": "Nigiris", "description": "2 piezas de nigiri de camarón"},
            {"name": "Nigiri Langostino x2",         "price":  3200, "category": "Nigiris", "description": "2 piezas de nigiri de langostino"},
            {"name": "Roll California (8 pzs)",      "price":  5200, "category": "Rolls",   "description": "Surimi, palta y pepino"},
            {"name": "Roll Philadelphia (8 pzs)",    "price":  5500, "category": "Rolls",   "description": "Salmón, queso crema y palta"},
            {"name": "Roll Spicy Salmon (8 pzs)",    "price":  5800, "category": "Rolls",   "description": "Salmón picante con pepino y palta"},
            {"name": "Roll Tempura Camarón (8 pzs)", "price":  6500, "category": "Rolls",   "description": "Camarón tempura con palta y queso crema"},
            {"name": "Roll Dragon (8 pzs)",          "price":  7200, "category": "Rolls",   "description": "Langostino, palta y salsa especial"},
            {"name": "Roll Vegetariano (8 pzs)",     "price":  4500, "category": "Rolls",   "description": "Pepino, palta y queso crema"},
            {"name": "Edamame",                      "price":  2200, "category": "Entradas","description": "Porotos de soya con sal marina"},
            {"name": "Agua Mineral 500ml",           "price":  1200, "category": "Bebidas", "description": "Agua mineral sin gas"},
            {"name": "Cerveza Artesanal 330ml",      "price":  3500, "category": "Bebidas", "description": "Cerveza artesanal nacional"},
            {"name": "Mochi de Helado x3",           "price":  3500, "category": "Postres", "description": "3 mochis de helado surtidos"},
        ],
        "recipes": [
            ("Nigiri Salmón x2",             "Arroz para sushi",    60.0),
            ("Nigiri Salmón x2",             "Salmón fresco",       60.0),
            ("Nigiri Salmón x2",             "Vinagre de arroz",     5.0),
            ("Nigiri Atún x2",               "Arroz para sushi",    60.0),
            ("Nigiri Atún x2",               "Atún fresco",         60.0),
            ("Nigiri Atún x2",               "Vinagre de arroz",     5.0),
            ("Nigiri Camarón x2",            "Arroz para sushi",    60.0),
            ("Nigiri Camarón x2",            "Camarón",             60.0),
            ("Nigiri Camarón x2",            "Vinagre de arroz",     5.0),
            ("Nigiri Langostino x2",         "Arroz para sushi",    60.0),
            ("Nigiri Langostino x2",         "Langostino",          60.0),
            ("Nigiri Langostino x2",         "Vinagre de arroz",     5.0),
            ("Roll California (8 pzs)",      "Arroz para sushi",   120.0),
            ("Roll California (8 pzs)",      "Alga nori",            1.0),
            ("Roll California (8 pzs)",      "Surimi",              60.0),
            ("Roll California (8 pzs)",      "Palta",               40.0),
            ("Roll California (8 pzs)",      "Pepino japonés",      40.0),
            ("Roll California (8 pzs)",      "Semillas de sésamo",   5.0),
            ("Roll California (8 pzs)",      "Vinagre de arroz",    10.0),
            ("Roll Philadelphia (8 pzs)",    "Arroz para sushi",   120.0),
            ("Roll Philadelphia (8 pzs)",    "Alga nori",            1.0),
            ("Roll Philadelphia (8 pzs)",    "Salmón fresco",       80.0),
            ("Roll Philadelphia (8 pzs)",    "Queso crema",         60.0),
            ("Roll Philadelphia (8 pzs)",    "Palta",               40.0),
            ("Roll Philadelphia (8 pzs)",    "Vinagre de arroz",    10.0),
            ("Roll Spicy Salmon (8 pzs)",    "Arroz para sushi",   120.0),
            ("Roll Spicy Salmon (8 pzs)",    "Alga nori",            1.0),
            ("Roll Spicy Salmon (8 pzs)",    "Salmón fresco",      100.0),
            ("Roll Spicy Salmon (8 pzs)",    "Palta",               40.0),
            ("Roll Spicy Salmon (8 pzs)",    "Pepino japonés",      30.0),
            ("Roll Spicy Salmon (8 pzs)",    "Semillas de sésamo",   5.0),
            ("Roll Spicy Salmon (8 pzs)",    "Vinagre de arroz",    10.0),
            ("Roll Tempura Camarón (8 pzs)", "Arroz para sushi",   120.0),
            ("Roll Tempura Camarón (8 pzs)", "Alga nori",            1.0),
            ("Roll Tempura Camarón (8 pzs)", "Camarón",             80.0),
            ("Roll Tempura Camarón (8 pzs)", "Palta",               40.0),
            ("Roll Tempura Camarón (8 pzs)", "Queso crema",         50.0),
            ("Roll Tempura Camarón (8 pzs)", "Semillas de sésamo",   5.0),
            ("Roll Tempura Camarón (8 pzs)", "Vinagre de arroz",    10.0),
            ("Roll Dragon (8 pzs)",          "Arroz para sushi",   120.0),
            ("Roll Dragon (8 pzs)",          "Alga nori",            1.0),
            ("Roll Dragon (8 pzs)",          "Langostino",          80.0),
            ("Roll Dragon (8 pzs)",          "Palta",               60.0),
            ("Roll Dragon (8 pzs)",          "Pepino japonés",      30.0),
            ("Roll Dragon (8 pzs)",          "Semillas de sésamo",   8.0),
            ("Roll Dragon (8 pzs)",          "Vinagre de arroz",    10.0),
            ("Roll Vegetariano (8 pzs)",     "Arroz para sushi",   120.0),
            ("Roll Vegetariano (8 pzs)",     "Alga nori",            1.0),
            ("Roll Vegetariano (8 pzs)",     "Palta",               60.0),
            ("Roll Vegetariano (8 pzs)",     "Pepino japonés",      40.0),
            ("Roll Vegetariano (8 pzs)",     "Queso crema",         60.0),
            ("Roll Vegetariano (8 pzs)",     "Vinagre de arroz",    10.0),
            ("Edamame",                      "Edamame",            100.0),
            ("Agua Mineral 500ml",           "Agua mineral 500ml",   1.0),
            ("Cerveza Artesanal 330ml",      "Cerveza 330ml",        1.0),
        ],
        "stock": [
            ("Arroz para sushi",   5000.0,  500.0),
            ("Alga nori",           100.0,   10.0),
            ("Salmón fresco",      3000.0,  300.0),
            ("Atún fresco",        2000.0,  200.0),
            ("Palta",              2000.0,  200.0),
            ("Queso crema",        1500.0,  200.0),
            ("Pepino japonés",     1500.0,  200.0),
            ("Camarón",            2000.0,  300.0),
            ("Langostino",         1500.0,  200.0),
            ("Surimi",             2000.0,  300.0),
            ("Vinagre de arroz",   2000.0,  300.0),
            ("Semillas de sésamo",  500.0,   50.0),
            ("Edamame",            2000.0,  300.0),
            ("Agua mineral 500ml",  100.0,   12.0),
            ("Cerveza 330ml",        60.0,   12.0),
            ("Limón",                30.0,    5.0),
        ],
        "tables": 12,
    },
}

# ─── Usuarios ────────────────────────────────────────────────────────────────

USERS = [
    {"email": "admin@garage.cl",          "full_name": "Administrador Garage",    "password": "admin1234"},
    {"email": "gerente.grill@garage.cl",  "full_name": "Gerente Garage Grill",    "password": "staff1234"},
    {"email": "gerente.sushi@garage.cl",  "full_name": "Gerente Garage Sushi",    "password": "staff1234"},
    {"email": "garzon.grill@garage.cl",   "full_name": "Garzón Garage Grill",     "password": "staff1234"},
    {"email": "garzon.sushi@garage.cl",   "full_name": "Garzón Garage Sushi",     "password": "staff1234"},
    {"email": "cocina.grill@garage.cl",   "full_name": "Cocina Garage Grill",     "password": "staff1234"},
    {"email": "cocina.sushi@garage.cl",   "full_name": "Cocina Garage Sushi",     "password": "staff1234"},
    {"email": "cajero.grill@garage.cl",   "full_name": "Cajero Garage Grill",     "password": "staff1234"},
    {"email": "cajero.sushi@garage.cl",   "full_name": "Cajero Garage Sushi",     "password": "staff1234"},
]

# (email, sucursal, rol)  — admin aparece en ambas sucursales
ROLES = [
    ("admin@garage.cl",         "Garage Grill", "admin"),
    ("admin@garage.cl",         "Garage Sushi", "admin"),
    ("gerente.grill@garage.cl", "Garage Grill", "manager"),
    ("gerente.sushi@garage.cl", "Garage Sushi", "manager"),
    ("garzon.grill@garage.cl",  "Garage Grill", "waiter"),
    ("garzon.sushi@garage.cl",  "Garage Sushi", "waiter"),
    ("cocina.grill@garage.cl",  "Garage Grill", "kitchen"),
    ("cocina.sushi@garage.cl",  "Garage Sushi", "kitchen"),
    ("cajero.grill@garage.cl",  "Garage Grill", "cashier"),
    ("cajero.sushi@garage.cl",  "Garage Sushi", "cashier"),
]


# ─── Seed ────────────────────────────────────────────────────────────────────

async def seed() -> None:
    async with AsyncSession(engine) as session:

        # ── Sucursales ───────────────────────────────────────────────────────
        print("\n=== Sucursales ===")
        branches: dict[str, Branch] = {}
        for d in BRANCHES:
            r = await session.exec(select(Branch).where(Branch.name == d["name"]))
            obj = r.first()
            if not obj:
                obj = Branch(**d)
                session.add(obj)
                await session.flush()
                print(f"  [+] {obj.name}")
            else:
                print(f"  [=] {obj.name}")
            branches[obj.name] = obj

        # ── Catálogo por sucursal ────────────────────────────────────────────
        for branch_name, data in CATALOG.items():
            branch = branches[branch_name]
            print(f"\n=== {branch_name} ===")

            # Categorías
            cats: dict[str, Category] = {}
            for d in data["categories"]:
                r = await session.exec(
                    select(Category).where(Category.name == d["name"], Category.branch_id == branch.id)
                )
                obj = r.first()
                if not obj:
                    obj = Category(branch_id=branch.id, **d)
                    session.add(obj)
                    await session.flush()
                    print(f"  [+] cat  {obj.name}")
                cats[obj.name] = obj

            # Ingredientes
            ings: dict[str, Ingredient] = {}
            for d in data["ingredients"]:
                r = await session.exec(
                    select(Ingredient).where(Ingredient.name == d["name"], Ingredient.branch_id == branch.id)
                )
                obj = r.first()
                if not obj:
                    obj = Ingredient(branch_id=branch.id, **d)
                    session.add(obj)
                    await session.flush()
                    print(f"  [+] ing  {obj.name}")
                ings[obj.name] = obj

            # Productos
            prods: dict[str, Product] = {}
            for d in data["products"]:
                r = await session.exec(
                    select(Product).where(Product.name == d["name"], Product.branch_id == branch.id)
                )
                obj = r.first()
                if not obj:
                    obj = Product(
                        branch_id=branch.id,
                        name=d["name"],
                        description=d["description"],
                        price=d["price"],
                        category_id=cats[d["category"]].id,
                    )
                    session.add(obj)
                    await session.flush()
                    print(f"  [+] prod {obj.name}  (${obj.price:,.0f})")
                prods[obj.name] = obj

            # Recetas
            recipe_new = 0
            for (prod_name, ing_name, qty) in data["recipes"]:
                prod = prods[prod_name]
                ing  = ings[ing_name]
                r = await session.exec(
                    select(Recipe).where(Recipe.product_id == prod.id, Recipe.ingredient_id == ing.id)
                )
                if not r.first():
                    session.add(Recipe(product_id=prod.id, ingredient_id=ing.id, quantity=qty))
                    recipe_new += 1
            if recipe_new:
                await session.flush()
                print(f"  [+] {recipe_new} líneas de receta")

            # Stock inicial
            stock_new = 0
            for (ing_name, qty, min_stock) in data["stock"]:
                ing = ings[ing_name]
                r = await session.exec(
                    select(BranchStock).where(
                        BranchStock.branch_id == branch.id,
                        BranchStock.ingredient_id == ing.id,
                    )
                )
                if not r.first():
                    session.add(BranchStock(branch_id=branch.id, ingredient_id=ing.id, quantity=qty, min_stock=min_stock))
                    stock_new += 1
            if stock_new:
                await session.flush()
                print(f"  [+] {stock_new} registros de stock")

            # Mesas
            table_new = 0
            for i in range(1, data["tables"] + 1):
                number = f"Mesa {i}"
                r = await session.exec(
                    select(Table).where(Table.branch_id == branch.id, Table.number == number)
                )
                if not r.first():
                    session.add(Table(branch_id=branch.id, number=number))
                    table_new += 1
            if table_new:
                await session.flush()
                print(f"  [+] {table_new} mesas")

        # ── Usuarios ─────────────────────────────────────────────────────────
        print("\n=== Usuarios ===")
        users: dict[str, User] = {}
        for d in USERS:
            r = await session.exec(select(User).where(User.email == d["email"]))
            obj = r.first()
            if not obj:
                obj = User(
                    email=d["email"],
                    full_name=d["full_name"],
                    hashed_password=get_password_hash(d["password"]),
                )
                session.add(obj)
                await session.flush()
                print(f"  [+] {obj.email}")
            else:
                print(f"  [=] {obj.email}")
            users[obj.email] = obj

        # ── Membresías / Roles ────────────────────────────────────────────────
        print("\n=== Membresías ===")
        for (email, branch_name, role) in ROLES:
            user   = users[email]
            branch = branches[branch_name]
            r = await session.exec(
                select(UserBranchRole).where(
                    UserBranchRole.user_id   == user.id,
                    UserBranchRole.branch_id == branch.id,
                    UserBranchRole.role      == role,
                )
            )
            if not r.first():
                session.add(UserBranchRole(user_id=user.id, branch_id=branch.id, role=role))
                print(f"  [+] {email}  →  {role} @ {branch_name}")
            else:
                print(f"  [=] {email}  ({role} @ {branch_name})")
        await session.flush()

        await session.commit()

    # ── Resumen ──────────────────────────────────────────────────────────────
    print()
    print("─" * 60)
    print("Seed completado.")
    print()
    print("Credenciales:")
    print("  admin@garage.cl          /  admin1234")
    print("  <rol>.<local>@garage.cl  /  staff1234")
    print()
    print("Sucursales:")
    for b in BRANCHES:
        print(f"  • {b['name']}  —  {b['address']}")
    print()
    print("Login:  POST /api/v1/auth/login")
    print("  Content-Type: application/x-www-form-urlencoded")
    print("  username=admin@garage.cl&password=admin1234")
    print()


if __name__ == "__main__":
    asyncio.run(seed())
