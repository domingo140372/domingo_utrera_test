import time
from typing import Optional, List

from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, status
from fastapi.responses import JSONResponse


class RedisRateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware de rate limiting simple usando Redis.

    Correcciones y mejoras realizadas:
    - Evita acceder a self.app.state (problemático cuando self.app es ExceptionMiddleware).
      Ahora se obtiene el cliente Redis desde request.app.state dentro de dispatch.
    - Añadido manejo de excepciones alrededor de las llamadas a Redis para evitar 500s
      en caso de fallo de Redis (fallback: no rate limit).
    - Asegura conversiones a int donde puede venir bytes/strings desde distintos clientes Redis.
    - Maneja request.client posiblemente None de forma segura.
    - Añade cabeceras de rate-limit también en la respuesta de 429.
    """

    def __init__(
        self,
        app,
        redis_client: Optional[object] = None,
        rate_limit: int = 100,
        time_window: int = 60,
        key_prefix: str = "rl",
        exempt_paths: Optional[List[str]] = None,
    ):
        super().__init__(app)
        self._redis = redis_client
        self.rate_limit = int(rate_limit)
        self.time_window = int(time_window)
        self.key_prefix = key_prefix
        self.exempt_paths = exempt_paths or ["/docs", "/openapi.json", "/healthz", "/static"]

    def _redis_from_request(self, request: Request) -> Optional[object]:
        """
        Obtiene el cliente redis preferentemente del atributo _redis (inyectado),
        si no está presente, intenta leer request.app.state.redis (forma correcta
        dentro de middleware).
        """
        if self._redis:
            return self._redis
        # request.app es el FastAPI/Starlette app y sí tiene 'state'
        return getattr(request.app.state, "redis", None)

    def _key(self, identifier: str) -> str:
        return f"{self.key_prefix}:{identifier}"

    def _identifier(self, request: Request) -> str:
        """
        Extrae un identificador único para rate limiting.
        - Si hay Authorization Bearer token, usa el token (recomendado: no usar token entero en prod).
        - Si hay X-Forwarded-For, usa la primera IP.
        - Finalmente, usa request.client.host si está disponible.
        """
        auth = request.headers.get("Authorization", "")
        if isinstance(auth, str) and auth.startswith("Bearer "):
            token = auth.split(" ", 1)[1]
            # En un entorno real conviene hashear este token o usar user_id autenticado para no
            # guardar tokens completos en la key de Redis.
            return f"user:{token}"

        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()

        client = request.client
        if client and client.host:
            return client.host

        # Fallback genérico
        return "unknown"

    async def dispatch(self, request: Request, call_next):
        # Excluir paths (por prefijo)
        for p in self.exempt_paths:
            if request.url.path.startswith(p):
                return await call_next(request)

        redis = self._redis_from_request(request)
        if not redis:
            # Si no hay redis disponible, no aplicamos rate limit (útil para dev/tests).
            return await call_next(request)

        try:
            ident = self._identifier(request)
            key = self._key(ident)

            # INCR y manejar tipos devueltos (puede ser bytes/str/int según cliente)
            current = await redis.incr(key)
            try:
                current = int(current)
            except Exception:
                # si no puede convertirse, forzamos a 1 para continuar (seguro)
                current = 1

            if current == 1:
                # establecer TTL sólo cuando la clave es nueva (comportamiento simple)
                try:
                    await redis.expire(key, self.time_window)
                except Exception:
                    # Si expire falla, no rompemos el request; dejamos continuar
                    pass

            ttl = await redis.ttl(key)
            try:
                ttl = int(ttl) if ttl is not None else None
            except Exception:
                ttl = None

        except Exception:
            # Si Redis da error (conexión, timeouts, etc.), hacemos fallback: permitir la petición.
            # Alternativa: devolver 503 si prefieres fallar cerrado.
            return await call_next(request)

        # Cuando excede el límite
        if current > self.rate_limit:
            reset_ts = int(time.time()) + (ttl if ttl and ttl > 0 else self.time_window)
            body = {
                "status": "error",
                "error": {
                    "code": "RATE_LIMIT_EXCEEDED",
                    "message": "Too many requests",
                    "details": f"Allowed {self.rate_limit} per {self.time_window} seconds",
                    "reset_at": reset_ts,
                },
            }
            headers = {
                "X-RateLimit-Limit": str(self.rate_limit),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(ttl if ttl is not None else self.time_window),
            }
            return JSONResponse(status_code=status.HTTP_429_TOO_MANY_REQUESTS, content=body, headers=headers)

        # Request permitido: pasar y adjuntar cabeceras de rate-limit
        response = await call_next(request)
        # Asegurarse de no romper si response.no headers (Starlette Response siempre tiene dict-like headers)
        response.headers.setdefault("X-RateLimit-Limit", str(self.rate_limit))
        response.headers.setdefault("X-RateLimit-Remaining", str(max(0, self.rate_limit - int(current))))
        response.headers.setdefault("X-RateLimit-Reset", str(ttl if ttl is not None else self.time_window))
        return response