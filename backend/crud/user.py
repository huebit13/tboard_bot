# /opt/tboard_backend/backend/crud/user.py

import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime
from backend.database.models import User

# Создайте logger для этого модуля
logger = logging.getLogger(__name__)

async def get_user_by_telegram_id(db: AsyncSession, telegram_id: int):
    result = await db.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    return result.scalar_one_or_none()


async def create_or_update_user(db: AsyncSession, telegram_id: int, username: str | None):
    logger.info(f"CRUD: Attempting to get or create user with telegram_id={telegram_id}")
    try: # <-- Добавлен блок try
        user = await get_user_by_telegram_id(db, telegram_id)

        if user:
            logger.info(f"CRUD: User found, updating: {telegram_id}")
            if username and user.username != username:
                user.username = username
            user.last_active_at = datetime.utcnow()
        else:
            logger.info(f"CRUD: User not found, creating: {telegram_id}")
            user = User(
                telegram_id=telegram_id,
                username=username,
                referral_link=f"ref_{telegram_id}",
                created_at=datetime.utcnow(),
                last_active_at=datetime.utcnow()
            )
            db.add(user)

        logger.info(f"CRUD: Committing transaction for user: {telegram_id}")
        await db.commit()
        logger.info(f"CRUD: Transaction committed for user: {telegram_id}")

        await db.refresh(user)
        logger.info(f"CRUD: User refreshed from DB: id={user.id}, telegram_id={user.telegram_id}")
        return user
    except Exception as e:
        logger.error(f"CRUD: Error in create_or_update_user: {e}", exc_info=True)
        await db.rollback()
        raise # Перебросьте исключение наверх


async def connect_wallet(db: AsyncSession, telegram_id: int, wallet_address: str, balance: float):
    logger.info(f"CRUD: Attempting to connect wallet for telegram_id={telegram_id}")
    user = await get_user_by_telegram_id(db, telegram_id)
    if not user:
        logger.warning(f"CRUD: User not found for wallet connection: {telegram_id}")
        return None

    user.ton_wallet_address = wallet_address
    user.wallet_connected_at = datetime.utcnow()
    user.balance_ton = balance

    await db.commit()
    await db.refresh(user)
    logger.info(f"CRUD: Wallet connected for user: id={user.id}, telegram_id={user.telegram_id}")
    return user
