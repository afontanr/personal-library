# Diseño: Esqueleto Hexagonal FastAPI

**Fecha:** 2026-05-04
**Estado:** Aprobado

## Contexto

Proyecto Python recién iniciado (`personal-library`) para llamar a endpoints externos. Se necesita
establecer una estructura de ficheros siguiendo arquitectura hexagonal antes de comenzar la
implementación real.

El proyecto ya tiene instaladas las dependencias (via egg-info): fastapi, uvicorn, httpx,
pydantic-settings. El pyproject.toml no existe aún y hay que crearlo.

## Objetivo

Crear el esqueleto de ficheros de la arquitectura hexagonal: carpetas, `__init__.py` vacíos, y
stubs mínimos en los ficheros clave. Sin lógica de negocio implementada.

## Arquitectura

Se usa la variante **hexagonal pura por capas** (Opción A). Las capas y sus responsabilidades:

### Domain (núcleo, sin dependencias externas)

- `domain/model/` — entidades y value objects del dominio
- `domain/ports/` — interfaces (puertos) que definen los contratos de salida. La capa de dominio
no conoce implementaciones concretas.

### Application (orquestación)

- `application/use_cases/` — casos de uso que coordinan entidades y puertos. Depende solo del
dominio.

### Infrastructure (detalles técnicos)

- `infrastructure/adapters/http/` — adaptador HTTP concreto con httpx, implementa el puerto
definido en el dominio.
- `infrastructure/config/` — configuración via pydantic-settings (URLs base, timeouts, etc.)

### Presentation (entrada)

- `presentation/api/routes/` — routers FastAPI que reciben las peticiones HTTP.
- `presentation/api/dependencies.py` — inyección de dependencias de FastAPI (provee adaptadores).
- `presentation/api/router.py` — registra todos los subrouters.

### Entrypoint

- `main.py` — crea la instancia de FastAPI y monta el router principal.

## Árbol de ficheros

```
personal-library/
├── pyproject.toml
├── README.md
├── .gitignore
└── src/
    └── personal_library/
        ├── __init__.py
        ├── main.py
        ├── domain/
        │   ├── __init__.py
        │   ├── model/
        │   │   └── __init__.py
        │   └── ports/
        │       ├── __init__.py
        │       └── external_http.py
        ├── application/
        │   ├── __init__.py
        │   └── use_cases/
        │       └── __init__.py
        ├── infrastructure/
        │   ├── __init__.py
        │   ├── adapters/
        │   │   ├── __init__.py
        │   │   └── http/
        │   │       ├── __init__.py
        │   │       └── httpx_adapter.py
        │   └── config/
        │       ├── __init__.py
        │       └── settings.py
        └── presentation/
            ├── __init__.py
            └── api/
                ├── __init__.py
                ├── dependencies.py
                ├── router.py
                └── routes/
                    ├── __init__.py
                    └── health.py
```

## Ficheros con contenido


| Fichero                                         | Contenido                                              |
| ----------------------------------------------- | ------------------------------------------------------ |
| `pyproject.toml`                                | Metadatos del paquete + deps declaradas                |
| `main.py`                                       | `create_app()` que instancia FastAPI y monta el router |
| `domain/ports/external_http.py`                 | ABC con el contrato del puerto HTTP de salida          |
| `infrastructure/adapters/http/httpx_adapter.py` | Clase stub que hereda del puerto                       |
| `infrastructure/config/settings.py`             | `BaseSettings` con `base_url` y `timeout`              |
| `presentation/api/dependencies.py`              | Factory function que provee el adaptador HTTP          |
| `presentation/api/router.py`                    | `APIRouter` que incluye subrouters                     |
| `presentation/api/routes/health.py`             | `GET /health` → `{"status": "ok"}`                     |


El resto son `__init__.py` vacíos.

## Regla de dependencias

```
presentation → application → domain ← infrastructure
```

Ninguna capa interna conoce las capas externas. El dominio no importa nada de infrastructure ni
presentation. La infraestructura implementa los puertos del dominio (inversión de dependencias).

## Decisiones

- **httpx** como cliente HTTP asíncrono (ya declarado en deps).
- **pydantic-settings** para configuración tipada desde variables de entorno.
- **src layout** (`src/personal_library/`) para evitar imports accidentales sin instalación.
- **pyproject.toml** con `[project.optional-dependencies]` para dev deps (pytest, ruff).

## Fuera de alcance

- Implementación de casos de uso concretos.
- Modelos de dominio específicos.
- Tests.
- CI/CD.

