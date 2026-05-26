"""
Seed script — datos completos para dos sucursales temáticas.

Crea:
  - 2 sucursales: Sushi y Parrilladas Pedro de Valdivia
  - 7 categorías de menú
  - 27 ingredientes
  - 25 productos con recetas completas
  - 9 usuarios con roles por sucursal
  - 12 mesas (sushi) + 15 mesas (parrillada)
  - Stock inicial por sucursal

No crea pedidos — se gestionan desde el frontend.

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

# ─── Datos ──────────────────────────────────────────────────────────────────

CATEGORIES = [
    {"name": "Nigiris",      "description": "Nigiris de distintas variedades"},
    {"name": "Rolls",        "description": "Rolls y makis variados"},
    {"name": "Carnes",       "description": "Cortes de carne a la parrilla"},
    {"name": "Guarniciones", "description": "Acompañamientos y guarniciones"},
    {"name": "Entradas",     "description": "Entradas y aperitivos"},
    {"name": "Bebidas",      "description": "Bebidas y tragos"},
    {"name": "Postres",      "description": "Postres y dulces"},
]

INGREDIENTS = [
    # Sushi
    {"name": "Arroz para sushi",   "unit": "gr",  "cost_per_unit":  0.006},
    {"name": "Alga nori",          "unit": "un",  "cost_per_unit":  150.0},
    {"name": "Salmón fresco",      "unit": "gr",  "cost_per_unit":   28.0},
    {"name": "Atún fresco",        "unit": "gr",  "cost_per_unit":   35.0},
    {"name": "Palta",              "unit": "gr",  "cost_per_unit":   10.0},
    {"name": "Queso crema",        "unit": "gr",  "cost_per_unit":    8.0},
    {"name": "Pepino japonés",     "unit": "gr",  "cost_per_unit":    4.0},
    {"name": "Camarón",            "unit": "gr",  "cost_per_unit":   22.0},
    {"name": "Langostino",         "unit": "gr",  "cost_per_unit":   30.0},
    {"name": "Surimi",             "unit": "gr",  "cost_per_unit":    6.0},
    {"name": "Vinagre de arroz",   "unit": "ml",  "cost_per_unit":    3.0},
    {"name": "Semillas de sésamo", "unit": "gr",  "cost_per_unit":   40.0},
    # Parrillada
    {"name": "Entraña",            "unit": "kg",  "cost_per_unit": 12000.0},
    {"name": "Lomo vetado",        "unit": "kg",  "cost_per_unit": 18000.0},
    {"name": "Vacío",              "unit": "kg",  "cost_per_unit": 10500.0},
    {"name": "Costillas de cerdo", "unit": "kg",  "cost_per_unit":  8500.0},
    {"name": "Longaniza",          "unit": "un",  "cost_per_unit":   900.0},
    {"name": "Chorizo parrillero", "unit": "un",  "cost_per_unit":  1100.0},
    {"name": "Papa",               "unit": "kg",  "cost_per_unit":  1200.0},
    {"name": "Mantequilla",        "unit": "gr",  "cost_per_unit":    12.0},
    {"name": "Lechuga",            "unit": "un",  "cost_per_unit":  1200.0},
    {"name": "Tomate",             "unit": "un",  "cost_per_unit":   400.0},
    {"name": "Sal gruesa",         "unit": "gr",  "cost_per_unit":    1.5},
    {"name": "Chimichurri",        "unit": "gr",  "cost_per_unit":   25.0},
    # Compartidos
    {"name": "Agua mineral 500ml", "unit": "un",  "cost_per_unit":   500.0},
    {"name": "Cerveza 330ml",      "unit": "un",  "cost_per_unit":   900.0},
    {"name": "Limón",              "unit": "un",  "cost_per_unit":   150.0},
]

BRANCHES = [
    {
        "name":    "Sushi Pedro de Valdivia",
        "address": "Av. Pedro de Valdivia 123, Providencia, Santiago",
        "phone":   "+56 2 2345 6789",
    },
    {
        "name":    "Parrilladas Pedro de Valdivia",
        "address": "Av. Pedro de Valdivia 456, Providencia, Santiago",
        "phone":   "+56 2 2345 6790",
    },
]

PRODUCTS = [
    # Nigiris
    {"name": "Nigiri Salmón x2",            "description": "2 piezas de nigiri de salmón fresco",      "price":  2600, "category": "Nigiris"},
    {"name": "Nigiri Atún x2",              "description": "2 piezas de nigiri de atún fresco",         "price":  2800, "category": "Nigiris"},
    {"name": "Nigiri Camarón x2",           "description": "2 piezas de nigiri de camarón",             "price":  2400, "category": "Nigiris"},
    {"name": "Nigiri Langostino x2",        "description": "2 piezas de nigiri de langostino",           "price":  3200, "category": "Nigiris"},
    # Rolls
    {"name": "Roll California (8 pzs)",     "description": "Surimi, palta y pepino",                    "price":  5200, "category": "Rolls"},
    {"name": "Roll Philadelphia (8 pzs)",   "description": "Salmón, queso crema y palta",               "price":  5500, "category": "Rolls"},
    {"name": "Roll Spicy Salmon (8 pzs)",   "description": "Salmón picante con pepino y palta",          "price":  5800, "category": "Rolls"},
    {"name": "Roll Tempura Camarón (8 pzs)","description": "Camarón tempura con palta y queso crema",   "price":  6500, "category": "Rolls"},
    {"name": "Roll Dragon (8 pzs)",         "description": "Langostino, palta y salsa especial",         "price":  7200, "category": "Rolls"},
    {"name": "Roll Vegetariano (8 pzs)",    "description": "Pepino, palta y queso crema",               "price":  4500, "category": "Rolls"},
    # Carnes
    {"name": "Entraña 300g",                "description": "Corte de entraña a la parrilla, 300g",      "price":  9900, "category": "Carnes"},
    {"name": "Lomo Vetado 300g",            "description": "Lomo vetado a la parrilla, 300g",           "price": 11900, "category": "Carnes"},
    {"name": "Vacío 300g",                  "description": "Vacío a la parrilla, 300g",                 "price":  9400, "category": "Carnes"},
    {"name": "Costillas de Cerdo 400g",     "description": "Costillas de cerdo a la parrilla, 400g",    "price":  8900, "category": "Carnes"},
    {"name": "Mix Parrillada Personal",     "description": "Entraña, longaniza, chorizo y vacío",       "price": 12900, "category": "Carnes"},
    # Guarniciones
    {"name": "Papas Fritas",                "description": "Papas al horno con sal y mantequilla",      "price":  2900, "category": "Guarniciones"},
    {"name": "Ensalada Mixta",              "description": "Lechuga, tomate y limón",                   "price":  2400, "category": "Guarniciones"},
    # Entradas
    {"name": "Edamame",                     "description": "Porotos de soya con sal marina",             "price":  2200, "category": "Entradas"},
    {"name": "Sopa Miso",                   "description": "Sopa tradicional japonesa con tofu",         "price":  1800, "category": "Entradas"},
    {"name": "Pan Amasado con Mantequilla", "description": "Pan amasado artesanal con mantequilla",      "price":  1900, "category": "Entradas"},
    # Bebidas
    {"name": "Agua Mineral 500ml",          "description": "Agua mineral sin gas",                      "price":  1200, "category": "Bebidas"},
    {"name": "Cerveza Artesanal 330ml",     "description": "Cerveza artesanal nacional",                "price":  3500, "category": "Bebidas"},
    {"name": "Jugo Natural",                "description": "Jugo de fruta natural del día",              "price":  2200, "category": "Bebidas"},
    # Postres
    {"name": "Mochi de Helado x3",          "description": "3 mochis de helado surtidos",               "price":  3500, "category": "Postres"},
    {"name": "Fruta de la Temporada",       "description": "Selección de frutas frescas de temporada",  "price":  2800, "category": "Postres"},
]

# (producto, ingrediente, cantidad)
RECIPES = [
    # Nigiri Salmón x2
    ("Nigiri Salmón x2",             "Arroz para sushi",      60.0),
    ("Nigiri Salmón x2",             "Salmón fresco",         60.0),
    ("Nigiri Salmón x2",             "Vinagre de arroz",       5.0),
    # Nigiri Atún x2
    ("Nigiri Atún x2",               "Arroz para sushi",      60.0),
    ("Nigiri Atún x2",               "Atún fresco",           60.0),
    ("Nigiri Atún x2",               "Vinagre de arroz",       5.0),
    # Nigiri Camarón x2
    ("Nigiri Camarón x2",            "Arroz para sushi",      60.0),
    ("Nigiri Camarón x2",            "Camarón",               60.0),
    ("Nigiri Camarón x2",            "Vinagre de arroz",       5.0),
    # Nigiri Langostino x2
    ("Nigiri Langostino x2",         "Arroz para sushi",      60.0),
    ("Nigiri Langostino x2",         "Langostino",            60.0),
    ("Nigiri Langostino x2",         "Vinagre de arroz",       5.0),
    # Roll California
    ("Roll California (8 pzs)",      "Arroz para sushi",     120.0),
    ("Roll California (8 pzs)",      "Alga nori",              1.0),
    ("Roll California (8 pzs)",      "Surimi",                60.0),
    ("Roll California (8 pzs)",      "Palta",                 40.0),
    ("Roll California (8 pzs)",      "Pepino japonés",        40.0),
    ("Roll California (8 pzs)",      "Semillas de sésamo",     5.0),
    ("Roll California (8 pzs)",      "Vinagre de arroz",      10.0),
    # Roll Philadelphia
    ("Roll Philadelphia (8 pzs)",    "Arroz para sushi",     120.0),
    ("Roll Philadelphia (8 pzs)",    "Alga nori",              1.0),
    ("Roll Philadelphia (8 pzs)",    "Salmón fresco",         80.0),
    ("Roll Philadelphia (8 pzs)",    "Queso crema",           60.0),
    ("Roll Philadelphia (8 pzs)",    "Palta",                 40.0),
    ("Roll Philadelphia (8 pzs)",    "Vinagre de arroz",      10.0),
    # Roll Spicy Salmon
    ("Roll Spicy Salmon (8 pzs)",    "Arroz para sushi",     120.0),
    ("Roll Spicy Salmon (8 pzs)",    "Alga nori",              1.0),
    ("Roll Spicy Salmon (8 pzs)",    "Salmón fresco",        100.0),
    ("Roll Spicy Salmon (8 pzs)",    "Palta",                 40.0),
    ("Roll Spicy Salmon (8 pzs)",    "Pepino japonés",        30.0),
    ("Roll Spicy Salmon (8 pzs)",    "Semillas de sésamo",     5.0),
    ("Roll Spicy Salmon (8 pzs)",    "Vinagre de arroz",      10.0),
    # Roll Tempura Camarón
    ("Roll Tempura Camarón (8 pzs)", "Arroz para sushi",     120.0),
    ("Roll Tempura Camarón (8 pzs)", "Alga nori",              1.0),
    ("Roll Tempura Camarón (8 pzs)", "Camarón",               80.0),
    ("Roll Tempura Camarón (8 pzs)", "Palta",                 40.0),
    ("Roll Tempura Camarón (8 pzs)", "Queso crema",           50.0),
    ("Roll Tempura Camarón (8 pzs)", "Semillas de sésamo",     5.0),
    ("Roll Tempura Camarón (8 pzs)", "Vinagre de arroz",      10.0),
    # Roll Dragon
    ("Roll Dragon (8 pzs)",          "Arroz para sushi",     120.0),
    ("Roll Dragon (8 pzs)",          "Alga nori",              1.0),
    ("Roll Dragon (8 pzs)",          "Langostino",            80.0),
    ("Roll Dragon (8 pzs)",          "Palta",                 60.0),
    ("Roll Dragon (8 pzs)",          "Pepino japonés",        30.0),
    ("Roll Dragon (8 pzs)",          "Semillas de sésamo",     8.0),
    ("Roll Dragon (8 pzs)",          "Vinagre de arroz",      10.0),
    # Roll Vegetariano
    ("Roll Vegetariano (8 pzs)",     "Arroz para sushi",     120.0),
    ("Roll Vegetariano (8 pzs)",     "Alga nori",              1.0),
    ("Roll Vegetariano (8 pzs)",     "Palta",                 60.0),
    ("Roll Vegetariano (8 pzs)",     "Pepino japonés",        40.0),
    ("Roll Vegetariano (8 pzs)",     "Queso crema",           60.0),
    ("Roll Vegetariano (8 pzs)",     "Vinagre de arroz",      10.0),
    # Entraña 300g
    ("Entraña 300g",                 "Entraña",                0.3),
    ("Entraña 300g",                 "Sal gruesa",             5.0),
    ("Entraña 300g",                 "Chimichurri",           10.0),
    # Lomo Vetado 300g
    ("Lomo Vetado 300g",             "Lomo vetado",            0.3),
    ("Lomo Vetado 300g",             "Sal gruesa",             5.0),
    ("Lomo Vetado 300g",             "Chimichurri",           10.0),
    # Vacío 300g
    ("Vacío 300g",                   "Vacío",                  0.3),
    ("Vacío 300g",                   "Sal gruesa",             5.0),
    ("Vacío 300g",                   "Chimichurri",           10.0),
    # Costillas de Cerdo 400g
    ("Costillas de Cerdo 400g",      "Costillas de cerdo",     0.4),
    ("Costillas de Cerdo 400g",      "Sal gruesa",             5.0),
    ("Costillas de Cerdo 400g",      "Chimichurri",           15.0),
    # Mix Parrillada Personal
    ("Mix Parrillada Personal",      "Entraña",                0.15),
    ("Mix Parrillada Personal",      "Vacío",                  0.1),
    ("Mix Parrillada Personal",      "Longaniza",              1.0),
    ("Mix Parrillada Personal",      "Chorizo parrillero",     1.0),
    ("Mix Parrillada Personal",      "Sal gruesa",             8.0),
    ("Mix Parrillada Personal",      "Chimichurri",           20.0),
    # Papas Fritas
    ("Papas Fritas",                 "Papa",                   0.2),
    ("Papas Fritas",                 "Mantequilla",           20.0),
    ("Papas Fritas",                 "Sal gruesa",             3.0),
    # Ensalada Mixta
    ("Ensalada Mixta",               "Lechuga",                0.25),
    ("Ensalada Mixta",               "Tomate",                 1.0),
    ("Ensalada Mixta",               "Limón",                  1.0),
    # Bebidas
    ("Agua Mineral 500ml",           "Agua mineral 500ml",     1.0),
    ("Cerveza Artesanal 330ml",      "Cerveza 330ml",          1.0),
    # Entradas
    ("Pan Amasado con Mantequilla",  "Mantequilla",           30.0),
]

USERS = [
    {"email": "admin@restaurante.cl",           "full_name": "Administrador Sistema",  "password": "admin1234"},
    {"email": "gerente.sushi@restaurante.cl",    "full_name": "Gerente Sushi",          "password": "staff1234"},
    {"email": "gerente.parrilla@restaurante.cl", "full_name": "Gerente Parrilladas",    "password": "staff1234"},
    {"email": "garzon.sushi@restaurante.cl",     "full_name": "Garzón Sushi",           "password": "staff1234"},
    {"email": "garzon.parrilla@restaurante.cl",  "full_name": "Garzón Parrilladas",     "password": "staff1234"},
    {"email": "cocina.sushi@restaurante.cl",     "full_name": "Cocina Sushi",           "password": "staff1234"},
    {"email": "cocina.parrilla@restaurante.cl",  "full_name": "Cocina Parrilladas",     "password": "staff1234"},
    {"email": "cajero.sushi@restaurante.cl",     "full_name": "Cajero Sushi",           "password": "staff1234"},
    {"email": "cajero.parrilla@restaurante.cl",  "full_name": "Cajero Parrilladas",     "password": "staff1234"},
]

# (email, nombre_sucursal | None, rol)
ROLES = [
    ("admin@restaurante.cl",           None,                             "admin"),
    ("gerente.sushi@restaurante.cl",   "Sushi Pedro de Valdivia",        "manager"),
    ("gerente.parrilla@restaurante.cl","Parrilladas Pedro de Valdivia",  "manager"),
    ("garzon.sushi@restaurante.cl",    "Sushi Pedro de Valdivia",        "waiter"),
    ("garzon.parrilla@restaurante.cl", "Parrilladas Pedro de Valdivia",  "waiter"),
    ("cocina.sushi@restaurante.cl",    "Sushi Pedro de Valdivia",        "kitchen"),
    ("cocina.parrilla@restaurante.cl", "Parrilladas Pedro de Valdivia",  "kitchen"),
    ("cajero.sushi@restaurante.cl",    "Sushi Pedro de Valdivia",        "cashier"),
    ("cajero.parrilla@restaurante.cl", "Parrilladas Pedro de Valdivia",  "cashier"),
]

# (sucursal, ingrediente, stock_actual, stock_mínimo)
BRANCH_STOCK = [
    # Sushi Pedro de Valdivia
    ("Sushi Pedro de Valdivia", "Arroz para sushi",    5000.0,  500.0),
    ("Sushi Pedro de Valdivia", "Alga nori",            100.0,   10.0),
    ("Sushi Pedro de Valdivia", "Salmón fresco",       3000.0,  300.0),
    ("Sushi Pedro de Valdivia", "Atún fresco",         2000.0,  200.0),
    ("Sushi Pedro de Valdivia", "Palta",               2000.0,  200.0),
    ("Sushi Pedro de Valdivia", "Queso crema",         1500.0,  200.0),
    ("Sushi Pedro de Valdivia", "Pepino japonés",      1500.0,  200.0),
    ("Sushi Pedro de Valdivia", "Camarón",             2000.0,  300.0),
    ("Sushi Pedro de Valdivia", "Langostino",          1500.0,  200.0),
    ("Sushi Pedro de Valdivia", "Surimi",              2000.0,  300.0),
    ("Sushi Pedro de Valdivia", "Vinagre de arroz",    2000.0,  300.0),
    ("Sushi Pedro de Valdivia", "Semillas de sésamo",   500.0,   50.0),
    ("Sushi Pedro de Valdivia", "Agua mineral 500ml",   100.0,   12.0),
    ("Sushi Pedro de Valdivia", "Cerveza 330ml",         60.0,   12.0),
    ("Sushi Pedro de Valdivia", "Limón",                 30.0,    5.0),
    # Parrilladas Pedro de Valdivia
    ("Parrilladas Pedro de Valdivia", "Entraña",             15.0,    2.0),
    ("Parrilladas Pedro de Valdivia", "Lomo vetado",         10.0,    2.0),
    ("Parrilladas Pedro de Valdivia", "Vacío",              12.0,    2.0),
    ("Parrilladas Pedro de Valdivia", "Costillas de cerdo",  10.0,    2.0),
    ("Parrilladas Pedro de Valdivia", "Longaniza",           40.0,    5.0),
    ("Parrilladas Pedro de Valdivia", "Chorizo parrillero",  40.0,    5.0),
    ("Parrilladas Pedro de Valdivia", "Papa",                20.0,    3.0),
    ("Parrilladas Pedro de Valdivia", "Mantequilla",       1000.0,  200.0),
    ("Parrilladas Pedro de Valdivia", "Lechuga",             10.0,    2.0),
    ("Parrilladas Pedro de Valdivia", "Tomate",              20.0,    5.0),
    ("Parrilladas Pedro de Valdivia", "Sal gruesa",        3000.0,  500.0),
    ("Parrilladas Pedro de Valdivia", "Chimichurri",       1000.0,  200.0),
    ("Parrilladas Pedro de Valdivia", "Agua mineral 500ml",  100.0,   12.0),
    ("Parrilladas Pedro de Valdivia", "Cerveza 330ml",        80.0,   12.0),
    ("Parrilladas Pedro de Valdivia", "Limón",                30.0,    5.0),
]

TABLES = [
    ("Sushi Pedro de Valdivia",       12),
    ("Parrilladas Pedro de Valdivia", 15),
]


# ─── Seed ───────────────────────────────────────────────────────────────────

async def seed() -> None:
    async with AsyncSession(engine) as session:

        # ── Categorías ──────────────────────────────────────────────────────
        print("\n=== Categorías ===")
        cats: dict[str, Category] = {}
        for d in CATEGORIES:
            r = await session.exec(select(Category).where(Category.name == d["name"]))
            obj = r.first()
            if not obj:
                obj = Category(**d)
                session.add(obj)
                await session.flush()
                print(f"  [+] {obj.name}")
            else:
                print(f"  [=] {obj.name}")
            cats[obj.name] = obj

        # ── Ingredientes ────────────────────────────────────────────────────
        print("\n=== Ingredientes ===")
        ings: dict[str, Ingredient] = {}
        for d in INGREDIENTS:
            r = await session.exec(select(Ingredient).where(Ingredient.name == d["name"]))
            obj = r.first()
            if not obj:
                obj = Ingredient(**d)
                session.add(obj)
                await session.flush()
                print(f"  [+] {obj.name} ({obj.unit})")
            else:
                print(f"  [=] {obj.name}")
            ings[obj.name] = obj

        # ── Sucursales ──────────────────────────────────────────────────────
        print("\n=== Sucursales ===")
        branches: dict[str, Branch] = {}
        for d in BRANCHES:
            r = await session.exec(select(Branch).where(Branch.name == d["name"]))
            obj = r.first()
            if not obj:
                obj = Branch(**d)
                session.add(obj)
                await session.flush()
                print(f"  [+] {obj.name}  ({obj.address})")
            else:
                print(f"  [=] {obj.name}")
            branches[obj.name] = obj

        # ── Productos ───────────────────────────────────────────────────────
        print("\n=== Productos ===")
        prods: dict[str, Product] = {}
        for d in PRODUCTS:
            r = await session.exec(select(Product).where(Product.name == d["name"]))
            obj = r.first()
            if not obj:
                obj = Product(
                    name=d["name"],
                    description=d["description"],
                    price=d["price"],
                    category_id=cats[d["category"]].id,
                )
                session.add(obj)
                await session.flush()
                print(f"  [+] {obj.name}  (${obj.price:,.0f})")
            else:
                print(f"  [=] {obj.name}")
            prods[obj.name] = obj

        # ── Recetas ─────────────────────────────────────────────────────────
        print("\n=== Recetas ===")
        recipe_new = 0
        for (prod_name, ing_name, qty) in RECIPES:
            prod = prods[prod_name]
            ing  = ings[ing_name]
            r = await session.exec(
                select(Recipe).where(
                    Recipe.product_id    == prod.id,
                    Recipe.ingredient_id == ing.id,
                )
            )
            if not r.first():
                session.add(Recipe(product_id=prod.id, ingredient_id=ing.id, quantity=qty))
                recipe_new += 1
        await session.flush()
        if recipe_new:
            print(f"  [+] {recipe_new} líneas de receta creadas")
        else:
            print("  [=] Recetas ya existen")

        # ── Usuarios ────────────────────────────────────────────────────────
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

        # ── Membresías / Roles ──────────────────────────────────────────────
        print("\n=== Membresías ===")
        for (email, branch_name, role) in ROLES:
            user      = users[email]
            branch_id = branches[branch_name].id if branch_name else None
            r = await session.exec(
                select(UserBranchRole).where(
                    UserBranchRole.user_id   == user.id,
                    UserBranchRole.branch_id == branch_id,
                    UserBranchRole.role      == role,
                )
            )
            if not r.first():
                session.add(UserBranchRole(user_id=user.id, branch_id=branch_id, role=role))
                print(f"  [+] {email}  →  {role} @ {branch_name or 'global'}")
            else:
                print(f"  [=] {email}  ({role})")
        await session.flush()

        # ── Mesas ───────────────────────────────────────────────────────────
        print("\n=== Mesas ===")
        for (branch_name, count) in TABLES:
            branch  = branches[branch_name]
            new_cnt = 0
            for i in range(1, count + 1):
                number = f"Mesa {i}"
                r = await session.exec(
                    select(Table).where(
                        Table.branch_id == branch.id,
                        Table.number    == number,
                    )
                )
                if not r.first():
                    session.add(Table(branch_id=branch.id, number=number))
                    new_cnt += 1
            await session.flush()
            if new_cnt:
                print(f"  [+] {new_cnt} mesas creadas  →  {branch_name}")
            else:
                print(f"  [=] Mesas ya existen         →  {branch_name}")

        # ── Stock inicial ───────────────────────────────────────────────────
        print("\n=== Stock inicial ===")
        stock_new = 0
        for (branch_name, ing_name, qty, min_stock) in BRANCH_STOCK:
            branch = branches[branch_name]
            ing    = ings[ing_name]
            r = await session.exec(
                select(BranchStock).where(
                    BranchStock.branch_id     == branch.id,
                    BranchStock.ingredient_id == ing.id,
                )
            )
            if not r.first():
                session.add(BranchStock(
                    branch_id=branch.id,
                    ingredient_id=ing.id,
                    quantity=qty,
                    min_stock=min_stock,
                ))
                stock_new += 1
        await session.flush()
        if stock_new:
            print(f"  [+] {stock_new} registros de stock creados")
        else:
            print("  [=] Stock ya existe")

        await session.commit()

    # ── Resumen ─────────────────────────────────────────────────────────────
    print()
    print("─" * 60)
    print("Seed completado exitosamente.")
    print()
    print("Credenciales:")
    print("  Admin:    admin@restaurante.cl        /  admin1234")
    print("  Personal: <rol>.<sucursal>@restaurante.cl  /  staff1234")
    print()
    print("Sucursales creadas:")
    for b in BRANCHES:
        print(f"  • {b['name']}  —  {b['address']}")
    print()
    print("Login:  POST /api/v1/auth/login")
    print("  Content-Type: application/x-www-form-urlencoded")
    print("  username=admin@restaurante.cl&password=admin1234")
    print()


if __name__ == "__main__":
    asyncio.run(seed())
