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
        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            return response.json()
