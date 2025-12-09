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

    # Relación con persona (una inspección puede tener varias contacts implicadas)
    contacts: List["PersonalsInspections"] = Relationship(back_populates="inspections")


class PersonalsInspections(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str
    telefono: Optional[str] = None
    email: Optional[str] = None
    rol: str  # "entrega" o "recibe"

    inspections_id: int = Field(foreign_key="inspections.id")
    inspections: Optional[Inspections] = Relationship(back_populates="contacts")
