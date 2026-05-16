import dataclasses

import pytest

from personal_library.domain.model.collection_book import (
    CollectionBook,
    ReadingPeriod,
)


def test_reading_period_defaults():
    period = ReadingPeriod()
    assert period.start_date is None
    assert period.end_date is None


def test_reading_period_with_dates():
    period = ReadingPeriod(start_date="2026-05-01", end_date="2026-05-15")
    assert period.start_date == "2026-05-01"
    assert period.end_date == "2026-05-15"


def test_reading_period_is_immutable():
    period = ReadingPeriod(start_date="2026-05-01")
    with pytest.raises(dataclasses.FrozenInstanceError):
        period.start_date = "2026-06-01"  # type: ignore


def test_collection_book_minimal_fields():
    book = CollectionBook(
        isbn_13="9788466341172",
        title="Medio Mundo",
        authors=["Joe Abercrombie"],
        added_at="2026-05-15T16:00:00",
    )
    assert book.isbn_13 == "9788466341172"
    assert book.isbn_10 is None
    assert book.title == "Medio Mundo"
    assert book.authors == ["Joe Abercrombie"]
    assert book.description is None
    assert book.published_date is None
    assert book.cover_image_url is None
    assert book.status == "new"
    assert book.rating is None
    assert book.tags == []
    assert book.opinion is None
    assert book.added_at == "2026-05-15T16:00:00"
    assert book.reading_periods == []


def test_collection_book_all_fields():
    periods = [
        ReadingPeriod(start_date="2026-01-01", end_date="2026-01-15"),
        ReadingPeriod(start_date="2026-03-01", end_date=None),
    ]
    book = CollectionBook(
        isbn_13="9788466341172",
        isbn_10="846634117X",
        title="Medio Mundo",
        authors=["Joe Abercrombie"],
        description="Una novela.",
        published_date="2026-05-19",
        cover_image_url="https://example.com/cover.jpg",
        status="reading",
        rating=4.5,
        tags=["fantasy", "epic"],
        opinion="Increible.",
        added_at="2026-05-15T16:00:00",
        reading_periods=periods,
    )
    assert book.status == "reading"
    assert book.rating == 4.5
    assert book.tags == ["fantasy", "epic"]
    assert book.opinion == "Increible."
    assert len(book.reading_periods) == 2


def test_collection_book_is_immutable():
    book = CollectionBook(
        isbn_13="9788466341172",
        title="Medio Mundo",
        authors=["Joe Abercrombie"],
        added_at="2026-05-15T16:00:00",
    )
    with pytest.raises(dataclasses.FrozenInstanceError):
        book.title = "Other"  # type: ignore
