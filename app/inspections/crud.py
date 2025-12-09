from sqlmodel import Session, select
from .models import Inspections, PersonalsInspections
from .schemas import InspeccionCreate


def create_inspeccion(session: Session, inspeccion_data: InspeccionCreate) -> Inspections:
    inspeccion = Inspections(
        vehiculo=inspeccion_data.vehiculo,
        anio=inspeccion_data.anio,
        modelo=inspeccion_data.modelo,
        color=inspeccion_data.color,
        fecha_inspeccion=inspeccion_data.fecha_inspeccion,
        tipo_inspeccion=inspeccion_data.tipo_inspeccion,
        ciudad=inspeccion_data.ciudad,
        estado=inspeccion_data.estado,
        notas=inspeccion_data.notas,
        gcp_folder_link=inspeccion_data.gcp_folder_link,
    )

    session.add(inspeccion)
    session.commit()
    session.refresh(inspeccion)

    # Agregar personas relacionadas
    for persona in inspeccion_data.personas:
        p = PersonalsInspections(
            nombre=persona.nombre,
            telefono=persona.telefono,
            email=persona.email,
            rol=persona.rol,
            inspeccion_id=inspeccion.id,
        )
        session.add(p)

    session.commit()
    session.refresh(inspeccion)
    return inspeccion


def get_inspeccion(session: Session, inspeccion_id: int) -> Inspections:
    statement = select(Inspections).where(Inspections.id == inspection_id)
    return session.exec(statement).first()


def get_all_inspeccions(session: Session):
    statement = select(Inspections)
    return session.exec(statement).all()

