# Personal Library

A personal book collection manager — look up books by ISBN, track your reading, rate and tag them, and scan barcodes with your camera.

![Python](https://img.shields.io/badge/python-3.11+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green)
![License](https://img.shields.io/badge/license-Apache%202.0-orange)

## What it does

- **Look up** any book by its ISBN (13 or 10 digits) using the Google Books API.
- **Save** books to your personal collection stored in a local SQLite database.
- **Manage** each book with reading status, star rating, custom tags, personal opinion, and reading dates.
- **Delete** books you no longer want in your collection.
- **Scan** physical barcodes with your phone or desktop camera to quickly add books.

Everything is available through a clean web UI — no separate frontend needed.

## How it works

```
┌──────────────────────────────────────────────────┐
│                  Your Browser                     │
│  Collection list  │  Book detail  │  Barcode scan │
└──────────────────────┬───────────────────────────┘
                       │
                 FastAPI server
                       │
         ┌─────────────┼─────────────┐
         ▼             ▼             ▼
   Google Books    SQLite DB    Cover service
```

1. **Search** — Enter an ISBN on the web page. The app fetches book data (title, authors, cover, description) from Google Books.
2. **Save** — Click "Add to my collection" to store the book locally with your own metadata (status, rating, tags, opinion, reading dates).
3. **Browse** — The home page shows your entire collection with cover thumbnails. Sort by date added. Search and filter coming soon.
4. **Scan** — Use your camera to scan a barcode. The ISBN is extracted and the book is looked up automatically.

The collection lives in a single SQLite file (`data/library.db`) — portable, self-contained, no cloud dependency.

## Requirements

- Python **3.11** or later
- [uv](https://docs.astral.sh/uv/) — fast Python package manager

## Quick start

```bash
# Clone the repo
git clone <repo-url>
cd personal-library

# Install dependencies
uv sync --extra dev

# Start the server
uv run uvicorn personal_library.main:app --reload
```

Open **http://localhost:8000** in your browser.

You'll see your collection (empty at first). Use the "Add a book" button or the barcode scanner to get started.

## Web UI

### Collection (home page `/`)

Shows all your books as a grid of cover cards. Each card shows the title, authors, status, and rating. Click a card to see full details or use the menu to delete it.

### Book detail (`/book/{isbn}`)

Edit everything about a book in your collection:

| Field | Description |
|---|---|
| Title | Book title |
| Authors | Comma-separated list |
| Published date | Publication year/date |
| Status | `new`, `pending`, `reading`, `done`, `dropped`, `high_priority` |
| Rate | 1–5 star rating |
| Tags | Custom labels (e.g. `fiction`, `programming`, `history`) |
| Opinion | Your personal notes about the book |
| Reading dates | When you started and finished reading |

### Barcode scanner (`/scan`)

A browser-based scanner using `html5-qrcode`. Works on both mobile and desktop — no extra setup needed. Grant camera permission, point at a barcode, and the book appears automatically.

## Configuration

| Variable | Default | Description |
|---|---|---|
| `GOOGLE_BOOKS_API_KEY` | *(none)* | Google Books API key. Without it, the quota is low (~100 req/day). With a key: 1000 req/day. [Get one here](https://console.cloud.google.com/apis/credentials). |
| `cover_service_base_url` | `https://bookcover.longitood.com` | Cover image resolution service. |
| `database_path` | `data/library.db` | Where the SQLite database is stored. |

Set environment variables before launching:

```bash
export GOOGLE_BOOKS_API_KEY=your-key-here
uv run uvicorn personal_library.main:app --reload
```

## Project structure

```
src/personal_library/
├── domain/              # Core domain model and interfaces (no external deps)
│   ├── model/           # BookInfo, CollectionBook, ReadingPeriod
│   └── ports/           # BookRepository, CollectionRepository, CoverResolver
├── application/         # Use cases (lookup, save, delete)
├── infrastructure/      # Adapters and configuration
│   ├── adapters/http/   # GoogleBooksClient, LongitoodCoverClient
│   ├── adapters/db/     # SqliteCollectionRepository
│   └── config/          # Settings (pydantic-settings)
├── presentation/        # FastAPI routes, Jinja2 templates, static files
└── main.py              # App factory and entry point
tests/                   # Test suite (pytest)
```

The codebase follows a **hexagonal architecture** (ports & adapters). Domain logic has zero external dependencies, making it easy to test and swap out adapters.

## Development

```bash
# Run tests
uv run pytest -v

# Run linter
uv run ruff check src/ tests/

# Watch mode (auto-reload on changes)
uv run uvicorn personal_library.main:app --reload
```

### API endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/health` | Health check |
| `GET` | `/api/books/{isbn}` | Look up a book by ISBN |
| `GET` | `/api/collection` | List all books in the collection |
| `POST` | `/api/collection` | Save a book to the collection |
| `DELETE` | `/api/collection/{isbn}` | Remove a book from the collection |

## License

[Apache License 2.0](LICENSE)
