# backend/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.database import engine, Base
from backend.routers import auth, users, games, coins, lobbies
from backend.websockets import game_ws
from backend.tasks import background_tasks
import logging
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="TBoard Backend", version="0.1.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://tboard.space",
        "http://localhost:5173",
        "http://localhost:3000"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
)

# HTTP Роутеры
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(games.router, prefix="/api/games", tags=["Games"])
app.include_router(coins.router, prefix="/api/coins", tags=["Coins"])
app.include_router(lobbies.router, prefix="/api/lobbies", tags=["Lobbies"])

# WebSocket
app.include_router(game_ws.router, tags=["WebSocket"])


@app.on_event("startup")
async def startup():
    """Инициализация при запуске"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created/verified")
    
    # Запускаем фоновые задачи
    background_tasks.start()
    logger.info("Background tasks started")
    logger.info("Application started successfully")


@app.on_event("shutdown")
async def shutdown():
    """Очистка при остановке"""
    background_tasks.stop()
    logger.info("Application shutdown complete")


@app.get("/")
def read_root():
    return {
        "message": "TBoard Backend is running!",
        "version": "0.1.0",
        "status": "healthy"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "tboard-backend",
        "version": "0.1.0"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)