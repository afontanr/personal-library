# Code review: esqueleto hexagonal (PR #1)

**Repositorio:** [afontanr/personal-library](https://github.com/afontanr/personal-library) — Pull Request #1  
**Rango revisado:** `7797b63` (Initial commit) → `ef8400b` (HEAD al momento de la revisión)  
**Tests:** 10/10 pasando (~0,68 s)

---

## Fortalezas

1. **Separación clara de capas hexagonales.** El dominio no importa infraestructura. La regla de dependencias (`presentation → application → domain ← infrastructure`) se respeta de forma coherente.
2. **Puerto modelado como ABC.** `BookRepository` usa `ABC` y `@abstractmethod`, idiomático en Python para un puerto secundario.
3. `**BookInfo` como dataclass congelado.** `@dataclass(frozen=True)` encaja con un objeto de valor: inmutable, comparable por estructura, sin fugas de infra al dominio.
4. **Estructura de tests alineada con la arquitectura.** Cuatro niveles de tests reflejan las capas. Uso de `FakeBookRepository` frente a mocks excesivos en dominio/aplicación. `pytest-httpx` en el adaptador HTTP es adecuado.
5. **Inyección de dependencias con `Depends` de FastAPI.** Idiomático; los overrides en tests funcionan bien (p. ej. `test_books.py`).
6. `**pyproject.toml` con extras de desarrollo.** Separación razonable entre dependencias de runtime y de desarrollo.

---

## Hallazgos

### Crítico (debe corregirse)

#### 1. `httpx.AsyncClient` no se cierra — fuga de recursos

**Archivo:** `src/personal_library/presentation/api/dependencies.py` (aprox. línea 18)

Se crea un `httpx.AsyncClient` por petición y no se cierra nunca, lo que puede agotar descriptores de archivo y conexiones bajo carga.

**Enfoque recomendado:** Gestionar el cliente en el ciclo de vida de la aplicación (`lifespan` de FastAPI), guardarlo en `app.state` e inyectarlo en el factory del repositorio.

```python
from contextlib import asynccontextmanager
import httpx
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with httpx.AsyncClient() as client:
        app.state.http_client = client
        yield

def create_app() -> FastAPI:
    app = FastAPI(title="Personal Library", lifespan=lifespan)
    app.include_router(api_router)
    return app
```

---

### Importante (convendría corregir)

#### 2. Sin validación del ISBN en la ruta

**Archivo:** `src/personal_library/presentation/api/routes/books.py`

El parámetro `isbn` llega como `str` sin validar formato. Conviene acotar (p. ej. ISBN-13 con `Path(pattern=...)` o validación explícita) para evitar entradas inválidas y respuestas confusas desde la API externa.

#### 3. Errores HTTP y de red sin traducción a la capa HTTP

**Archivo:** `src/personal_library/infrastructure/adapters/http/google_books_client.py` (aprox. línea 19)

`response.raise_for_status()` puede propagar `httpx.HTTPStatusError` y producir 500 genéricos. Conviene capturar, mapear 404 a “no encontrado” y decidir política para 5xx, 429, timeouts y errores de conexión.

#### 4. `get_settings()` crea `Settings` en cada petición

**Archivo:** `src/personal_library/presentation/api/dependencies.py`

Reinstanciar `Settings()` en cada request es innecesario y puede ser indeseable si se espera configuración estable por proceso. Patrón habitual: `@lru_cache` en el factory de settings (según documentación de pydantic-settings).

#### 5. Caso de uso instanciado dentro del handler

**Archivo:** `src/personal_library/presentation/api/routes/books.py`

`LookupBookByIsbn` se construye dentro de la ruta en lugar de inyectarse con `Depends`, lo que acopla la ruta al constructor y complica sustituir el caso de uso en tests sin tocar el repositorio.

#### 6. Test de inmutabilidad demasiado permisivo

**Archivo:** `tests/domain/model/test_book.py` (aprox. línea 32)

Capturar `Exception` genérico puede ocultar fallos reales. Preferir `pytest.raises` con las excepciones esperadas (p. ej. `AttributeError` / `FrozenInstanceError`).

---

### Menor (mejoras opcionales)

#### 7. Desviación respecto al alcance del spec

El documento de diseño (`docs/superpowers/specs/2026-05-04-hexagonal-skeleton-design.md`) marcaba fuera de alcance casos de uso concretos, modelo de dominio, tests y lógica de negocio; el PR los incluye. Es una ampliación positiva si está documentada explícitamente en la descripción del PR.

#### 8. Desviación de nombre de puerto frente al borrador del spec

El spec mencionaba un puerto HTTP genérico; el PR usa `BookRepository` orientado al dominio, lo cual suele ser preferible. Conviene mencionarlo en la documentación del PR.

#### 9. README escaso o vacío

Si el spec pedía README operativo, añadir al menos cómo instalar dependencias y arrancar la app localmente.

#### 10. Respuesta como `dict` en lugar de modelo Pydantic

**Archivo:** `src/personal_library/presentation/api/routes/books.py`

Un modelo de respuesta en presentación (p. ej. `BookInfoResponse`) mejora OpenAPI, validación de salida y desacopla el contrato HTTP del dataclass de dominio.

#### 11. URL por defecto de portadas Amazon

**Archivo:** `src/personal_library/infrastructure/config/settings.py`

El dominio `images-na.ssl-images-amazon.com` es legado; valorar `m.media-amazon.com` como default (sigue siendo configurable vía `Settings`).

---

## Recomendaciones

1. Priorizar el ciclo de vida de `httpx.AsyncClient` (punto crítico).
2. Añadir un esquema Pydantic de respuesta en la capa de presentación.
3. Valorar excepciones de dominio (p. ej. libro no encontrado) y mapeo centralizado a códigos HTTP.
4. Añadir `ruff check` (u otra lint) en CI si aún no está.

---

## Veredicto


| Pregunta               | Respuesta                                                                                                                                                                                             |
| ---------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **¿Listo para merge?** | Sí, **tras** corregir la fuga del cliente HTTP (hallazgo crítico #1).                                                                                                                                 |
| **Razonamiento**       | La arquitectura hexagonal es coherente, los tests pasan y el código está ordenado. El único bloqueante operativo claro es el cliente HTTP sin cerrar; el resto son mejoras o deuda técnica manejable. |


---

## Referencias en el repo

- Especificación: `docs/superpowers/specs/2026-05-04-hexagonal-skeleton-design.md`
- Este documento: `docs/code-reviews/pr-1-hexagonal-skeleton-code-review.md`

