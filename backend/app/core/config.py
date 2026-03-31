from dataclasses import dataclass
from os import getenv


@dataclass(frozen=True)
class Settings:
    service_name: str = "brisa-api"
    version: str = "0.1.0"
    environment: str = getenv("BRISA_ENV", "development")
    port: int = int(getenv("PORT", "8000"))
    bicimad_stations_url: str = getenv(
        "BICIMAD_STATIONS_URL",
        "https://madrid.publicbikesystem.net/customer/gbfs/v2/es/station_information",
    )
    bicimad_fallback_url: str = getenv(
        "BICIMAD_FALLBACK_URL",
        "https://datos.emtmadrid.es/dataset/5fcc0945-2cbd-46c3-801a-6a83f4167c11/resource/105ce5df-793f-4e0a-a88e-5d3b3f024a5d/download/bikestationbicimad_geojson.geojson",
    )
    frontend_origins_raw: str = getenv("FRONTEND_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")

    @property
    def frontend_origins(self) -> list[str]:
        return [origin.strip() for origin in self.frontend_origins_raw.split(",") if origin.strip()]


settings = Settings()
