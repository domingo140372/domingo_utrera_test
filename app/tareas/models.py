## Modelos de tareas
from typing import Optional
from sqlmodel import Field, SQLModel, Relationship
from datetime import datetime, timezone
from uuid import UUID, uuid4
from enum import Enum
from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy.types import Enum as SAEnum

# Importo Users esperando que exista en app.users.models y que tenga una relación back_populates "tareas"
from app.users.models import Users


class EstadoEnum(str, Enum):
    pendiente = "pendiente"
    completada = "completada"


class Tareas(SQLModel, table=True):
    """
    Modelo SQLModel para la entidad 'Tareas'.

    - tarea_id: PK (string generado por uuid4)
    - user_id: FK hacia users.id (se asume UUID en Users)
    - titulo: string obligatorio (validación doble)
    - descripcion: texto opcional
    - estado: enum ('pendiente' | 'completada')
    - created_at / updated_at: timestamps timezone-aware
    - user: relación hacia Users (back_populates="tareas")
    """
    __tablename__ = "tareas"

    tarea_id: Optional[str] = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    titulo: str = Field(..., 
        sa_column=Column(String(255), nullable=False),
        max_length=255,
    )
    descripcion: Optional[str] = Field(default=None)
    estado: EstadoEnum = Field(
        default=EstadoEnum.pendiente,
        sa_column=Column(SAEnum(EstadoEnum, name="estado_enum")),
    )
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_deleted: bool = Field(default=False)

    user: Optional[Users] = Relationship(back_populates="tareas")
