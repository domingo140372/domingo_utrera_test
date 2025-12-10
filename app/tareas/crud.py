## CRUD de tareas

from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timezone

from sqlmodel import Session, select
from sqlmodel.sql.expression import Select

from .models import Tareas
from .schemas import TareaCreate, TareaUpdate, EstadoEnum


class NotFoundError(Exception):
    """
    Excepción para recursos no encontrados.

    Atributos útiles:
    - resource: nombre del tipo de recurso (p.ej. "Tarea")
    - identifier: id del recurso buscado (opcional)
    - message: mensaje humano legible
    - status_code: código HTTP asociado (por defecto 404)
    """
    def __init__(self, resource: str = "resource", 
    					identifier: str | None = None, 
    					message: str | None = None):
        self.resource = resource
        self.identifier = identifier
        if message is None:
            if identifier:
                message = f"{resource} no encontrada (id={identifier})"
            else:
                message = f"{resource} no encontrada"
        self.message = message
        self.status_code = 404
        super().__init__(self.message)
    
    def __str__(self) -> str:
        	return self.message

    def __repr__(self) -> str:
        return f"NotFoundError(resource={self.resource!r}, identifier={self.identifier!r}, message={self.message!r})"


class PermissionDeniedError(Exception):
    """
    Excepción para operaciones denegadas por permisos.

    Atributos:
    - resource: nombre del tipo de recurso (p. ej. "Tarea")
    - identifier: id del recurso afectado (opcional)
    - action: acción intentada (p. ej. "eliminar", "actualizar")
    - message: mensaje legible para el cliente (si no se proporciona se genera uno por defecto)
    - status_code: código HTTP asociado (por defecto 403)
    """
    def __init__(
        self,
        resource: str = "resource",
        identifier: Optional[str] = None,
        action: Optional[str] = None,
        message: Optional[str] = None,
    ):
        self.resource = resource
        self.identifier = identifier
        self.action = action

        if message is None:
            if action and identifier:
                message = f"No autorizado para {action} {resource} (id={identifier})"
            elif action:
                message = f"No autorizado para {action} {resource}"
            elif identifier:
                message = f"No autorizado sobre {resource} (id={identifier})"
            else:
                message = "Permiso denegado"

        self.message = message
        self.status_code = 403
        super().__init__(self.message)

    def __str__(self) -> str:
        return self.message

    def __repr__(self) -> str:
        return (
            f"PermissionDeniedError(resource={self.resource!r}, "
            f"identifier={self.identifier!r}, action={self.action!r}, message={self.message!r})"
        )


class TaskRepository:
    """
    Repository/DAO para la entidad Tareas.

    Uso típico:
        with Session(engine) as session:
            repo = TaskRepository(session)
            tarea = repo.create(tarea_in)
    """

    def __init__(self, session: Session):
        self.session = session

    def _base_query(self, include_deleted: bool = False) -> Select:
        stmt = select(Tareas)
        if not include_deleted:
            stmt = stmt.where(Tareas.is_deleted == False)  # filtra borrados suaves por defecto
        else:
            stmt = stmt.where(Tareas.is_deleted == True)  # filtra borrados suaves por defecto

        return stmt

    def create(self, tarea_in: TareaCreate) -> Tareas:
        """
        Crea una nueva tarea.
        """
        tarea = Tareas(
            user_id=tarea_in.user_id,
            titulo=tarea_in.titulo,
            descripcion=tarea_in.descripcion,
            # estado por defecto viene del modelo (pendiente)
        )
        self.session.add(tarea)
        self.session.commit()
        self.session.refresh(tarea)
        return tarea

    def get(self, tarea_id: str, include_deleted: bool = False) -> Optional[Tareas]:
        """
        Obtiene una tarea por su id. Por defecto excluye is_deleted == True.
        """
        stmt = self._base_query(include_deleted=include_deleted).where(Tareas.tarea_id == tarea_id)
        result = self.session.exec(stmt).first()
        return result

    def list(
        self,
        user_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100,
        include_deleted: bool = False,
    ) -> List[Tareas]:
        """
        Lista tareas. Por defecto excluye borrados suaves.
        Soporta filtrado por user_id y paginación simple skip/limit.
        """
        stmt = self._base_query(include_deleted=include_deleted)
        if user_id is not None:
            stmt = stmt.where(Tareas.user_id == user_id)
        stmt = stmt.offset(skip).limit(limit)
        return self.session.exec(stmt).all()

    def update(self, tarea_id: str, tarea_in: TareaUpdate, requester_user_id: Optional[UUID] = None) -> Tareas:
        """
        Actualiza campos permitidos de la tarea.
        - requester_user_id: si se pasa, se valida que sea el propietario antes de aplicar cambios.
        - Solo los campos titulo, descripcion y estado son actualizables desde esta función.
        """
        tarea = self.get(tarea_id, include_deleted=False)
        if not tarea:
            raise NotFoundError(resource="Tarea", identifier=tarea_id)

        if requester_user_id is not None and tarea.user_id != requester_user_id:
            raise PermissionDeniedError(resource="Tarea", identifier=tarea_id, action="actualizar")

        data = tarea_in.dict(exclude_unset=True)
        allowed = {"titulo", "descripcion", "estado"}
        for key, value in data.items():
            if key in allowed:
                # validar tipo para estado si viene como str/int (se espera EstadoEnum o str válido)
                if key == "estado" and value is not None:
                    if isinstance(value, str):
                        # normalizar y validar
                        try:
                            value = EstadoEnum(value)
                        except ValueError:
                            raise ValueError(f"Estado inválido: {value}")
                setattr(tarea, key, value)

        # actualizar timestamp
        tarea.updated_at = datetime.now(timezone.utc)

        self.session.add(tarea)
        self.session.commit()
        self.session.refresh(tarea)
        return tarea

    def soft_delete(self, tarea_id: str, requester_user_id: Optional[UUID] = None) -> None:
        """
        Soft delete: marca is_deleted = True.
        - Verifica existencia y permisos (si requester_user_id es provisto).
        - No elimina físicamente la fila.
        """
        tarea = self.get(tarea_id, include_deleted=False)
        if not tarea:
            raise NotFoundError(resource="Tarea", identifier=tarea_id)

        if requester_user_id is not None and tarea.user_id != requester_user_id:
            raise PermissionDeniedError(resource="Tarea", identifier=tarea_id, action="eliminar")

        tarea.is_deleted = True
        tarea.updated_at = datetime.now(timezone.utc)
        self.session.add(tarea)
        self.session.commit()
        self.session.refresh(tarea)
        return tarea

    def restore(self, tarea_id: str, requester_user_id: Optional[UUID] = None) -> Tareas:
        """
        Restaura una tarea borrada (is_deleted = False).
        """
        tarea = self.get(tarea_id, include_deleted=True)
        if not tarea:
            raise NotFoundError(resource="Tarea", identifier=tarea_id)

        if not tarea.is_deleted:
            return tarea  # ya estaba activa

        if requester_user_id is not None and tarea.user_id != requester_user_id:
            raise PermissionDeniedError(resource="Tarea", identifier=tarea_id, action="eliminar")

        tarea.is_deleted = False
        tarea.updated_at = datetime.now(timezone.utc)
        self.session.add(tarea)
        self.session.commit()
        self.session.refresh(tarea)
        return tarea

