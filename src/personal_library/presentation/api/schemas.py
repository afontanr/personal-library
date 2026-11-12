from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints

from personal_library.domain.model.collection_book import CollectionBook


class BookInfoResponse(BaseModel):
    isbn_13: str
    isbn_10: str | None
    title: str
    authors: list[str]
    description: str | None
    published_date: str | None
    cover_image_url: str | None


class ReadingPeriodRequest(BaseModel):
    start_date: str | None = None
    end_date: str | None = None


class SagaRequest(BaseModel):
    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
    volume: float | None = Field(default=None, ge=0)


class SagaResponse(BaseModel):
    id: int | None
    name: str
    volume: float | None


class SagaSummaryResponse(BaseModel):
    id: int
    name: str


class SaveBookRequest(BaseModel):
    isbn_13: str
    title: str
    authors: list[str]
    isbn_10: str | None = None
    description: str | None = None
    published_date: str | None = None
    cover_image_url: str | None = None
    status: str = "new"
    rating: float | None = None
    tags: list[str] = []
    opinion: str | None = None
    reading_periods: list[ReadingPeriodRequest] = []
    saga: SagaRequest | None = None


class CollectionBookResponse(BaseModel):
    isbn_13: str
    isbn_10: str | None
    title: str
    authors: list[str]
    description: str | None
    published_date: str | None
    cover_image_url: str | None
    status: str
    rating: float | None
    tags: list[str]
    opinion: str | None
    added_at: str
    reading_periods: list[ReadingPeriodRequest]
    saga: SagaResponse | None = None

    @classmethod
    def from_book(cls, book: CollectionBook) -> "CollectionBookResponse":
        return cls(
            isbn_13=book.isbn_13,
            isbn_10=book.isbn_10,
            title=book.title,
            authors=book.authors,
            description=book.description,
            published_date=book.published_date,
            cover_image_url=book.cover_image_url,
            status=book.status,
            rating=book.rating,
            tags=book.tags,
            opinion=book.opinion,
            added_at=book.added_at,
            reading_periods=[
                ReadingPeriodRequest(start_date=rp.start_date, end_date=rp.end_date)
                for rp in book.reading_periods
            ],
            saga=(
                SagaResponse(
                    id=book.saga.saga_id, name=book.saga.name, volume=book.saga.volume
                )
                if book.saga
                else None
            ),
        )
