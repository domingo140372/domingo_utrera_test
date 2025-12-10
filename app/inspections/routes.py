from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from typing import List

from app.database import get_session
from .schemas import InspeccionCreate, InspeccionRead
from .crud import create_inspeccion, get_inspeccion, get_all_inspeccions

router = APIRouter()


@router.post("/", response_model=InspeccionRead)
def create_new_inspeccion(
    inspeccion: InspeccionCreate, session: Session = Depends(get_session)
):
    return create_inspeccion(session, inspeccion)


@router.get("/{inspeccion_id}", response_model=InspeccionRead)
def read_inspeccion(inspeccion_id: int, session: Session = Depends(get_session)):
    db_inspeccion = get_inspeccion(session, inspeccion_id)
    if not db_inspeccion:
        raise HTTPException(status_code=404, detail="Inspección no encontrada")
    return db_inspeccion


@router.get("/", response_model=List[InspeccionRead])
def read_all_inspeccions(session: Session = Depends(get_session)):
    return get_all_inspeccions(session)

