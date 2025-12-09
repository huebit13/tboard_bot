from pydantic import BaseModel
from typing import Optional

class UserCreate(BaseModel):
    telegram_id: int
    username: Optional[str] = None

class WalletConnect(BaseModel):
    telegram_id: int
    ton_wallet_address: str
    balance_ton: float
