import pytest
from uuid import uuid4
from pydantic import ValidationError

from app.tareas.schemas import TareaCreate, TareaUpdate


def test_tarea_create_invalid_titulo_string():
    with pytest.raises(ValidationError) as excinfo:
        TareaCreate(user_id=uuid4(), titulo="string", descripcion="descripcion")
    errors = excinfo.value.errors()
    assert any(err["msg"] == "DEBE INGRESAR UN TITULO VALIDO" for err in errors)


def test_tarea_create_invalid_titulo_null():
    # cuando cliente envía "titulo": None -> debe fallar
    with pytest.raises(ValidationError) as excinfo:
        TareaCreate(user_id=uuid4(), titulo=None, descripcion="descripcion")
    errors = excinfo.value.errors()
    assert any(err["msg"] == "DEBE INGRESAR UN TITULO VALIDO" for err in errors)


def test_tarea_update_invalid_titulo_null():
    # Para update, si el cliente explícitamente coloca titulo: null, también debe validarse como inválido
    with pytest.raises(ValidationError) as excinfo:
        TareaUpdate(titulo=None)
    errors = excinfo.value.errors()
    assert any(err["msg"] == "DEBE INGRESAR UN TITULO VALIDO" for err in errors)