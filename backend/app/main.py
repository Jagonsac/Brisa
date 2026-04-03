from contextlib import asynccontextmanager

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


@asynccontextmanager
async def lifespan(_: FastAPI):
    await warmup_route_graph()
    yield


app = FastAPI(title=settings.service_name, version=settings.version, lifespan=lifespan)
configure_cors(app)

app.include_router(health_router)
app.include_router(stations_router)
app.include_router(routes_router)
app.include_router(geocoding_router)
app.include_router(safety_router)
app.include_router(cyclability_router)
