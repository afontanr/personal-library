# Personal Library

API FastAPI con arquitectura hexagonal para integraciones HTTP externas.

## Requisitos

- Python >= 3.11

## Instalacion

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Ejecutar la aplicacion

```bash
uvicorn personal_library.main:app --reload
```

La API estara disponible en `http://localhost:8000`.

## Ejecutar tests

```bash
pytest -v
```

## Ejecutar linter

```bash
ruff check src/ tests/
```

## Estructura del proyecto

```
src/personal_library/
  domain/         # Modelo de dominio, puertos (sin dependencias externas)
  application/    # Casos de uso
  infrastructure/ # Adaptadores HTTP, configuracion
  presentation/   # Rutas FastAPI, dependencias, esquemas
  main.py         # Punto de entrada
```
