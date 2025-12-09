from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from backend.schemas.user import UserCreate, WalletConnect
from backend.crud.user import create_or_update_user, connect_wallet
from backend.database import get_db

router = APIRouter()


@router.post("/init")
async def init_user(data: UserCreate, db: AsyncSession = Depends(get_db)):
    user = await create_or_update_user(
        db=db,
        telegram_id=data.telegram_id,
        username=data.username
    )
    return {"status": "ok", "user": user}


@router.post("/wallet/connect")
async def wallet_connect(data: WalletConnect, db: AsyncSession = Depends(get_db)):
    user = await connect_wallet(
        db=db,
        telegram_id=data.telegram_id,
        wallet_address=data.ton_wallet_address,
        balance=data.balance_ton,
    )
    return {"status": "ok", "user": user}
