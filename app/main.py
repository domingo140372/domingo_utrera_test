# app/main.py
from fastapi import FastAPI
from redis.asyncio import Redis

from .config import settings
from .database import create_db_and_tables
from .middlewares.rate_limit import RedisRateLimitMiddleware
from .routes import init_routes

from app.exceptions import (
    not_found_exception_handler,
    permission_denied_exception_handler,
    generic_exception_handler,  # opcional
)

from app.tareas.crud import NotFoundError
from app.tareas.crud import PermissionDeniedError

# Crear app
app = FastAPI(title="Api_TEST", version="2.0.0")

# Registrar middleware (redis_client se obtiene luego desde app.state)
app.add_middleware(
    RedisRateLimitMiddleware,
    redis_client=None,  # se resolverá dinámicamente en el middleware
    rate_limit=settings.RATE_LIMIT,
    time_window=settings.RATE_LIMIT_WINDOW,
)

# Registrar rutas
init_routes(app)

# Registrar handlers globales
app.add_exception_handler(NotFoundError, not_found_exception_handler)
app.add_exception_handler(PermissionDeniedError, permission_denied_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)


@app.on_event("startup")
async def on_startup():
    """Inicializa la base de datos y Redis al inicio"""
    create_db_and_tables()

    # Conectar Redis y guardarlo en app.state
    app.state.redis = Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DB,
        decode_responses=True,
    )


@app.on_event("shutdown")
async def on_shutdown():
    """Cerrar Redis al apagar la app"""
    if hasattr(app.state, "redis"):
        try:
            await app.state.redis.close()
        except Exception:
            pass
