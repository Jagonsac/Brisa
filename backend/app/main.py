from contextlib import asynccontextmanager
from os import getenv

from fastapi import FastAPI

from app.core.config import settings
from app.core.cors import configure_cors
from app.routers.geocoding import router as geocoding_router
from app.routers.health import router as health_router
from app.routers.routes import router as routes_router
from app.routers.routes import warmup_route_graph
from app.routers.stations import router as stations_router
from app.routers.safety import router as safety_router
from app.routers.cyclability import router as cyclability_router
from app.services.safety_service import SafetyService


def _should_precompute_on_startup() -> bool:
    return getenv("PRECOMPUTE_CACHE_ON_STARTUP", "true").strip().lower() in {"1", "true", "yes", "on"}


@asynccontextmanager
async def lifespan(_: FastAPI):
    await warmup_route_graph()
    if _should_precompute_on_startup():
        SafetyService().get_neighborhood_grid()
    yield


app = FastAPI(title=settings.service_name, version=settings.version, lifespan=lifespan)
configure_cors(app)

app.include_router(health_router)
app.include_router(stations_router)
app.include_router(routes_router)
app.include_router(geocoding_router)
app.include_router(safety_router)
app.include_router(cyclability_router)
