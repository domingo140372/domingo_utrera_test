from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from .crud import TaskRepository, NotFoundError, PermissionDeniedError
from .schemas import (
    TareaCreate,
    TareaUpdate,
    TareaResponse,
    TareaRead,
)
from app.database import get_session  # depende de que exista esta dependencia en tu proyecto
from app.users.models import Users
from app.auth import get_current_user  # depende de que exista: devuelve Users

router = APIRouter()


def _map_notfound(exc: NotFoundError) -> HTTPException:
    return HTTPException(status_code=exc.status_code if hasattr(exc, "status_code") else 404, detail=str(exc))


def _map_permission(exc: PermissionDeniedError) -> HTTPException:
    return HTTPException(status_code=exc.status_code if hasattr(exc, "status_code") else 403, detail=str(exc))


@router.post(
    "/",
    response_model=TareaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear nueva tarea",
)
def create_tarea(
    tarea_in: TareaCreate,
    session: Session = Depends(get_session),
    current_user: Users = Depends(get_current_user),
):
    """
    Crea una nueva tarea. El owner se fuerza al usuario autenticado (current_user).
    """
    repo = TaskRepository(session)

    # Forzar que la tarea pertenezca al usuario autenticado
    tarea_in.user_id = current_user.id  # si TareaCreate lo tiene como atributo; si no, creamos dict abajo

    try:
        tarea = repo.create(tarea_in)
    except Exception as exc:
        # Errores inesperados => 500
        raise HTTPException(status_code=500, detail=str(exc))

    return tarea


@router.get(
    "/",
    response_model=List[TareaRead],
    summary="Listar tareas del usuario autenticado",
)
def list_tareas(
    session: Session = Depends(get_session),
    current_user: Users = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100,
    include_deleted: bool = False,
):
    """
    Lista las tareas del usuario autenticado.
    Por defecto excluye tareas con is_deleted = True.
    """
    repo = TaskRepository(session)
    tareas = repo.list(user_id=current_user.id, skip=skip, limit=limit, include_deleted=include_deleted)
    return tareas


@router.get(
    "/{tarea_id}",
    response_model=TareaResponse,
    summary="Obtener una tarea por id",
)
def get_tarea(
    tarea_id: str,
    session: Session = Depends(get_session),
    current_user: Users = Depends(get_current_user),
    include_deleted: bool = False,
):
    """
    Obtiene una tarea por su id. Solo el propietario (o un rol con permiso) debería verla.
    """
    repo = TaskRepository(session)
    try:
        tarea = repo.get(tarea_id, include_deleted=include_deleted)
        if not tarea:
            raise NotFoundError(resource="Tarea", identifier=tarea_id)
        # Validación de propietario: solo el dueño puede leer su tarea
        if tarea.user_id != current_user.id:
            raise PermissionDeniedError(resource="Tarea", identifier=tarea_id, action="ver")
    except NotFoundError as exc:
        raise _map_notfound(exc)
    except PermissionDeniedError as exc:
        raise _map_permission(exc)

    return tarea


@router.put(
    "/{tarea_id}",
    response_model=TareaResponse,
    summary="Actualizar una tarea",
)
def update_tarea(
    tarea_id: str,
    tarea_in: TareaUpdate,
    session: Session = Depends(get_session),
    current_user: Users = Depends(get_current_user),
):
    """
    Actualiza una tarea. Solo el propietario puede actualizar.
    Se aceptan actualizaciones parciales (campos opcionales).
    """
    repo = TaskRepository(session)
    try:
        tarea = repo.update(tarea_id, tarea_in, requester_user_id=current_user.id)
    except NotFoundError as exc:
        raise _map_notfound(exc)
    except PermissionDeniedError as exc:
        raise _map_permission(exc)
    except ValueError as exc:
        # por ejemplo enum inválido
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    return tarea


@router.delete(
    "/{tarea_id}/delete",
    response_model=TareaRead,
    summary="Eliminar (soft delete) una tarea",
)
def delete_tarea(
    tarea_id: str,
    session: Session = Depends(get_session),
    current_user: Users = Depends(get_current_user),
):
    """
    Soft-delete: marca is_deleted = True en lugar de eliminar físicamente.
    Solo el propietario puede eliminar su tarea.
    """
    repo = TaskRepository(session)
    try:
        tarea = repo.soft_delete(tarea_id, requester_user_id=current_user.id)
    except NotFoundError as exc:
        raise _map_notfound(exc)
    except PermissionDeniedError as exc:
        raise _map_permission(exc)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    return tarea


@router.post(
    "/{tarea_id}/restore",
    response_model=TareaResponse,
    summary="Restaurar una tarea borrada",
)
def restore_tarea(
    tarea_id: str,
    session: Session = Depends(get_session),
    current_user: Users = Depends(get_current_user),
):
    """
    Restaura una tarea previamente marcada como is_deleted = True.
    Solo el propietario puede restaurarla.
    """
    repo = TaskRepository(session)
    try:
        tarea = repo.restore(tarea_id, requester_user_id=current_user.id)
    except NotFoundError as exc:
        raise _map_notfound(exc)
    except PermissionDeniedError as exc:
        raise _map_permission(exc)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    return tarea