# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

Uses [uv](https://docs.astral.sh/uv/) and Python 3.11+.

```bash
uv sync --extra dev                                   # install deps (incl. pytest, ruff)
uv run uvicorn personal_library.main:app --reload     # dev server on http://localhost:8000
uv run pytest -v                                      # all tests
uv run pytest tests/application/use_cases/test_save_book.py::test_name   # single test
uv run ruff check src/ tests/                         # lint (line length 88; B008 ignored for FastAPI Depends)
```

`pytest-asyncio` runs in `asyncio_mode = "auto"`. HTTP adapters are tested with `pytest-httpx` (`httpx_mock`); API routes are tested in-process via `httpx.ASGITransport` against `create_app()`.

## Architecture

Hexagonal (ports & adapters) FastAPI app under `src/personal_library/`:

- **domain/** — frozen dataclasses (`BookInfo`, `CollectionBook`, `ReadingPeriod`), abstract ports (`BookRepository`, `CollectionRepository`, `CoverResolver`), and domain exceptions (`BookNotFoundError`, `BookRepositoryError`). No external dependencies.
- **application/use_cases/** — one class per use case with an async `execute()` (`LookupBookByIsbn`, `SaveBookToCollection`, `DeleteBookFromCollection`). `lookup_book.py` also holds the `to_isbn13` / `to_isbn10` helpers used by the web layer. Lookup normalizes to ISBN-13, fetches from Google Books, then tries the cover resolver; cover failures are swallowed and must not break lookup.
- **infrastructure/** — `GoogleBooksClient` and `LongitoodCoverClient` (httpx), `SqliteCollectionRepository` (aiosqlite), and `Settings` (pydantic-settings; fields map to env vars, e.g. `GOOGLE_BOOKS_API_KEY`, `DATABASE_PATH`).
- **presentation/** — `api/` (JSON routes under `/api/...`, Pydantic schemas) and `web/` (server-rendered Jinja2 pages `/`, `/book/{isbn}`, `/scan`, plus static JS/CSS).

### Wiring

- `main.py` `lifespan` creates the shared `httpx.AsyncClient` and a single initialized `SqliteCollectionRepository`, stored on `app.state`. The DB directory is created on startup; tables are created with `CREATE TABLE IF NOT EXISTS` (no migration tool).
- `presentation/api/dependencies.py` is the composition root: FastAPI `Depends` providers build adapters from `app.state` and inject them into use cases. Web routes reuse these same providers.
- Tests swap implementations with `app.dependency_overrides[get_collection_repository] = ...` using in-memory fakes of the ports.

### Persistence notes

- `collection_books` (keyed by `isbn_13`) plus `reading_periods` (FK with `ON DELETE CASCADE`). `authors` and `tags` are stored as JSON strings.
- `save()` is an upsert (`ON CONFLICT(isbn_13) DO UPDATE`) that preserves `added_at`. `POST /api/collection` is therefore used both to add a book and to save edits from the detail page.

### Frontend

No build step. Vanilla JS in `web/static/js/` (`app.js` for list/detail pages, `scanner.js` using vendored `html5-qrcode`) calls the JSON API with `fetch`. UI text is in Spanish.

### Docker / deployment

`Dockerfile` + `docker-compose.yml` are for running locally (DB bind-mounted from `${LIBRARY_DATA_DIR:-./data}`, container runs as `PUID:PGID`). The Raspberry Pi runs LibreELEC (no compose, no git): there the app is the `library` service of the separate `kodi-raspberrypi-mediacenter` repo (`scripts/lib.sh`), behind a `caddy` container with `tls internal` (HTTPS is required for the camera scanner). The image is built for arm64 and shipped with `scripts/deploy-pi.sh`. The app sits behind a proxy, so absolute URLs (`url_for`) rely on uvicorn `--proxy-headers` + `FORWARDED_ALLOW_IPS`. See `docs/adr/0001-despliegue-en-libreelec.md`.

## Design docs

Feature specs live in `docs/superpowers/specs/` (e.g. hexagonal skeleton, delete book); check them for intended behavior when extending those features.
