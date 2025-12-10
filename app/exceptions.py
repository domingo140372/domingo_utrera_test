from fastapi import Request
from fastapi.responses import JSONResponse

# Importar las excepciones tal como las tienes en el proyecto
from app.tareas.crud import NotFoundError
from app.tareas.crud import PermissionDeniedError


async def not_found_exception_handler(request: Request, exc: NotFoundError):
    """
    Maneja NotFoundError y devuelve JSON con status 404.
    """
    return JSONResponse(
        status_code=getattr(exc, "status_code", 404),
        content={"detail": str(exc)},
    )


async def permission_denied_exception_handler(request: Request, exc: PermissionDeniedError):
    """
    Maneja PermissionDeniedError y devuelve JSON con status 403.
    """
    return JSONResponse(
        status_code=getattr(exc, "status_code", 403),
        content={"detail": str(exc)},
    )


async def generic_exception_handler(request: Request, exc: Exception):
    """
    Opcional: handler genérico para excepciones no controladas.
    Útil en pruebas o para evitar stack traces en JSON en producción.
    Puedes decidir si lo registras o no.
    """
    return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})