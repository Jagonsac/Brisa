from contextlib import asynccontextmanager
from os import getenv

from fastapi import FastAPI

from app.core.config import settings
from app.core.cors import configure_cors
from app.routers.geocoding import router as geocoding_router
from app.routers.health import router as health_router
from app.routers.routes import router as routes_router
from app.services.bootstrap_service import BootstrapService
from app.routers.stations import router as stations_router
from app.routers.safety import router as safety_router
from app.routers.cyclability import router as cyclability_router
from app.routers.ai_insights import router as ai_insights_router


def _env_flag(name: str, default: str = "true") -> bool:
    return getenv(name, default).strip().lower() in {"1", "true", "yes", "on"}


@asynccontextmanager
async def lifespan(_: FastAPI):
    if _env_flag("PRECOMPUTE_CACHE_ON_STARTUP", "true"):
        BootstrapService().warmup(force_rebuild=_env_flag("FORCE_REBUILD_CACHE_ON_STARTUP", "false"))
    yield


app = FastAPI(title=settings.service_name, version=settings.version, lifespan=lifespan)
configure_cors(app)

app.include_router(health_router)
app.include_router(stations_router)
app.include_router(routes_router)
app.include_router(geocoding_router)
app.include_router(safety_router)
app.include_router(cyclability_router)
app.include_router(ai_insights_router)
