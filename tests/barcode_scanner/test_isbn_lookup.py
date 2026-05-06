import httpx

from personal_library.barcode_scanner.isbn_lookup import (
    lookup_book_for_scan,
    normalize_isbn_for_api,
)


def test_normalize_strips_hyphens_isbn13():
    assert normalize_isbn_for_api("978-84-663-4117-2") == "9788466341172"


def test_normalize_accepts_plain_isbn13():
    assert normalize_isbn_for_api("9788466341172") == "9788466341172"


def test_normalize_accepts_isbn10_uppercase_x():
    assert normalize_isbn_for_api("846634117X") == "846634117X"


def test_normalize_lowercase_x_to_uppercase():
    assert normalize_isbn_for_api("846634117x") == "846634117X"


def test_normalize_rejects_non_isbn():
    assert normalize_isbn_for_api("ABC-001") is None
    assert normalize_isbn_for_api("123") is None


def _client_with_json(status: int, payload: dict) -> httpx.Client:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status, json=payload)

    transport = httpx.MockTransport(handler)
    return httpx.Client(transport=transport, base_url="http://test")


def test_lookup_success_returns_payload():
    body = {
        "isbn_13": "9788466341172",
        "isbn_10": "846634117X",
        "title": "Medio Mundo",
        "authors": ["Joe Abercrombie"],
        "description": "Desc",
        "published_date": "2026-05-19",
        "cover_image_url": "https://example.com/cover.jpg",
    }
    client = _client_with_json(200, body)

    data, err = lookup_book_for_scan("9788466341172", "http://test", client)

    assert err is None
    assert data == body


def test_lookup_invalid_isbn_no_request():
    def handler(request: httpx.Request) -> httpx.Response:
        raise AssertionError("no HTTP call expected")

    transport = httpx.MockTransport(handler)
    client = httpx.Client(transport=transport, base_url="http://test")

    data, err = lookup_book_for_scan("not-isbn", "http://test", client)

    assert data is None
    assert "ISBN" in err


def test_lookup_404_message():
    client = _client_with_json(404, {"detail": "Book not found"})

    data, err = lookup_book_for_scan("9788466341172", "http://test", client)

    assert data is None
    assert err is not None


def test_lookup_502_message():
    client = _client_with_json(502, {"detail": "Upstream service error"})

    data, err = lookup_book_for_scan("9788466341172", "http://test", client)

    assert data is None
    assert err is not None
