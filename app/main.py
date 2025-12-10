from fastapi import FastAPI
from redis.asyncio import Redis

from .config import settings
from .database import create_db_and_tables, engine
from .middlewares.rate_limit import RedisRateLimitMiddleware
from .routes import init_routes
from .seed import seed_admin
from sqlmodel import Session

from app.exceptions import (
    not_found_exception_handler,
    permission_denied_exception_handler,
    generic_exception_handler,  # opcional
)

from app.tareas.crud import NotFoundError
from app.tareas.crud import PermissionDeniedError


def create_app(*, redis_client=None) -> FastAPI:
    """
    Factory para crear la app FastAPI.

    - redis_client: si se pasa, se inyecta en app.state.redis y se registra el middleware
      con ese cliente (útil para tests con fakeredis).
    - Si no se pasa, el middleware se registra también (con redis_client=None) y en startup
      se crea la conexión real a Redis y se guarda en app.state.redis.
    """
    app = FastAPI(title="Api_TEST", version="2.0.0")

    # Registrar middleware: se añade DURANTE la construcción de la app (no en caliente)
    app.add_middleware(
        RedisRateLimitMiddleware,
        redis_client=redis_client,  # puede ser None (resolverá en runtime) o un fake_redis para tests
        rate_limit=settings.RATE_LIMIT,
        time_window=settings.RATE_LIMIT_WINDOW,
    )

    # Registrar rutas
    init_routes(app)

    # Registrar handlers globales
    app.add_exception_handler(NotFoundError, not_found_exception_handler)
    app.add_exception_handler(PermissionDeniedError, permission_denied_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)

    # Si nos pasaron un redis_client (ej. fakeredis en tests), lo guardamos ya en app.state
    if redis_client is not None:
        app.state.redis = redis_client

    # Eventos de lifecycle
    @app.on_event("startup")
    async def on_startup():
        """Inicializa la base de datos y Redis al inicio"""
        create_db_and_tables()

        # Si no se inyectó redis_client, creamos la conexión real y la guardamos en app.state
        if not hasattr(app.state, "redis") or app.state.redis is None:
            app.state.redis = Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                decode_responses=True,
            )

        print("🔄 Ejecutando seeders...")
        with Session(engine) as session:
            seed_admin(session)
        print("APP READY")

    @app.on_event("shutdown")
    async def on_shutdown():
        """Cerrar Redis al apagar la app"""
        if hasattr(app.state, "redis"):
            try:
                # algunos fakes no son awaitables; intentamos cerrar de forma segura
                maybe_close = getattr(app.state.redis, "close", None)
                if maybe_close is not None:
                    # close puede ser coroutine o función sincrónica
                    result = maybe_close()
                    if hasattr(result, "__await__"):
                        await result
            except Exception:
                pass

    return app


# instancia por defecto usada en despliegue normal
app = create_app()