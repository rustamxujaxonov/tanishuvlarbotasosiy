from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select, update, and_, func

from config import DATABASE_URL
from .models import Base, User, GenderEnum

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# ================== USER ==================
async def get_user(user_id: int) -> Optional[User]:
    async with AsyncSessionLocal() as s:
        return await s.get(User, user_id)


async def get_or_create_user(user_id: int, full_name: str, username: str = None):
    async with AsyncSessionLocal() as s:
        user = await s.get(User, user_id)
        if user:
            return user, False
        user = User(id=user_id, full_name=full_name, username=username)
        s.add(user)
        await s.commit()
        await s.refresh(user)
        return user, True


async def update_user(user_id: int, **kwargs):
    kwargs["last_active"] = datetime.utcnow()
    async with AsyncSessionLocal() as s:
        await s.execute(update(User).where(User.id == user_id).values(**kwargs))
        await s.commit()


async def is_premium_active(user_id: int) -> bool:
    user = await get_user(user_id)
    if not user or not user.is_premium:
        return False
    if user.premium_until and user.premium_until < datetime.utcnow():
        await update_user(user_id, is_premium=False, premium_until=None)
        return False
    return True


async def grant_premium(user_id: int, days: int):
    base = datetime.utcnow()
    user = await get_user(user_id)
    if user and user.premium_until:
        base = max(base, user.premium_until)
    until = base + timedelta(days=days)
    await update_user(user_id, is_premium=True, premium_until=until)
    return until


# ================== QIDIRUV ==================
async def find_partner(user_id: int, gender_filter: GenderEnum = None):
    async with AsyncSessionLocal() as s:
        conditions = [
            User.is_searching == True,
            User.id != user_id,
            User.is_banned == False,
            User.is_registered == True,
            User.current_partner_id == None,
        ]
        if gender_filter:
            conditions.append(User.gender == gender_filter)

        result = await s.execute(
            select(User)
            .where(and_(*conditions))
            .order_by(User.last_active.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()


async def connect_users(user1_id: int, user2_id: int):
    async with AsyncSessionLocal() as s:
        await s.execute(
            update(User)
            .where(User.id.in_([user1_id, user2_id]))
            .values(is_searching=False, current_partner_id=None)
        )
        await s.execute(update(User).where(User.id == user1_id).values(current_partner_id=user2_id))
        await s.execute(update(User).where(User.id == user2_id).values(current_partner_id=user1_id))
        await s.commit()


async def disconnect_users(user_id: int):
    user = await get_user(user_id)
    if not user or not user.current_partner_id:
        return None
    partner_id = user.current_partner_id

    async with AsyncSessionLocal() as s:
        await s.execute(
            update(User)
            .where(User.id.in_([user_id, partner_id]))
            .values(current_partner_id=None, is_searching=False)
        )
        await s.commit()
    return partner_id
