from __future__ import annotations
from typing import Optional
from uuid import UUID
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, constr, validator

def _titulo_invalido(valor: Optional[str]) -> bool:
    """
    Normaliza y verifica si el título es inválido:
    - None -> inválido
    - cadena vacía o sólo espacios -> inválido
    - la palabra literal 'string' (cualquier case) -> inválido
    """
    if valor is None:
        return True
    if not isinstance(valor, str):
        return True
    cleaned = valor.strip()
    if cleaned == "":
        return True
    if cleaned.lower() == "string":
        return True
    return False

class EstadoEnum(str, Enum):
    pendiente = "pendiente"
    completada = "completada"


class TareaCreate(BaseModel):
    """Esquema para la creación de una nueva tarea desde el cliente."""
    user_id: UUID = Field(..., description="ID del usuario propietario de la tarea")
    titulo: constr(min_length=1, max_length=255) = Field(..., description="Título de la tarea (no vacío)")
    descripcion: Optional[str] = Field(None, description="Descripción opcional de la tarea")

    @validator("titulo", pre=True, always=True)
    def validar_titulo_create(cls, v):
        if _titulo_invalido(v):
            raise ValueError("Debe ingresar un titulo valido")
        return v

    class Config:
        orm_mode = True


class TareaRead(BaseModel):
    """Esquema para la lectura/serialización de una tarea desde la API."""
    tarea_id: str
    user_id: UUID
    titulo: str
    descripcion: Optional[str] = None
    estado: EstadoEnum
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class TareaUpdate(BaseModel):
    """
    Esquema para actualizar una tarea.
    - Todos los campos son opcionales: el cliente puede enviar solo los que desea cambiar.
    - titulo, si se proporciona, debe respetar la restricción de longitud y no estar vacío.
    """
    titulo: Optional[constr(min_length=1, max_length=255)] = Field(
        None, description="Nuevo título (si se envía, no puede estar vacío)"
    )
    descripcion: Optional[Optional[str]] = Field(
        None, description="Nueva descripción (puede ser None para limpiar)"
    )
    estado: Optional[EstadoEnum] = Field(
        None, description="Nuevo estado: 'pendiente' o 'completada'"
    )

    class Config:
        orm_mode = True


class TareaResponse(BaseModel):
    """Respuesta para lectura/serialización de una tarea."""

    tarea_id: str
    user_id: UUID
    titulo: str
    descripcion: Optional[str] = None
    is_deleted: bool = False
    estado: EstadoEnum
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
