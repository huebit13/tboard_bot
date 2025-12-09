from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime
from app.models import User


async def get_user_by_telegram_id(db: AsyncSession, telegram_id: int):
    result = await db.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    return result.scalar_one_or_none()


async def create_or_update_user(db: AsyncSession, telegram_id: int, username: str | None):
    user = await get_user_by_telegram_id(db, telegram_id)

    if user:
        if username and user.username != username:
            user.username = username
        user.last_active_at = datetime.utcnow()
    else:
        user = User(
            telegram_id=telegram_id,
            username=username,
            referral_link=f"ref_{telegram_id}",  
            created_at=datetime.utcnow(),
            last_active_at=datetime.utcnow()
        )
        db.add(user)

    await db.commit()
    await db.refresh(user)
    return user


async def connect_wallet(db: AsyncSession, telegram_id: int, wallet_address: str, balance: float):
    user = await get_user_by_telegram_id(db, telegram_id)
    if not user:
        return None

    user.ton_wallet_address = wallet_address
    user.wallet_connected_at = datetime.utcnow()
    user.balance_ton = balance

    await db.commit()
    await db.refresh(user)
    return user
