from dataclasses import dataclass, field


@dataclass(frozen=True)
class ReadingPeriod:
    start_date: str | None = None
    end_date: str | None = None


@dataclass(frozen=True)
class CollectionBook:
    isbn_13: str
    title: str
    authors: list[str]
    added_at: str
    isbn_10: str | None = None
    description: str | None = None
    published_date: str | None = None
    cover_image_url: str | None = None
    status: str = "new"
    rating: float | None = None
    tags: list[str] = field(default_factory=list)
    opinion: str | None = None
    reading_periods: list[ReadingPeriod] = field(default_factory=list)
