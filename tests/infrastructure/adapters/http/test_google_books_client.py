import httpx
import pytest

from personal_library.domain.exceptions import BookNotFoundError, BookRepositoryError
from personal_library.infrastructure.adapters.http.google_books_client import (
    GoogleBooksClient,
)
from personal_library.infrastructure.config.settings import Settings

GOOGLE_BOOKS_RESPONSE = {
    "kind": "books#volumes",
    "totalItems": 1,
    "items": [
        {
            "volumeInfo": {
                "title": "Medio Mundo / Half the World",
                "authors": ["Joe Abercrombie"],
                "publishedDate": "2026-05-19",
                "description": "Una novela de fantasía épica.",
                "industryIdentifiers": [
                    {"type": "ISBN_10", "identifier": "846634117X"},
                    {"type": "ISBN_13", "identifier": "9788466341172"},
                ],
            }
        }
    ],
}

GOOGLE_BOOKS_EMPTY_RESPONSE = {
    "kind": "books#volumes",
    "totalItems": 0,
}


@pytest.mark.asyncio
async def test_find_by_isbn_returns_book_info(httpx_mock):
    settings = Settings(
        google_books_base_url="https://fake.api",
        amazon_image_base_url="https://fake.images",
    )
    httpx_mock.add_response(
        url="https://fake.api/volumes?q=isbn:9788466341172",
        json=GOOGLE_BOOKS_RESPONSE,
    )

    async with httpx.AsyncClient() as http_client:
        client = GoogleBooksClient(http_client=http_client, settings=settings)
        book = await client.find_by_isbn("9788466341172")

    assert book is not None
    assert book.isbn_13 == "9788466341172"
    assert book.isbn_10 == "846634117X"
    assert book.title == "Medio Mundo / Half the World"
    assert book.authors == ["Joe Abercrombie"]
    assert book.description == "Una novela de fantasía épica."
    assert book.published_date == "2026-05-19"
    assert book.cover_image_url == "https://fake.images/846634117X.jpg"


@pytest.mark.asyncio
async def test_find_by_isbn_raises_not_found_when_empty(httpx_mock):
    settings = Settings(
        google_books_base_url="https://fake.api",
        amazon_image_base_url="https://fake.images",
    )
    httpx_mock.add_response(
        url="https://fake.api/volumes?q=isbn:0000000000000",
        json=GOOGLE_BOOKS_EMPTY_RESPONSE,
    )

    async with httpx.AsyncClient() as http_client:
        client = GoogleBooksClient(http_client=http_client, settings=settings)
        with pytest.raises(BookNotFoundError) as exc_info:
            await client.find_by_isbn("0000000000000")

    assert exc_info.value.isbn == "0000000000000"


@pytest.mark.asyncio
async def test_find_by_isbn_handles_missing_isbn10(httpx_mock):
    response = {
        "kind": "books#volumes",
        "totalItems": 1,
        "items": [
            {
                "volumeInfo": {
                    "title": "Some Book",
                    "authors": ["Author"],
                    "publishedDate": "2024-01-01",
                    "description": "Desc",
                    "industryIdentifiers": [
                        {"type": "ISBN_13", "identifier": "9781234567890"},
                    ],
                }
            }
        ],
    }
    settings = Settings(
        google_books_base_url="https://fake.api",
        amazon_image_base_url="https://fake.images",
    )
    httpx_mock.add_response(
        url="https://fake.api/volumes?q=isbn:9781234567890",
        json=response,
    )

    async with httpx.AsyncClient() as http_client:
        client = GoogleBooksClient(http_client=http_client, settings=settings)
        book = await client.find_by_isbn("9781234567890")

    assert book is not None
    assert book.isbn_10 is None
    assert book.cover_image_url is None


@pytest.mark.asyncio
async def test_find_by_isbn_raises_repository_error_on_http_error(httpx_mock):
    settings = Settings(
        google_books_base_url="https://fake.api",
        amazon_image_base_url="https://fake.images",
    )
    httpx_mock.add_response(
        url="https://fake.api/volumes?q=isbn:9788466341172",
        status_code=500,
    )

    async with httpx.AsyncClient() as http_client:
        client = GoogleBooksClient(http_client=http_client, settings=settings)
        with pytest.raises(BookRepositoryError):
            await client.find_by_isbn("9788466341172")


@pytest.mark.asyncio
async def test_find_by_isbn_raises_repository_error_on_timeout(httpx_mock):
    settings = Settings(
        google_books_base_url="https://fake.api",
        amazon_image_base_url="https://fake.images",
    )
    httpx_mock.add_exception(
        httpx.ReadTimeout("timed out"),
        url="https://fake.api/volumes?q=isbn:9788466341172",
    )

    async with httpx.AsyncClient() as http_client:
        client = GoogleBooksClient(http_client=http_client, settings=settings)
        with pytest.raises(BookRepositoryError):
            await client.find_by_isbn("9788466341172")
