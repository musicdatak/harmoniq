from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import analysis, auth, playlists, tracks


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title="HarmoniQ", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth.router)
app.include_router(playlists.router)
app.include_router(tracks.router)
app.include_router(analysis.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
