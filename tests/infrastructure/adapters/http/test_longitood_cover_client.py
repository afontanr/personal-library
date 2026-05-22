import httpx
import pytest

from personal_library.infrastructure.adapters.http.longitood_cover_client import (
    LongitoodCoverClient,
)
from personal_library.infrastructure.config.settings import Settings


@pytest.fixture
def settings():
    return Settings(cover_service_base_url="https://example.com")


@pytest.mark.asyncio
async def test_resolve_returns_url_on_200(httpx_mock, settings):
    httpx_mock.add_response(
        url="https://example.com/bookcover/978-8410466135",
        json={"url": "https://example-images.com/cover.jpg"},
    )

    async with httpx.AsyncClient() as client:
        resolver = LongitoodCoverClient(http_client=client, settings=settings)
        result = await resolver.resolve("9788410466135")

    assert result == "https://example-images.com/cover.jpg"


@pytest.mark.asyncio
async def test_resolve_returns_none_on_404(httpx_mock, settings):
    httpx_mock.add_response(
        url="https://example.com/bookcover/978-0000000000",
        status_code=404,
    )

    async with httpx.AsyncClient() as client:
        resolver = LongitoodCoverClient(http_client=client, settings=settings)
        result = await resolver.resolve("9780000000000")

    assert result is None


@pytest.mark.asyncio
async def test_resolve_returns_none_on_500(httpx_mock, settings):
    httpx_mock.add_response(
        url="https://example.com/bookcover/978-0000000000",
        status_code=500,
    )

    async with httpx.AsyncClient() as client:
        resolver = LongitoodCoverClient(http_client=client, settings=settings)
        result = await resolver.resolve("9780000000000")

    assert result is None


@pytest.mark.asyncio
async def test_resolve_returns_none_on_network_error(httpx_mock, settings):
    httpx_mock.add_exception(
        httpx.ConnectError("connection refused"),
        url="https://example.com/bookcover/978-0000000000",
    )

    async with httpx.AsyncClient() as client:
        resolver = LongitoodCoverClient(http_client=client, settings=settings)
        result = await resolver.resolve("9780000000000")

    assert result is None


@pytest.mark.asyncio
async def test_resolve_returns_none_on_invalid_json(httpx_mock, settings):
    httpx_mock.add_response(
        url="https://example.com/bookcover/978-0000000000",
        text="not json",
    )

    async with httpx.AsyncClient() as client:
        resolver = LongitoodCoverClient(http_client=client, settings=settings)
        result = await resolver.resolve("9780000000000")

    assert result is None


@pytest.mark.asyncio
async def test_resolve_returns_none_when_url_field_missing(httpx_mock, settings):
    httpx_mock.add_response(
        url="https://example.com/bookcover/978-0000000000",
        json={},
    )

    async with httpx.AsyncClient() as client:
        resolver = LongitoodCoverClient(http_client=client, settings=settings)
        result = await resolver.resolve("9780000000000")

    assert result is None


@pytest.mark.asyncio
async def test_resolve_returns_none_when_url_field_is_null(httpx_mock, settings):
    httpx_mock.add_response(
        url="https://example.com/bookcover/978-0000000000",
        json={"url": None},
    )

    async with httpx.AsyncClient() as client:
        resolver = LongitoodCoverClient(http_client=client, settings=settings)
        result = await resolver.resolve("9780000000000")

    assert result is None


@pytest.mark.asyncio
async def test_resolve_returns_none_when_url_is_empty(httpx_mock, settings):
    httpx_mock.add_response(
        url="https://example.com/bookcover/978-0000000000",
        json={"url": ""},
    )

    async with httpx.AsyncClient() as client:
        resolver = LongitoodCoverClient(http_client=client, settings=settings)
        result = await resolver.resolve("9780000000000")

    assert result is None


@pytest.mark.asyncio
async def test_resolve_hyphenates_isbn_after_prefix(httpx_mock, settings):
    httpx_mock.add_response(
        url="https://example.com/bookcover/978-8410466135",
        json={"url": "https://example-images.com/cover.jpg"},
    )

    async with httpx.AsyncClient() as client:
        resolver = LongitoodCoverClient(http_client=client, settings=settings)
        await resolver.resolve("9788410466135")

    requests = httpx_mock.get_requests()
    assert len(requests) == 1
    assert "978-8410466135" in str(requests[0].url)
