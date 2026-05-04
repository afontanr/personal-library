from dataclasses import FrozenInstanceError

import pytest

from personal_library.domain.model.book import BookInfo


def test_book_info_creation():
    book = BookInfo(
        isbn_13="9788466341172",
        isbn_10="846634117X",
        title="Medio Mundo / Half the World",
        authors=["Joe Abercrombie"],
        description="Una novela de fantasía",
        published_date="2026-05-19",
        cover_image_url="https://images-na.ssl-images-amazon.com/images/P/846634117X.jpg",
    )
    assert book.isbn_13 == "9788466341172"
    assert book.isbn_10 == "846634117X"
    assert book.title == "Medio Mundo / Half the World"
    assert book.authors == ["Joe Abercrombie"]
    assert book.description == "Una novela de fantasía"
    assert book.published_date == "2026-05-19"
    assert (
        book.cover_image_url
        == "https://images-na.ssl-images-amazon.com/images/P/846634117X.jpg"
    )


def test_book_info_is_immutable():
    book = BookInfo(
        isbn_13="9788466341172",
        isbn_10="846634117X",
        title="Medio Mundo",
        authors=["Joe Abercrombie"],
        description="Desc",
        published_date="2026-05-19",
        cover_image_url="https://example.com/img.jpg",
    )
    with pytest.raises(FrozenInstanceError):
        book.title = "Otro título"


def test_book_info_optional_fields():
    book = BookInfo(
        isbn_13="9788466341172",
        isbn_10=None,
        title="Medio Mundo",
        authors=["Joe Abercrombie"],
        description=None,
        published_date=None,
        cover_image_url=None,
    )
    assert book.isbn_10 is None
    assert book.description is None
    assert book.published_date is None
    assert book.cover_image_url is None
