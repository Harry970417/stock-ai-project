import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import quote, analysis, signal, volume, watchlist
from services.scheduler import scheduler, setup_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_scheduler()
    scheduler.start()
    yield
    scheduler.shutdown(wait=False)


app = FastAPI(title="Stock AI API", version="1.0.0", lifespan=lifespan)

_cors_origins = [
    "http://localhost:3000",
    "https://stock-ai-project-production.up.railway.app",
]
_extra = os.getenv("CORS_ORIGINS", "")
if _extra:
    _cors_origins += [o.strip() for o in _extra.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(quote.router, prefix="/api/quote", tags=["quote"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["analysis"])
app.include_router(signal.router, prefix="/api/signal", tags=["signal"])
app.include_router(volume.router, prefix="/api/volume", tags=["volume"])
app.include_router(watchlist.router, prefix="/api/watchlist", tags=["watchlist"])


@app.get("/")
def root():
    return {"status": "ok", "message": "Stock AI API is running"}
