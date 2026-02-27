from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json

from src.core.config import settings
from src.db.session import engine, Base
from src.api.agents import router as agents_router
from src.api.matches import router as matches_router
from src.api.metrics import router as metrics_router
from src.api.activity import router as activity_router
from src.core.websockets import manager
from src.services.cache import redis_client

app = FastAPI(title=settings.PROJECT_NAME, version=settings.VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def redis_listener():
    """Background task that listens to Redis PubSub and broadcasts to WebSockets"""
    pubsub = redis_client.pubsub()
    await pubsub.subscribe("agentic_hinge_events")
    print("Started Redis PubSub listener for 'agentic_hinge_events'")
    
    try:
        async for message in pubsub.listen():
            if message["type"] == "message":
                try:
                    payload = json.loads(message["data"])
                    event_type = payload.get("type")
                    data = payload.get("data", {})
                    
                    if event_type == "new_message":
                        # Route specifically to the match chatroom
                        match_id = data.get("match_id")
                        if match_id:
                            await manager.broadcast(f"match_{match_id}", payload)
                    elif event_type == "new_activity":
                        # Route specifically to the global activity feed
                        await manager.broadcast("feed", payload)
                except json.JSONDecodeError:
                    pass
    except asyncio.CancelledError:
        await pubsub.unsubscribe("agentic_hinge_events")

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # Spawn the Redis pubsub listener
    asyncio.create_task(redis_listener())

app.include_router(agents_router, prefix="/agents", tags=["agents"])
app.include_router(matches_router, prefix="/matches", tags=["matches"])
app.include_router(metrics_router, prefix="/metrics", tags=["metrics"])
app.include_router(activity_router, prefix="/activity", tags=["activity"])

@app.get("/")
async def root():
    return {"message": "Welcome to Agentic Hinge API!"}

@app.websocket("/ws/{channel}")
async def websocket_endpoint(websocket: WebSocket, channel: str):
    await manager.connect(websocket, channel)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, channel)
