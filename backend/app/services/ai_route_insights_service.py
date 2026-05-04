from __future__ import annotations

import json
import os
import time
from collections import defaultdict, deque
from threading import Lock
from typing import Any

import httpx


class AIRouteInsightsError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


class AIRouteInsightsService:
    def __init__(self) -> None:
        self.api_key = os.getenv("OPENAI_API_KEY", "").strip()
        self.model = os.getenv("OPENAI_ROUTE_INSIGHTS_MODEL", "gpt-5.4-mini")
        self.timeout_seconds = float(os.getenv("OPENAI_ROUTE_INSIGHTS_TIMEOUT_SECONDS", "12"))
        self.max_requests_per_window = int(os.getenv("AI_ROUTE_INSIGHTS_RATE_LIMIT", "20"))
        self.rate_limit_window_seconds = int(os.getenv("AI_ROUTE_INSIGHTS_WINDOW_SECONDS", "300"))
        self._calls_by_ip: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def _enforce_rate_limit(self, client_key: str) -> None:
        now = time.time()
        with self._lock:
            history = self._calls_by_ip[client_key]
            while history and now - history[0] > self.rate_limit_window_seconds:
                history.popleft()
            if len(history) >= self.max_requests_per_window:
                raise AIRouteInsightsError("rate_limited", "Has alcanzado el límite temporal de análisis con IA. Inténtalo en unos minutos.", 429)
            history.append(now)

    def _build_prompt_payload(self, routes: list[dict[str, Any]]) -> dict[str, Any]:
        sanitized = []
        for route in routes:
            sanitized.append(
                {
                    "mode": route.get("mode"),
                    "distanceKm": route.get("distanceKm"),
                    "relativeSafety": route.get("relativeSafety"),
                    "lightingQuality": route.get("lightingQuality"),
                    "nightRisk": route.get("nightRisk"),
                    "hazardPoints": route.get("hazardPoints", route.get("hazards", []))[:20],
                    "explanations": route.get("explanations", [])[:4],
                }
            )
        return {"city": "Madrid", "routes": sanitized}

    async def analyze_routes(self, *, routes: list[dict[str, Any]], client_key: str) -> dict[str, Any]:
        if not self.api_key:
            raise AIRouteInsightsError("ai_not_configured", "La IA no está configurada en el servidor.", 503)
        if not routes:
            raise AIRouteInsightsError("invalid_input", "No hay rutas para analizar.")

        self._enforce_rate_limit(client_key)

        prompt_payload = self._build_prompt_payload(routes)
        system_prompt = (
            "Eres el copiloto ciclista de Brisa (Madrid). "
            "Analiza SOLO seguridad ciclista de rutas proporcionadas. "
            "Responde SIEMPRE JSON válido y nada más. "
            "Prioriza incidencias concretas de puntos de peligro antes que puntuaciones globales. Evita anglicismos (por ejemplo, usa 'puntos de peligro' y no 'hotspots'). "
            "Si una ruta no tiene hazardPoints, indícalo explícitamente. "
            "Si faltan datos, dilo con prudencia. No inventes calles, barrios, eventos ni coordenadas."
        )
        user_prompt = (
            "Genera JSON con esta forma exacta: "
            "{\"overview\":string,\"routes\":[{\"mode\":string,\"best\":string,\"worst\":string,\"riskLevel\":\"low\"|\"medium\"|\"high\",\"tips\":[string]}],\"globalTips\":[string]}. "
            "Máximo 2 frases por campo textual y máximo 3 consejos por ruta. Explica que una alta concentración de accidentes también puede reflejar mayor volumen de tráfico ciclista en la zona, no solo mayor peligro intrínseco.\n"
            f"Datos: {json.dumps(prompt_payload, ensure_ascii=False)}"
        )

        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.post(
                "https://api.openai.com/v1/responses",
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                json={
                    "model": self.model,
                    "input": [
                        {"role": "system", "content": [{"type": "input_text", "text": system_prompt}]},
                        {"role": "user", "content": [{"type": "input_text", "text": user_prompt}]},
                    ],
                    "text": {"format": {"type": "json_schema", "name": "route_insights", "schema": {"type": "object", "additionalProperties": False, "properties": {"overview": {"type": "string"}, "routes": {"type": "array", "items": {"type": "object", "additionalProperties": False, "properties": {"mode": {"type": "string"}, "best": {"type": "string"}, "worst": {"type": "string"}, "riskLevel": {"type": "string", "enum": ["low", "medium", "high"]}, "tips": {"type": "array", "items": {"type": "string"}}}, "required": ["mode", "best", "worst", "tips"]}}, "globalTips": {"type": "array", "items": {"type": "string"}}}, "required": ["overview", "routes", "globalTips"]}}},
                    "max_output_tokens": 650,
                },
            )
        if response.status_code >= 400:
            raise AIRouteInsightsError("openai_error", "No se pudo generar el análisis IA en este momento.", 502)

        payload = response.json()
        output_text = payload.get("output_text", "") or ""
        for item in payload.get("output", []):
            for content in item.get("content", []):
                if content.get("type") in {"output_text", "text"}:
                    output_text += content.get("text", "")
                if content.get("type") == "output_json":
                    output_text += json.dumps(content.get("json", {}), ensure_ascii=False)
        if not output_text:
            raise AIRouteInsightsError("invalid_ai_response", "La IA devolvió una respuesta vacía.", 502)

        try:
            data = json.loads(output_text)
        except json.JSONDecodeError as error:
            raise AIRouteInsightsError("invalid_ai_response", "La IA devolvió un formato no válido.", 502) from error

        if not isinstance(data, dict) or "routes" not in data:
            raise AIRouteInsightsError("invalid_ai_response", "La IA devolvió un esquema incompleto.", 502)

        data.setdefault("overview", "")
        data.setdefault("globalTips", [])
        normalized_routes = []
        for route in data.get("routes", []):
            if not isinstance(route, dict):
                continue
            normalized_routes.append({
                "mode": str(route.get("mode", "")),
                "best": str(route.get("best", "")),
                "worst": str(route.get("worst", "")),
                "riskLevel": route.get("riskLevel", "medium"),
                "tips": [str(tip) for tip in (route.get("tips") or [])][:3],
            })
        data["routes"] = normalized_routes

        return data
