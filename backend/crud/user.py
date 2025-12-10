from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime
from backend.database.models import User


async def get_user_by_telegram_id(db: AsyncSession, telegram_id: int):
    result = await db.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    return result.scalar_one_or_none()


async def create_or_update_user(db: AsyncSession, telegram_id: int, username: str | None):
    logger.info(f"CRUD: Attempting to get or create user with telegram_id={telegram_id}") # Добавьте лог
    try:
        user = await get_user_by_telegram_id(db, telegram_id)

        if user:
            logger.info(f"CRUD: User found, updating: {telegram_id}") # Добавьте лог
            if username and user.username != username:
                user.username = username
            user.last_active_at = datetime.utcnow()
        else:
            logger.info(f"CRUD: User not found, creating: {telegram_id}") # Добавьте лог
            user = User(
                telegram_id=telegram_id,
                username=username,
                referral_link=f"ref_{telegram_id}",  
                created_at=datetime.utcnow(),
                last_active_at=datetime.utcnow()
            )
            db.add(user)

        logger.info(f"CRUD: Committing transaction for user: {telegram_id}") # Добавьте лог
        await db.commit()
        logger.info(f"CRUD: Transaction committed for user: {telegram_id}") # Добавьте лог
        
        await db.refresh(user) # Обновляем объект, чтобы получить ID и т.д.
        logger.info(f"CRUD: User refreshed from DB: id={user.id}, telegram_id={user.telegram_id}") # Добавьте лог
        return user
    except Exception as e:
        logger.error(f"CRUD: Error in create_or_update_user: {e}", exc_info=True) # Добавьте лог
        await db.rollback() # Обязательно откатите при ошибке
        raise # Перебросьте исключение наверх


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
