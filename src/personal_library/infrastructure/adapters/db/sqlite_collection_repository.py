import json

import aiosqlite

from personal_library.domain.model.collection_book import (
    CollectionBook,
    ReadingPeriod,
)
from personal_library.domain.model.saga import Saga, SagaMembership
from personal_library.domain.ports.collection_repository import CollectionRepository
from personal_library.domain.ports.saga_repository import SagaRepository

CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS sagas (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL,
    normalized_name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS collection_books (
    isbn_13         TEXT PRIMARY KEY,
    isbn_10         TEXT,
    title           TEXT NOT NULL,
    authors         TEXT NOT NULL,
    description     TEXT,
    published_date  TEXT,
    cover_image_url TEXT,
    status          TEXT NOT NULL DEFAULT 'new',
    rating          REAL,
    tags            TEXT,
    opinion         TEXT,
    added_at        TEXT NOT NULL,
    saga_id         INTEGER REFERENCES sagas(id),
    saga_volume     REAL
);

CREATE TABLE IF NOT EXISTS reading_periods (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    isbn_13    TEXT NOT NULL REFERENCES collection_books(isbn_13) ON DELETE CASCADE,
    start_date TEXT,
    end_date   TEXT
);
"""

DELETE_ORPHAN_SAGAS_SQL = """
DELETE FROM sagas WHERE id NOT IN
    (SELECT saga_id FROM collection_books WHERE saga_id IS NOT NULL)
"""

SELECT_BOOKS_SQL = """
SELECT collection_books.*, sagas.name AS saga_name
FROM collection_books
LEFT JOIN sagas ON sagas.id = collection_books.saga_id
"""


class SqliteCollectionRepository(CollectionRepository, SagaRepository):
    def __init__(self, database_path: str) -> None:
        self._database_path = database_path
        self._db: aiosqlite.Connection

    async def initialize(self) -> None:
        self._db = await aiosqlite.connect(self._database_path)
        self._db.row_factory = aiosqlite.Row
        await self._db.executescript(CREATE_TABLES_SQL)
        await self._db.commit()
        await self._db.execute("PRAGMA foreign_keys = ON")

    async def save(self, book: CollectionBook) -> None:
        await self._db.execute("BEGIN IMMEDIATE")
        try:
            saga_id = await self._resolve_saga_id(book.saga)
            saga_volume = book.saga.volume if book.saga else None
            await self._db.execute(
                """
                INSERT INTO collection_books
                    (isbn_13, isbn_10, title, authors, description,
                     published_date, cover_image_url, status, rating,
                     tags, opinion, added_at, saga_id, saga_volume)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(isbn_13) DO UPDATE SET
                    isbn_10 = excluded.isbn_10,
                    title = excluded.title,
                    authors = excluded.authors,
                    description = excluded.description,
                    published_date = excluded.published_date,
                    cover_image_url = excluded.cover_image_url,
                    status = excluded.status,
                    rating = excluded.rating,
                    tags = excluded.tags,
                    opinion = excluded.opinion,
                    saga_id = excluded.saga_id,
                    saga_volume = excluded.saga_volume
                """,
                (
                    book.isbn_13,
                    book.isbn_10,
                    book.title,
                    json.dumps(book.authors),
                    book.description,
                    book.published_date,
                    book.cover_image_url,
                    book.status,
                    book.rating,
                    json.dumps(book.tags),
                    book.opinion,
                    book.added_at,
                    saga_id,
                    saga_volume,
                ),
            )

            await self._db.execute(
                "DELETE FROM reading_periods WHERE isbn_13 = ?",
                (book.isbn_13,),
            )

            for period in book.reading_periods:
                await self._db.execute(
                    "INSERT INTO reading_periods"
                    " (isbn_13, start_date, end_date) VALUES (?, ?, ?)",
                    (book.isbn_13, period.start_date, period.end_date),
                )

            await self._db.execute(DELETE_ORPHAN_SAGAS_SQL)
            await self._db.commit()
        except Exception:
            await self._db.execute("ROLLBACK")
            raise

    async def delete(self, isbn_13: str) -> None:
        await self._db.execute("BEGIN IMMEDIATE")
        try:
            await self._db.execute(
                "DELETE FROM collection_books WHERE isbn_13 = ?",
                (isbn_13,),
            )
            await self._db.execute(DELETE_ORPHAN_SAGAS_SQL)
            await self._db.commit()
        except Exception:
            await self._db.execute("ROLLBACK")
            raise

    async def find_all_sagas(self) -> list[Saga]:
        cursor = await self._db.execute(
            "SELECT id, name FROM sagas ORDER BY normalized_name"
        )
        rows = await cursor.fetchall()
        return [Saga(id=row["id"], name=row["name"]) for row in rows]

    async def _resolve_saga_id(self, saga: SagaMembership | None) -> int | None:
        if saga is None:
            return None
        await self._db.execute(
            "INSERT INTO sagas (name, normalized_name) VALUES (?, ?)"
            " ON CONFLICT(normalized_name) DO NOTHING",
            (saga.name, saga.normalized_name),
        )
        cursor = await self._db.execute(
            "SELECT id FROM sagas WHERE normalized_name = ?",
            (saga.normalized_name,),
        )
        row = await cursor.fetchone()
        return row["id"]

    async def find_by_isbn(self, isbn_13: str) -> CollectionBook | None:
        cursor = await self._db.execute(
            SELECT_BOOKS_SQL + " WHERE collection_books.isbn_13 = ?",
            (isbn_13,),
        )
        row = await cursor.fetchone()
        if row is None:
            return None

        reading_periods = await self._fetch_reading_periods(isbn_13)
        return self._row_to_book(row, reading_periods)

    async def find_all(self) -> list[CollectionBook]:
        cursor = await self._db.execute(
            SELECT_BOOKS_SQL + " ORDER BY collection_books.added_at DESC"
        )
        rows = await cursor.fetchall()

        periods_cursor = await self._db.execute(
            "SELECT isbn_13, start_date, end_date FROM reading_periods"
        )
        all_periods_rows = await periods_cursor.fetchall()

        periods_by_isbn: dict[str, list[ReadingPeriod]] = {}
        for p in all_periods_rows:
            isbn = p["isbn_13"]
            if isbn not in periods_by_isbn:
                periods_by_isbn[isbn] = []
            periods_by_isbn[isbn].append(
                ReadingPeriod(start_date=p["start_date"], end_date=p["end_date"])
            )

        return [
            self._row_to_book(row, periods_by_isbn.get(row["isbn_13"], []))
            for row in rows
        ]

    async def _fetch_reading_periods(self, isbn_13: str) -> list[ReadingPeriod]:
        cursor = await self._db.execute(
            "SELECT start_date, end_date FROM reading_periods WHERE isbn_13 = ?",
            (isbn_13,),
        )
        rows = await cursor.fetchall()
        return [
            ReadingPeriod(start_date=row["start_date"], end_date=row["end_date"])
            for row in rows
        ]

    @staticmethod
    def _row_to_book(
        row: aiosqlite.Row, periods: list[ReadingPeriod]
    ) -> CollectionBook:
        return CollectionBook(
            isbn_13=row["isbn_13"],
            isbn_10=row["isbn_10"],
            title=row["title"],
            authors=json.loads(row["authors"]),
            description=row["description"],
            published_date=row["published_date"],
            cover_image_url=row["cover_image_url"],
            status=row["status"],
            rating=row["rating"],
            tags=json.loads(row["tags"]) if row["tags"] else [],
            opinion=row["opinion"],
            added_at=row["added_at"],
            reading_periods=periods,
            saga=(
                SagaMembership(
                    name=row["saga_name"],
                    volume=row["saga_volume"],
                    saga_id=row["saga_id"],
                )
                if row["saga_id"] is not None
                else None
            ),
        )

    async def close(self) -> None:
        await self._db.close()
