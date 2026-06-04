from datetime import datetime

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from config import ADMIN_IDS, PREMIUM_PRICES
from database.db import (
    get_user, get_premium_request,
    update_premium_request, grant_premium, update_user
)
from keyboards.buttons import main_menu

router = Router()


# ─── Admin filteri ────────────────────────────────────────────
def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


# ═══════════════════════════════════════════════════════════════
#  ADMIN PANEL KOMANDALAR
# ═══════════════════════════════════════════════════════════════

@router.message(Command("admin"))
async def admin_panel(message: Message):
    if not is_admin(message.from_user.id):
        return

    await message.answer(
        "🔐 <b>Admin Panel</b>\n\n"
        "Buyruqlar:\n"
        "/stats — Statistika\n"
        "/ban [user_id] — Foydalanuvchini ban qilish\n"
        "/unban [user_id] — Banni olib tashlash\n"
        "/give_premium [user_id] [reja] — Premium berish\n"
        "  Rejalar: 1_day | 3_days | 1_week | 1_month\n\n"
        "Chekni tasdiqlash: Guruhda kelgan so'rov ostidagi tugmalardan foydalaning.",
        parse_mode="HTML",
    )


@router.message(Command("stats"))
async def admin_stats(message: Message):
    if not is_admin(message.from_user.id):
        return

    from sqlalchemy import select, func
    from database.db import AsyncSessionLocal
    from database.models import User

    async with AsyncSessionLocal() as s:
        total = (await s.execute(select(func.count(User.id)))).scalar()
        premium = (await s.execute(
            select(func.count(User.id)).where(User.is_premium == True)
        )).scalar()
        searching = (await s.execute(
            select(func.count(User.id)).where(User.is_searching == True)
        )).scalar()
        in_chat = (await s.execute(
            select(func.count(User.id)).where(User.current_partner_id != None)
        )).scalar()

    await message.answer(
        f"📊 <b>Statistika</b>\n\n"
        f"👥 Jami foydalanuvchilar: <b>{total}</b>\n"
        f"⭐ Premium: <b>{premium}</b>\n"
        f"🔍 Qidiruvda: <b>{searching}</b>\n"
        f"💬 Chatda: <b>{in_chat}</b>",
        parse_mode="HTML",
    )


@router.message(Command("ban"))
async def admin_ban(message: Message):
    if not is_admin(message.from_user.id):
        return

    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Foydalanish: /ban [user_id]")
        return

    try:
        target_id = int(parts[1])
    except ValueError:
        await message.answer("❌ Noto'g'ri ID formati.")
        return

    user = await get_user(target_id)
    if not user:
        await message.answer("❌ Foydalanuvchi topilmadi.")
        return

    await update_user(target_id, is_banned=True)
    await message.answer(f"🚫 Foydalanuvchi {target_id} ban qilindi.")

    try:
        await message.bot.send_message(target_id, "🚫 Siz botdan chiqarib yuborldingiz.")
    except Exception:
        pass


@router.message(Command("unban"))
async def admin_unban(message: Message):
    if not is_admin(message.from_user.id):
        return

    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Foydalanish: /unban [user_id]")
        return

    try:
        target_id = int(parts[1])
    except ValueError:
        await message.answer("❌ Noto'g'ri ID formati.")
        return

    await update_user(target_id, is_banned=False)
    await message.answer(f"✅ Foydalanuvchi {target_id} unbanned.")


@router.message(Command("give_premium"))
async def admin_give_premium(message: Message):
    """Qo'lda premium berish: /give_premium 123456789 1_month"""
    if not is_admin(message.from_user.id):
        return

    parts = message.text.split()
    if len(parts) < 3:
        await message.answer("Foydalanish: /give_premium [user_id] [reja]")
        return

    try:
        target_id = int(parts[1])
    except ValueError:
        await message.answer("❌ Noto'g'ri ID.")
        return

    plan_key = parts[2]
    if plan_key not in PREMIUM_PRICES:
        plans = " | ".join(PREMIUM_PRICES.keys())
        await message.answer(f"❌ Noto'g'ri reja. Mavjudlar: {plans}")
        return

    user = await get_user(target_id)
    if not user:
        await message.answer("❌ Foydalanuvchi topilmadi.")
        return

    plan = PREMIUM_PRICES[plan_key]
    until = await grant_premium(target_id, plan["days"])

    await message.answer(
        f"✅ {target_id} ga <b>{plan['label']}</b> berildi.\n"
        f"⏳ Tugash: {until.strftime('%d.%m.%Y %H:%M')}",
        parse_mode="HTML",
    )

    try:
        await message.bot.send_message(
            target_id,
            f"🎉 <b>Sizga Premium faollashtirildi!</b>\n\n"
            f"📦 Reja: {plan['label']}\n"
            f"⏳ Tugash sanasi: {until.strftime('%d.%m.%Y %H:%M')}",
            parse_mode="HTML",
        )
    except Exception:
        pass


# ═══════════════════════════════════════════════════════════════
#  PREMIUM SO'ROVLARINI TASDIQLASH (Guruhdan callback)
# ═══════════════════════════════════════════════════════════════

@router.callback_query(F.data.startswith("admin_approve:"))
async def approve_premium(callback: CallbackQuery):
    """
    Format: admin_approve:{request_id}:{user_id}:{plan_key}
    """
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Siz admin emassiz!", show_alert=True)
        return

    parts = callback.data.split(":")
    request_id = int(parts[1])
    user_id    = int(parts[2])
    plan_key   = parts[3]

    req = await get_premium_request(request_id)
    if not req:
        await callback.answer("❌ So'rov topilmadi.", show_alert=True)
        return

    if req.status != "pending":
        await callback.answer("⚠️ Bu so'rov allaqachon ko'rib chiqilgan!", show_alert=True)
        return

    plan = PREMIUM_PRICES.get(plan_key)
    if not plan:
        await callback.answer("❌ Noto'g'ri reja.", show_alert=True)
        return

    # Premiumni beramiz
    until = await grant_premium(user_id, plan["days"])

    # So'rovni yangilaymiz
    await update_premium_request(
        request_id,
        status="approved",
        admin_id=callback.from_user.id,
        reviewed_at=datetime.utcnow(),
        plan_key=plan_key,
    )

    # Admin xabarini yangilaymiz
    await callback.message.edit_caption(
        caption=callback.message.caption + f"\n\n✅ <b>TASDIQLANDI</b> — Admin: {callback.from_user.full_name}\n"
                                           f"📦 Reja: {plan['label']}\n"
                                           f"⏳ Tugash: {until.strftime('%d.%m.%Y %H:%M')}",
        parse_mode="HTML",
    )

    # Foydalanuvchiga xabar
    try:
        await callback.bot.send_message(
            user_id,
            f"🎉 <b>Premium faollashtirildi!</b>\n\n"
            f"📦 Reja: <b>{plan['label']}</b>\n"
            f"⏳ Tugash sanasi: <b>{until.strftime('%d.%m.%Y %H:%M')}</b>\n\n"
            "Endi barcha premium imkoniyatlardan foydalanishingiz mumkin! ⭐",
            parse_mode="HTML",
        )
    except Exception:
        pass

    await callback.answer("✅ Premium berildi!", show_alert=True)


@router.callback_query(F.data.startswith("admin_reject:"))
async def reject_premium(callback: CallbackQuery):
    """
    Format: admin_reject:{request_id}:{user_id}
    """
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Siz admin emassiz!", show_alert=True)
        return

    parts = callback.data.split(":")
    request_id = int(parts[1])
    user_id    = int(parts[2])

    req = await get_premium_request(request_id)
    if not req:
        await callback.answer("❌ So'rov topilmadi.", show_alert=True)
        return

    if req.status != "pending":
        await callback.answer("⚠️ Bu so'rov allaqachon ko'rib chiqilgan!", show_alert=True)
        return

    await update_premium_request(
        request_id,
        status="rejected",
        admin_id=callback.from_user.id,
        reviewed_at=datetime.utcnow(),
    )

    await callback.message.edit_caption(
        caption=callback.message.caption + f"\n\n❌ <b>RAD ETILDI</b> — Admin: {callback.from_user.full_name}",
        parse_mode="HTML",
    )

    try:
        await callback.bot.send_message(
            user_id,
            "❌ <b>To'lovingiz tasdiqlanmadi.</b>\n\n"
            "Sabab: Chek rasmida muammo bor yoki to'lov aniqlanmadi.\n\n"
            "Qaytadan to'lov qilib, to'g'ri chek rasmini yuboring yoki admin bilan bog'laning.",
            parse_mode="HTML",
        )
    except Exception:
        pass

    await callback.answer("❌ Rad etildi.", show_alert=True)
