# Personal Library

API FastAPI con arquitectura hexagonal para integraciones HTTP externas.

## Requisitos

- Python >= 3.11

## Instalación

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Ejecutar la aplicación

```bash
uvicorn personal_library.main:app --reload
```

La API estará disponible en `http://localhost:8000`.

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
  infrastructure/ # Adaptadores HTTP, configuración
  presentation/   # Rutas FastAPI, dependencias, esquemas
  barcode_scanner/ # Lector de códigos de barras (Streamlit + WebRTC)
  main.py         # Punto de entrada
```

## Lector de códigos de barras

Página Streamlit que abre la cámara del dispositivo y escanea códigos de barras en tiempo real.

### Dependencias del sistema

```bash
sudo apt-get install -y libzbar0
```

### Instalación

```bash
pip install -e ".[scanner]"
```

### Ejecutar el lector

```bash
streamlit run src/personal_library/barcode_scanner/app.py
```

La aplicación estará disponible en `http://localhost:8501`. Pulsa **START** para abrir la cámara y escanear códigos de barras.
