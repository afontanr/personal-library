import asyncio
import logging

import httpx

from personal_library.domain.exceptions import BookNotFoundError, BookRepositoryError
from personal_library.domain.model.book import BookInfo
from personal_library.domain.ports.book_repository import BookRepository
from personal_library.infrastructure.config.settings import Settings

logger = logging.getLogger(__name__)


class GoogleBooksClient(BookRepository):
    def __init__(self, http_client: httpx.AsyncClient, settings: Settings) -> None:
        self._http_client = http_client
        self._settings = settings

    async def find_by_isbn(self, isbn_13: str) -> BookInfo:
        url = f"{self._settings.google_books_base_url}/volumes"
        params: dict[str, str] = {"q": f"isbn:{isbn_13}"}
        if self._settings.google_books_api_key:
            params["key"] = self._settings.google_books_api_key

        for attempt in range(3):
            try:
                response = await self._http_client.get(
                    url,
                    params=params,
                    timeout=self._settings.http_timeout,
                )
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code == 429 and attempt < 2:
                    delay = 2 ** attempt
                    logger.info(
                        "Google Books rate limited for ISBN %s, "
                        "retrying in %ds (attempt %d/3)",
                        isbn_13, delay, attempt + 1,
                    )
                    await asyncio.sleep(delay)
                    continue
                raise BookRepositoryError(
                    f"Google Books API returned {exc.response.status_code}"
                ) from exc
            except httpx.HTTPError as exc:
                raise BookRepositoryError(
                    f"Google Books API request failed: {exc}"
                ) from exc
            else:
                break

        data = response.json()

        if data.get("totalItems", 0) == 0 or "items" not in data:
            raise BookNotFoundError(isbn_13)

        volume = data["items"][0]["volumeInfo"]
        isbn_10 = self._extract_identifier(volume, "ISBN_10")
        cover_url = (
            f"{self._settings.amazon_image_base_url}/{isbn_10}.jpg"
            if isbn_10
            else None
        )

        return BookInfo(
            isbn_13=isbn_13,
            isbn_10=isbn_10,
            title=volume.get("title", ""),
            authors=volume.get("authors", []),
            description=volume.get("description"),
            published_date=volume.get("publishedDate"),
            cover_image_url=cover_url,
        )

    @staticmethod
    def _extract_identifier(volume_info: dict, identifier_type: str) -> str | None:
        for identifier in volume_info.get("industryIdentifiers", []):
            if identifier.get("type") == identifier_type:
                return identifier.get("identifier")
        return None
