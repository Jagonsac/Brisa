from fastapi import FastAPI

from app.core.config import settings
from app.core.cors import configure_cors
from app.routers.geocoding import router as geocoding_router
from app.routers.health import router as health_router
from app.routers.routes import router as routes_router
from app.routers.stations import router as stations_router

app = FastAPI(title=settings.service_name, version=settings.version)
configure_cors(app)

app.include_router(health_router)
app.include_router(stations_router)
app.include_router(routes_router)
app.include_router(geocoding_router)
