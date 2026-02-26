from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.config import settings
from src.db.session import engine, Base
from src.api.agents import router as agents_router
from src.api.matches import router as matches_router

app = FastAPI(title=settings.PROJECT_NAME, version=settings.VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

app.include_router(agents_router, prefix="/agents", tags=["agents"])
app.include_router(matches_router, prefix="/matches", tags=["matches"])

@app.get("/")
async def root():
    return {"message": "Welcome to Agentic Hinge API!"}
