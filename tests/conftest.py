import pytest
from app.database import create_engine, SQLModel, Session, get_session
from fastapi.testclient import TestClient
import fakeredis
from httpx import AsyncClient
from app.main import create_app
from app.database import get_session
from app.middlewares.rate_limit import RedisRateLimitMiddleware

# Usamos SQLite en memoria para los tests
sqlite_url = "sqlite:///:memory:"
engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

@pytest.fixture(name="session")
def session_fixture():
    """Fixture de sesión de base de datos para pruebas."""
    create_db_and_tables()
    with Session(engine) as session:
        yield session
    SQLModel.metadata.drop_all(engine)

@pytest.fixture(name="client")
async def client_fixture(session: Session):
    """Fixture para cliente de pruebas asíncrono con Redis simulado.

    - Crea fake_redis y construye la app con create_app(redis_client=fake_redis)
      para que el middleware se registre durante la creación.
    - Sobrescribe la dependencia get_session para usar la sesión de pruebas.
    - Usa AsyncClient en contexto para yield del cliente asíncrono.
    """
    # Sobrescribir la dependencia de la BD para que use la sesión de pruebas
    def get_session_override():
        return session

    # Redis simulado con fakeredis (inyectado en la app al crearla)
    fake_redis = fakeredis.FakeStrictRedis()

    # Construir la app de prueba con el redis falso (middleware ya registrado en create_app)
    app = create_app(redis_client=fake_redis)

    # Inyectar override para la dependencia de sesión
    app.dependency_overrides[get_session] = get_session_override

    # Crear cliente asíncrono de pruebas y exponerlo al test
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        yield ac

    # Limpieza al finalizar el fixture
    app.dependency_overrides.clear()