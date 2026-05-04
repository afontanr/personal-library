from dataclasses import dataclass


@dataclass(frozen=True)
class BookInfo:
    isbn_13: str
    isbn_10: str | None
    title: str
    authors: list[str]
    description: str | None
    published_date: str | None
    cover_image_url: str | None
