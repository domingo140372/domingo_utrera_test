# tests/conftest.py

import inspect
import pytest

# importaciones tuyas (las pedidas)
from app.database import create_engine, SQLModel, Session, get_session
from fastapi.testclient import TestClient
import fakeredis
import fakeredis.aioredis
from httpx import AsyncClient, ASGITransport
from app.main import create_app
from app.middlewares.rate_limit import RedisRateLimitMiddleware

# ---------------------------------------------------------
# Configuración de DB en memoria usando el create_engine de tu app
# ---------------------------------------------------------
sqlite_url = "sqlite:///:memory"  
# usa la misma forma que en tu proyecto
# si tu create_engine acepta connect_args:
try:
    engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})
except TypeError:
    # En caso de que create_engine tenga otra firma (defensivo)
    engine = create_engine(sqlite_url)


def create_db_and_tables():
    """Crear tablas según SQLModel metadata"""
    SQLModel.metadata.create_all(engine)


# ---------------------------------------------------------
# Fixture: session (sincrónica) — crea y limpia tablas por test
# ---------------------------------------------------------
@pytest.fixture(name="session")
def session_fixture():
    """Fixture de sesión de base de datos para pruebas (sync)."""
    create_db_and_tables()
    with Session(engine) as session:
        yield session
    # limpieza
    SQLModel.metadata.drop_all(engine)


# ---------------------------------------------------------
# Fixture: client (async) — usa AsyncClient + ASGITransport y fakeredis async
# ---------------------------------------------------------
@pytest.fixture(name="client")
async def client_fixture(session: Session):
    """
    Fixture para cliente de pruebas asíncrono.

    - Detecta si get_session original es async/gen y crea un override compatible.
    - Usa fakeredis.aioredis.FakeRedis() (async) para el middleware de rate limit.
    - Usa ASGITransport para AsyncClient (httpx >= 0.28).
    """

    # --- Crear override de get_session que sea compatible ---
    # Si la dependencia original es una async-generator, debemos devolver un async override.
    if inspect.isasyncgenfunction(get_session) or inspect.iscoroutinefunction(get_session):
        async def get_session_override():
            # yield la sesión de pruebas (session provista por el fixture sync)
            yield session
    else:
        # dependencia sync-generator o sync callable
        def get_session_override():
            yield session

    # --- Redis simulado (async) ---
    # Usamos fakeredis.aioredis.FakeRedis para evitar TypeError si el middleware usa await.
    fake_redis = fakeredis.aioredis.FakeRedis()

    # --- Crear la app inyectando el cliente redis falso ---
    # Se asume que create_app acepta parámetro redis_client opcional
    try:
        app = create_app(redis_client=fake_redis)
    except TypeError:
        # Si create_app no acepta ese argumento, intenta crear app sin inyectarlo
        app = create_app()

        # si el middleware espera un attr en app, lo añadimos (defensivo)
        setattr(app.state, "redis_client", fake_redis)

    # --- Inyectar override de la sesión ---
    app.dependency_overrides[get_session] = get_session_override

    # --- Crear transport ASGI para httpx (compatibilidad con versiones recientes) ---
    transport = ASGITransport(app=app)

    # --- Cliente httpx async usando ASGITransport ---
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac

    # --- Limpieza ---
    app.dependency_overrides.clear()
    # flush del redis simulado por si acaso (no siempre necesario)
    try:
        await fake_redis.flushall()
    except Exception:
        # si fake_redis.flushall no existe o falla, lo ignoramos
        pass
