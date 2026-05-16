# Personal Library

API FastAPI con arquitectura hexagonal para integraciones HTTP externas.

## Requisitos

- Python >= 3.11
- [uv](https://docs.astral.sh/uv/) (gestor de dependencias y entornos virtuales)

## Instalación

```bash
uv sync --extra dev
```

> El archivo `uv.lock` está versionado en Git para garantizar builds reproducibles con las mismas versiones exactas de todas las dependencias.

## Ejecutar la aplicación

```bash
uv run uvicorn personal_library.main:app --reload
```

La API estará disponible en `http://localhost:8000`.

## Ejecutar tests

```bash
uv run pytest -v
```

## Ejecutar linter

```bash
uv run ruff check src/ tests/
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

Página Streamlit que abre la cámara del dispositivo, escanea un código de barras ISBN y muestra automáticamente la ficha del libro (título, autores, portada y descripción) consultando la API.

### Dependencias del sistema

```bash
sudo apt-get install -y libzbar0
```

### Instalación

```bash
uv sync --extra scanner
```

### Levantar todo para usarlo

Necesitas dos procesos corriendo a la vez. Ábrelos en terminales separadas:

**Terminal 1 — API de libros:**

```bash
uv run uvicorn personal_library.main:app --reload
```

**Terminal 2 — Lector de códigos de barras:**

```bash
uv run streamlit run src/personal_library/barcode_scanner/app.py
```

Luego abre [http://localhost:8501](http://localhost:8501) en el navegador, pulsa **START** y escanea un código de barras ISBN. El lector normalizará el código, consultará `GET /api/books/{isbn}` en la API y mostrará la ficha del libro en pantalla.

### Variable de entorno `GOOGLE_BOOKS_API_KEY` (recomendado)

Sin API key, Google Books tiene una cuota diaria muy baja (~100 peticiones) y devolverá error 429 cuando se agote. Para usar tu propia cuota:

1. Ve a [Google Cloud Console](https://console.cloud.google.com/apis/library/books.googleapis.com) y habilita la API Books.
2. Crea una credencial de tipo API Key en [Credentials](https://console.cloud.google.com/apis/credentials).
3. Exporta la variable antes de lanzar la API:

```bash
export GOOGLE_BOOKS_API_KEY=tu-api-key
uv run uvicorn personal_library.main:app --reload
```

La cuota gratuita con API key es de 1000 peticiones/día.

### Variable de entorno `PERSONAL_LIBRARY_API_BASE`

Por defecto el lector apunta a `http://127.0.0.1:8000`. Si la API corre en otro host o puerto, define la variable antes de lanzar Streamlit:

```bash
export PERSONAL_LIBRARY_API_BASE=http://<host-api>:8000
uv run streamlit run src/personal_library/barcode_scanner/app.py
```

### Mensajes de error

Los textos coinciden con los que devuelve `lookup_book_for_scan` en `isbn_lookup.py`:

| Situación | Mensaje en pantalla |
|---|---|
| Código no es ISBN válido | `El codigo escaneado no tiene formato ISBN-13 (13 digitos) ni ISBN-10 (9 digitos mas digito de control).` |
| Libro no encontrado (404) | `Libro no encontrado para ese ISBN.` |
| Error de catálogo upstream (502) | El error del servicio externo (detalle incluido, ej. `Error del servicio externo: Google Books API returned 429`) |
| API caída o inaccesible | Prefijo `No se pudo contactar la API:` seguido del detalle del error |
| Respuesta 200 con cuerpo no JSON | `La API devolvio un cuerpo que no es JSON valido.` |
| Otro error HTTP | `Error del servidor (<codigo>).` |
