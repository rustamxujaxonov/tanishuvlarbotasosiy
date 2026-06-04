from datetime import datetime
from sqlalchemy import (
    BigInteger, String, Integer, Boolean,
    DateTime, Text, ForeignKey, Enum
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
import enum


class Base(DeclarativeBase):
    pass


class GenderEnum(str, enum.Enum):
    male   = "male"
    female = "female"


class User(Base):
    """Foydalanuvchilar jadvali"""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)  # Telegram user_id
    username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    full_name: Mapped[str] = mapped_column(String(128))            # Telegram ismi
    custom_name: Mapped[str | None] = mapped_column(String(64))    # O'zi kiritgan ism
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    region: Mapped[str | None] = mapped_column(String(64), nullable=True)
    gender: Mapped[GenderEnum | None] = mapped_column(
        Enum(GenderEnum), nullable=True
    )

    # Holat
    is_registered: Mapped[bool] = mapped_column(Boolean, default=False)
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False)
    is_searching: Mapped[bool] = mapped_column(Boolean, default=False)

    # Premium
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False)
    premium_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Chat holati
    current_partner_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=True
    )

    # Vaqt
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_active: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Onboarding qadami (1-4)
    onboarding_step: Mapped[int] = mapped_column(Integer, default=0)


class ChatSession(Base):
    """Chat sessiyalari - kim kim bilan gaplashgan"""
    __tablename__ = "chat_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user1_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    user2_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class PremiumRequest(Base):
    """Premium to'lov so'rovlari (chek rasmlar)"""
    __tablename__ = "premium_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    plan_key: Mapped[str] = mapped_column(String(20))  # "1_day", "3_days" va h.k.
    photo_file_id: Mapped[str] = mapped_column(String(256))  # Telegram file_id
    status: Mapped[str] = mapped_column(String(20), default="pending")
    # pending | approved | rejected
    admin_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Adminlar guruhidagi xabar ID (callback uchun)
    admin_message_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
