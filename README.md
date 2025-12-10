# 🚀 FastAPI – API de Usuarios, Mensajes y Tareas  
### *Proyecto de pruebas con FastAPI, Postgres, Redis y Pytest*

Este proyecto implementa una API moderna utilizando **FastAPI**, con soporte para autenticación JWT, middleware de *rate limiting* con Redis, mensajería estructurada y pruebas automatizadas con `pytest`.

La intención del proyecto es servir como base sólida para aplicaciones REST de propósito general, manteniendo buenas prácticas y una arquitectura clara.

---

## 📌 Funcionalidades principales

### 🧑‍💻 Usuarios
- Crear, actualizar y eliminar usuarios (borrado lógico).
- Obtener usuario por **ID**, usuario autenticado (**/users/me**) o listado completo.
- Manejo seguro de contraseñas (hashing automático).

### 🔐 Autenticación
- Login mediante **OAuth2 + JWT** (`/token`).
- Expiración configurable y algoritmo ajustable vía `.env`.

### 💬 Mensajes
- Enviar mensajes asociados a una sesión.
- Contar palabras, caracteres y metadatos automáticos.
- Filtrar por remitente, límites y paginación.

### 📝 Tareas
- Crear tareas asignadas a un usuario.
- Consultar tareas listar.
- Consultar tareas por id_tarea.
- Actualizar tareas por id_tarea.
- Eliminar tareas por id_tarea (soft-deleted = True).
- Restaurar tareas por id_tarea (soft-deleted = False).

### 🛡️ Seguridad
- Middleware de **Rate Limiting con Redis**.
- Validación estricta de entrada mediante Pydantic.
- JWT como mecanismo de autenticación.

### 🧪 Pruebas automatizadas
### Nota: Las pruebas unitarias no estan completas y 
### 			dan errores es una parte nueva que estoy experimentando
- Ejecutadas con `pytest`.
- Base de datos temporal SQLite en memoria.
- Tests para usuarios, autenticación y mensajes.

---

## 🛠️ Tecnologías utilizadas

| Componente | Descripción |
|-----------|-------------|
| **FastAPI** | Framework principal para la API. |
| **SQLModel** | Modelado de datos (SQLAlchemy + Pydantic). |
| **Redis** | Almacenamiento rápido para *rate limiting*. |
| **PostgreSQL** (opcional) | Compatible para producción. |
| **Docker Compose** | Orquestación local. |
| **JWT (python-jose)** | Tokens de autenticación. |
| **Pytest** | Motor de pruebas. |

---

## 📂 Estructura del proyecto

 app/
 
│── main.py # Punto de entrada FastAPI

│── config.py # Configuración centralizada (usa .env)

│── database.py # Conexión y creación de tablas

│── epcextions.py # Lanzamiento de errores de manera global

│── inpections # Contiene MVC de inpecciones

│── messages # Contiene MVC de mensajes

│── tareas # Contiene MVC de tareas

│── users # Contiene MVC de usuarios y autenticacion

│── services.py # Lógica de negocio (mensajes)

│── middlewares/

│ └── rate_limit.py # Middleware de Rate Limiting con Redis

tests/

│── test_users.py # Pruebas de usuarios

│── test_auth.py # Pruebas de autenticación

│── test_messages.py # Pruebas de mensajes

│── test_tareas.py # Pruebas de tareas


docker-compose.yml # Servicios FastAPI + Redis

requirements.txt # Dependencias

local_env.txt # Variables de entorno (ejemplo)

---
## Clonar el proyecto
```
git clone git@github.com:domingo140372/domingo_utrera_test.git
```

## ⚙️ Configuración

### 1. Variables de entorno (`.env`)
Crea un archivo `.env` en la raíz:

```env
# Base de datos
DATABASE_URL="sqlite:///./database.db"
# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0

# Seguridad
SECRET_KEY=tu_hash_secreto
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Rate limiting
RATE_LIMIT=100
RATE_LIMIT_WINDOW=60

⚠️ local_env.txt sirve como plantilla.
⚠️ .env no se sube a GitHub.

```


🐳 Levantar servicios con Docker
```
	docker-compose up --build
```

## Esto iniciará:

| 		Servicio			|			URL  		|
|-----------------------------|---------------------|
| FastAPI | http://localhost:8000 |
| Redis | redis://localhost:6379 |
| PgAdmin |	http://localhost:8080 |

## 🔧 Seeder automático de usuario admin

El proyecto incluye un seeder que se ejecuta automáticamente cuando la aplicación inicia.
Este seeder crea un usuario administrador si aún no existe en la base de datos.

## 📌 ¿Para qué sirve?

Garantizar que siempre exista un usuario con permisos administrativos.

Evitar tener que crear manualmente el admin al iniciar un entorno nuevo.

Útil para desarrollo, testing y despliegues iniciales.
```
	ADMIN_EMAIL=admin@example.com
	ADMIN_PASSWORD=admin123
	ADMIN_USERNAME=admin_tareas
```

## 🚀 Ejecución automática al iniciar FastAPI

El seeder corre durante el evento startup de FastAPI.

## 🧪 Pruebas

´´´
***NOTA: Las pruebas unitarias actualmente no estan completas
	  y estan dando error***
´´´
🧪 Ejecución de pruebas
1. Crear y activar entorno virtual
	```
	python3 -m venv venv
	source venv/bin/activate
	```
2. Instalar dependencias
```
pip install -r requirements.txt
```
3. Ejecutar pruebas
```
pytest -v
```

## Pruebas incluidas:

Creación y autenticación de usuarios

Verificación de JWT

Validación de mensajes

Pruebas de límite de tasa con Redis


## 📚 Documentación automática

FastAPI genera documentación interactiva:
```
Swagger UI:
http://localhost:8000/docs
```
<img width="1265" height="433" alt="image" src="https://github.com/user-attachments/assets/9da6eccf-5d5d-4a76-9e1a-52851ecab12f" />

```
ReDoc:
http://localhost:8000/redoc
```

📌 - **Próximos pasos**

	- Integrar Socket.IO para notificaciones en tiempo real.

	- Añadir soporte para PostgreSQL en lugar de SQLite.

	- Despliegue automatizado con GitHub Actions + IaC (CloudFormation/Terraform).
