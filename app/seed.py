from sqlmodel import Session, select
from .users.models import Users
from app.users.crud import hash_password
from .config import settings


def seed_admin(session: Session):
    """Crea usuario admin si no existe."""
    admin_email = settings.ADMIN_EMAIL
    admin_password = settings.ADMIN_PASSWORD
    admin_username = settings.ADMIN_USERNAME

    # Verificar si ya existe
    stmt = select(Users).where(Users.email == admin_email)
    existing_admin = session.exec(stmt).first()

    if existing_admin:
        print("👤 Admin ya existe, no se crea nuevamente.")
        return

    # Crear admin
    admin_user = Users(
        username=admin_username,
        email=admin_email,
        password_hash=hash_password(admin_password),
        is_active=True,
    )

    session.add(admin_user)
    session.commit()

    print("✅ Usuario admin creado exitosamente")
