import asyncio
from typing import Any

import httpx


class BicimadClient:
    def __init__(self, timeout: float = 8.0):
        self.timeout_seconds = timeout

    async def fetch_json(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> Any:
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.get(url, params=params, headers=headers)
                response.raise_for_status()
                return response.json()
        except asyncio.CancelledError as error:
            raise RuntimeError(f"La petición HTTP fue cancelada para: {url}") from error
        except httpx.HTTPError as error:
            raise RuntimeError(f"No se pudo obtener respuesta HTTP desde: {url}") from error
