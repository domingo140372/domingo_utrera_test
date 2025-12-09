from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class PersonaInspeccionBase(BaseModel):
    nombre: str
    telefono: Optional[str] = None
    email: Optional[str] = None
    rol: str


class PersonaInspeccionCreate(PersonaInspeccionBase):
    pass


class PersonaInspeccionRead(PersonaInspeccionBase):
    id: int
    inspeccion_id: int


class InspeccionBase(BaseModel):
    vehiculo: str
    anio: int
    modelo: str
    color: str
    fecha_inspeccion: datetime
    tipo_inspeccion: str
    ciudad: str
    estado: str
    notas: Optional[str] = None
    gcp_folder_link: Optional[str] = None


class InspeccionCreate(InspeccionBase):
    personas: List[PersonaInspeccionCreate] = []


class InspeccionRead(InspeccionBase):
    id: int
    personas: List[PersonaInspeccionRead] = []

