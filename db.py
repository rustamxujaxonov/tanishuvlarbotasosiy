from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import select, update, and_, or_

from config import DATABASE_URL
from database.models import Base, User, ChatSession, PremiumRequest, GenderEnum

# ─── Engine va Session ────────────────────────────────────────
engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def init_db():
    """Jadvallarni yaratish (agar mavjud bo'lmasa)"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncSession:
    """Context manager sifatida ishlatish uchun"""
    async with AsyncSessionLocal() as session:
        yield session


# ═══════════════════════════════════════════════════════════════
#  USER CRUD
# ═══════════════════════════════════════════════════════════════

async def get_user(user_id: int) -> Optional[User]:
    async with AsyncSessionLocal() as s:
        return await s.get(User, user_id)


async def create_user(user_id: int, full_name: str, username: str = None) -> User:
    async with AsyncSessionLocal() as s:
        user = User(id=user_id, full_name=full_name, username=username)
        s.add(user)
        await s.commit()
        await s.refresh(user)
        return user


async def get_or_create_user(user_id: int, full_name: str, username: str = None) -> tuple[User, bool]:
    """(user, created) qaytaradi"""
    async with AsyncSessionLocal() as s:
        user = await s.get(User, user_id)
        if user:
            return user, False
        user = User(id=user_id, full_name=full_name, username=username)
        s.add(user)
        await s.commit()
        await s.refresh(user)
        return user, True


async def update_user(user_id: int, **kwargs) -> None:
    kwargs["last_active"] = datetime.utcnow()
    async with AsyncSessionLocal() as s:
        await s.execute(update(User).where(User.id == user_id).values(**kwargs))
        await s.commit()


async def is_premium_active(user_id: int) -> bool:
    user = await get_user(user_id)
    if not user or not user.is_premium:
        return False
    if user.premium_until and user.premium_until < datetime.utcnow():
        # Muddati o'tgan — o'chiramiz
        await update_user(user_id, is_premium=False, premium_until=None)
        return False
    return True


async def grant_premium(user_id: int, days: int) -> datetime:
    """Foydalanuvchiga premium beradi, tugash sanasini qaytaradi"""
    user = await get_user(user_id)
    # Agar allaqachon premium bo'lsa, ustiga qo'shamiz
    base = max(datetime.utcnow(), user.premium_until or datetime.utcnow())
    until = base + timedelta(days=days)
    await update_user(user_id, is_premium=True, premium_until=until)
    return until


# ═══════════════════════════════════════════════════════════════
#  SEARCH / MATCHING
# ═══════════════════════════════════════════════════════════════

async def find_partner(
    user_id: int,
    gender_filter: Optional[GenderEnum] = None
) -> Optional[User]:
    """
    Qidiruv holatidagi random foydalanuvchini topadi.
    gender_filter berilsa, faqat shu jinsdagilarni qidiradi (premium).
    """
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


async def connect_users(user1_id: int, user2_id: int) -> ChatSession:
    """Ikki foydalanuvchini ulaydi va sessiya yaratadi"""
    async with AsyncSessionLocal() as s:
        # Ikkalasini ham yangilaymiz
        await s.execute(
            update(User)
            .where(User.id.in_([user1_id, user2_id]))
            .values(is_searching=False, current_partner_id=None)
        )
        await s.execute(
            update(User).where(User.id == user1_id).values(current_partner_id=user2_id)
        )
        await s.execute(
            update(User).where(User.id == user2_id).values(current_partner_id=user1_id)
        )
        session = ChatSession(user1_id=user1_id, user2_id=user2_id)
        s.add(session)
        await s.commit()
        await s.refresh(session)
        return session


async def disconnect_users(user_id: int) -> Optional[int]:
    """Foydalanuvchini chatdan chiqaradi, partner ID ni qaytaradi"""
    user = await get_user(user_id)
    if not user or not user.current_partner_id:
        return None
    partner_id = user.current_partner_id

    async with AsyncSessionLocal() as s:
        # Sessiyani yakunlaymiz
        await s.execute(
            update(ChatSession)
            .where(
                and_(
                    ChatSession.is_active == True,
                    or_(
                        ChatSession.user1_id == user_id,
                        ChatSession.user2_id == user_id,
                    )
                )
            )
            .values(is_active=False, ended_at=datetime.utcnow())
        )
        # Ikkalasini ham tozalaymiz
        await s.execute(
            update(User)
            .where(User.id.in_([user_id, partner_id]))
            .values(current_partner_id=None, is_searching=False)
        )
        await s.commit()
    return partner_id


# ═══════════════════════════════════════════════════════════════
#  PREMIUM REQUESTS
# ═══════════════════════════════════════════════════════════════

async def create_premium_request(
    user_id: int, plan_key: str, photo_file_id: str
) -> PremiumRequest:
    async with AsyncSessionLocal() as s:
        req = PremiumRequest(user_id=user_id, plan_key=plan_key, photo_file_id=photo_file_id)
        s.add(req)
        await s.commit()
        await s.refresh(req)
        return req


async def get_premium_request(request_id: int) -> Optional[PremiumRequest]:
    async with AsyncSessionLocal() as s:
        return await s.get(PremiumRequest, request_id)


async def update_premium_request(request_id: int, **kwargs) -> None:
    async with AsyncSessionLocal() as s:
        await s.execute(
            update(PremiumRequest)
            .where(PremiumRequest.id == request_id)
            .values(**kwargs)
        )
        await s.commit()
