from pydantic import BaseModel


class BookInfoResponse(BaseModel):
    isbn_13: str
    isbn_10: str | None
    title: str
    authors: list[str]
    description: str | None
    published_date: str | None
    cover_image_url: str | None
