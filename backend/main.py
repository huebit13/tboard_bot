

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from backend.database import engine, get_db, Base, AsyncSession 
from backend.schemas.user import UserCreate, WalletConnect
from backend.crud.user import create_or_update_user, connect_wallet
from backend.routers import users
import hashlib
import hmac
import os
from datetime import datetime, timedelta
import json


app = FastAPI(title="TBoard Backend", version="0.1.0")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # TODO: Заменить на адрес фронтенда в продакшене
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required")

def validate_telegram_init_data(init_data: str) -> dict:
    try:

        pairs = init_data.split("&")
        params = {}
        hash_from_data = None
        for pair in pairs:
            key, value = pair.split("=", 1)
            if key == "hash":
                hash_from_data = value
            else:

                import urllib.parse
                params[key] = urllib.parse.unquote(value)


        if not hash_from_data:
            raise ValueError("Hash not found in initData")


        sorted_params = sorted(params.items())
        data_check_string = "\n".join(f"{k}={v}" for k, v in sorted_params)


        secret_key = hmac.new(b"WebAppData", TELEGRAM_BOT_TOKEN.encode(), hashlib.sha256).digest()


        calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()


        if calculated_hash != hash_from_data: 
            raise ValueError("Invalid hash in initData")


        if 'auth_date' in params:
            auth_date = int(params['auth_date'])

            if datetime.now().timestamp() - auth_date > 24 * 60 * 60:
                 raise ValueError("Auth date is too old")

        user_data = json.loads(params['user']) if 'user' in params else {}
        return user_data

    except (ValueError, KeyError) as e:
        print(f"Error validating Telegram init data: {e}")
        raise HTTPException(status_code=400, detail="Invalid Telegram init data")


from fastapi import Request

@app.post("/api/auth/login")
async def login(request: Request, db: AsyncSession = Depends(get_db)): 
    try:

        body = await request.json()
        init_data = body.get("initData")

        if not init_data: 
            raise HTTPException(status_code=400, detail="Init data is required")

        user_info = validate_telegram_init_data(init_data)


        telegram_id = user_info.get("id")
        username = user_info.get("username")

        if not telegram_id:
            raise HTTPException(status_code=400, detail="Telegram ID not found in init data")


        user = await create_or_update_user(
            db=db,
            telegram_id=telegram_id,
            username=username
        )


        return {
            "status": "ok",
            "message": "User authenticated and initialized",
            "user": {
                "telegram_id": user.telegram_id,
                "username": user.username,
                "balance_ton": float(user.balance_ton) if user.balance_ton else 0.0
            }
        }

    except HTTPException:

        raise
    except Exception as e:

        print(f"Unexpected error during login: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during login")


app.include_router(users.router, prefix="/api", tags=["users"])


@app.on_event("startup")
async def startup():

    async with engine.begin() as conn: 

        await conn.run_sync(Base.metadata.create_all)

@app.get("/")
def read_root():
    return {"message": "TBoard Backend is running!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
