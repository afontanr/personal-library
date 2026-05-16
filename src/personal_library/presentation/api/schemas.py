from pydantic import BaseModel


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
