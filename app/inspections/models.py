from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime


class Inspections(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    vehiculo: str
    anio: int
    modelo: str
    color: str
    fecha_inspeccion: datetime
    tipo_inspeccion: str  # pickup, delivery
    ciudad: str
    estado: str
    notas: Optional[str] = None
    gcp_folder_link: Optional[str] = None  # enlace a bucket GCP

    # Relación con persona (una inspección puede tener varias personas implicadas)
    personas: List["PersonaInspeccion"] = Relationship(back_populates="inspeccion")


class PersonalsInspections(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str
    telefono: Optional[str] = None
    email: Optional[str] = None
    rol: str  # "entrega" o "recibe"

    inspeccion_id: int = Field(foreign_key="inspeccion.id")
    inspeccion: Optional[Inspeccion] = Relationship(back_populates="personas")
