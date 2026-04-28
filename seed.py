"""
Seed script — creates the initial Branch, admin user and membership.

Usage:
    python seed.py

Override defaults via env vars:
    SEED_BRANCH_NAME     (default: "Casa Matriz")
    SEED_BRANCH_ADDRESS  (default: "Sin dirección")
    SEED_ADMIN_EMAIL     (default: "admin@restaurante.cl")
    SEED_ADMIN_NAME      (default: "Administrador")
    SEED_ADMIN_PASSWORD  (default: "admin1234")
"""
import asyncio
import os

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.security import get_password_hash
from app.db.session import engine
from app.models.base import Branch, User, UserBranchRole

BRANCH_NAME    = os.getenv("SEED_BRANCH_NAME",     "Casa Matriz")
BRANCH_ADDRESS = os.getenv("SEED_BRANCH_ADDRESS",  "Sin dirección")
ADMIN_EMAIL    = os.getenv("SEED_ADMIN_EMAIL",      "admin@restaurante.cl")
ADMIN_NAME     = os.getenv("SEED_ADMIN_NAME",       "Administrador")
ADMIN_PASSWORD = os.getenv("SEED_ADMIN_PASSWORD",   "admin1234")


async def seed() -> None:
    async with AsyncSession(engine) as session:

        # --- Branch ---
        result = await session.exec(select(Branch).where(Branch.name == BRANCH_NAME))
        branch = result.first()
        if not branch:
            branch = Branch(name=BRANCH_NAME, address=BRANCH_ADDRESS)
            session.add(branch)
            await session.flush()
            print(f"[+] Branch creada:      '{branch.name}' (id={branch.id})")
        else:
            print(f"[=] Branch ya existe:   '{branch.name}' (id={branch.id})")

        # --- Admin user ---
        result = await session.exec(select(User).where(User.email == ADMIN_EMAIL))
        user = result.first()
        if not user:
            user = User(
                email=ADMIN_EMAIL,
                full_name=ADMIN_NAME,
                hashed_password=get_password_hash(ADMIN_PASSWORD),
            )
            session.add(user)
            await session.flush()
            print(f"[+] Usuario creado:")
            print(f"    email:    {ADMIN_EMAIL}")
            print(f"    password: {ADMIN_PASSWORD}")
        else:
            print(f"[=] Usuario ya existe:  '{user.email}' (id={user.id})")

        # --- Admin membership (global — branch_id=None) ---
        result = await session.exec(
            select(UserBranchRole).where(
                UserBranchRole.user_id == user.id,
                UserBranchRole.role == "admin",
                UserBranchRole.branch_id == None,
            )
        )
        if not result.first():
            session.add(UserBranchRole(user_id=user.id, branch_id=None, role="admin"))
            print(f"[+] Membresía admin global creada")
        else:
            print(f"[=] Membresía admin global ya existe")

        await session.commit()

    print()
    print("Seed completado. Credenciales de acceso:")
    print(f"  email:    {ADMIN_EMAIL}")
    print(f"  password: {ADMIN_PASSWORD}")
    print()
    print("Login: POST /api/v1/auth/login")
    print("  Content-Type: application/x-www-form-urlencoded")
    print(f"  username={ADMIN_EMAIL}&password={ADMIN_PASSWORD}")


if __name__ == "__main__":
    asyncio.run(seed())
