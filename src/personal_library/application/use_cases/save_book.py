from dataclasses import dataclass, field
from datetime import UTC, datetime

from personal_library.domain.model.collection_book import (
    CollectionBook,
    ReadingPeriod,
)
from personal_library.domain.ports.collection_repository import CollectionRepository


@dataclass
class SaveBookInput:
    @dataclass
    class ReadingPeriodInput:
        start_date: str | None = None
        end_date: str | None = None

    isbn_13: str
    title: str
    authors: list[str]
    isbn_10: str | None = None
    description: str | None = None
    published_date: str | None = None
    cover_image_url: str | None = None
    status: str = "new"
    rating: float | None = None
    tags: list[str] = field(default_factory=list)
    opinion: str | None = None
    reading_periods: list[ReadingPeriodInput] = field(default_factory=list)


class SaveBookToCollection:
    def __init__(self, collection_repository: CollectionRepository) -> None:
        self._collection_repository = collection_repository

    async def execute(self, book_input: SaveBookInput) -> CollectionBook:
        reading_periods = [
            ReadingPeriod(start_date=rp.start_date, end_date=rp.end_date)
            for rp in book_input.reading_periods
        ]

        book = CollectionBook(
            isbn_13=book_input.isbn_13,
            isbn_10=book_input.isbn_10,
            title=book_input.title,
            authors=book_input.authors,
            description=book_input.description,
            published_date=book_input.published_date,
            cover_image_url=book_input.cover_image_url,
            status=book_input.status,
            rating=book_input.rating,
            tags=book_input.tags,
            opinion=book_input.opinion,
            added_at=datetime.now(UTC).isoformat(),
            reading_periods=reading_periods,
        )

        await self._collection_repository.save(book)
        return book
