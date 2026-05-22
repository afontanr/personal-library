import logging

import httpx

from personal_library.domain.ports.cover_resolver import CoverResolver
from personal_library.infrastructure.config.settings import Settings

logger = logging.getLogger(__name__)


class LongitoodCoverClient(CoverResolver):
    def __init__(self, http_client: httpx.AsyncClient, settings: Settings) -> None:
        self._http_client = http_client
        self._settings = settings

    async def resolve(self, isbn_13: str) -> str | None:
        hyphenated = self._hyphenate_isbn(isbn_13)
        url = f"{self._settings.cover_service_base_url}/bookcover/{hyphenated}"

        logger.info("Resolving cover for ISBN %s via %s", isbn_13, url)

        try:
            response = await self._http_client.get(
                url,
                timeout=self._settings.http_timeout,
            )
        except httpx.HTTPError as exc:
            logger.warning(
                "Cover service unreachable for ISBN %s: %s", isbn_13, exc
            )
            return None

        if response.status_code != 200:
            logger.info(
                "Cover service returned %s for ISBN %s",
                response.status_code,
                isbn_13,
            )
            return None

        try:
            data = response.json()
        except ValueError:
            logger.warning("Cover service returned invalid JSON for ISBN %s", isbn_13)
            return None

        url_value = data.get("url")
        if not isinstance(url_value, str) or not url_value:
            logger.info("Cover service returned no URL for ISBN %s", isbn_13)
            return None

        logger.info("Cover resolved for ISBN %s: %s", isbn_13, url_value)
        return url_value

    @staticmethod
    def _hyphenate_isbn(isbn_13: str) -> str:
        return f"{isbn_13[:3]}-{isbn_13[3:]}"
