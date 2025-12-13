# backend/websockets/game_ws.py

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from backend.websockets.handlers import GameWebSocketHandler
from backend.utils.jwt import verify_token
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.websocket("/ws/game")
async def websocket_game_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint для игровых взаимодействий.
    Требует токен в query параметрах: /ws/game?token=<JWT_TOKEN>
    """
    handler = GameWebSocketHandler(websocket)
    
    try:
        logger.info(f"WebSocket connection attempt from {websocket.client}")
        
        # Аутентификация
        token = websocket.query_params.get("token")
        if not token:
            logger.warning("WebSocket connection attempt without token")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Token required")
            return

        user_data = verify_token(token)
        if not user_data:
            logger.warning(f"WebSocket connection attempt with invalid token")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token")
            return

        user_id = user_data["user_id"]
        logger.info(f"WebSocket authenticated for user {user_id}")

        # Подключаем пользователя
        await handler.connect(user_id)
        
        # Обрабатываем сообщения
        await handler.handle_messages()

    except WebSocketDisconnect:
        if handler.user_id:
            await handler.disconnect()
            logger.info(f"WebSocket disconnected for user {handler.user_id}")
        else:
            logger.info("WebSocket disconnected before authentication")
    
    except Exception as e:
        logger.error(f"Unexpected error in WebSocket connection: {e}", exc_info=True)
        if handler.user_id:
            await handler.disconnect()
        try:
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR, reason="Internal server error")
        except:
            pass


@router.websocket("/ws/test")
async def websocket_test(websocket: WebSocket):
    """Тестовый WebSocket endpoint"""
    await websocket.accept()
    await websocket.send_json({"message": "Test WebSocket works!"})
    logger.info("Test WebSocket connected")
    
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_json({"echo": data})
    except WebSocketDisconnect:
        logger.info("Test WebSocket disconnected")