import asyncio
import hashlib
import json
import re

import redis.asyncio as redis

from ia_service.core.config import get_settings

# Subir este número cuando cambie un prompt, para ignorar las respuestas guardadas con el prompt viejo
CACHE_VERSION = 1

settings = get_settings()
_client = redis.from_url(settings.REDIS_URL, decode_responses=True)



in_flight: dict[str, asyncio.Future] = {}


def build_cache_key(text: str, provider: str | None, model: str | None) -> str:
    normalized = re.sub(r"\s+", " ", text.strip().lower())
    normalized = re.sub(r"[.!?]+$", "", normalized)
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    return f"nlp4re:cache:v{CACHE_VERSION}:{provider or 'default'}:{model or 'default'}:{digest}"


async def get_cached(key: str) -> dict | None:
    # Si Redis falla, se sigue sin caché en lugar de romper el análisis
    try:
        value = await _client.get(key)
        await _client.incr("nlp4re:stats:hits" if value else "nlp4re:stats:misses")
        return json.loads(value) if value else None
    except Exception:
        return None


async def save_cached(key: str, result: dict) -> None:
    try:
        # nx=True: si otro usuario ya guardó esta clave, no la sobrescribe ni falla
        await _client.set(key, json.dumps(result, ensure_ascii=False), ex=settings.CACHE_TTL_SECONDS, nx=True)
    except Exception:
        pass
