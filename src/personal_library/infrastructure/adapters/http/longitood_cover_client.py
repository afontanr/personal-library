import httpx

from personal_library.domain.ports.cover_resolver import CoverResolver
from personal_library.infrastructure.config.settings import Settings


class LongitoodCoverClient(CoverResolver):
    def __init__(self, http_client: httpx.AsyncClient, settings: Settings) -> None:
        self._http_client = http_client
        self._settings = settings

    async def resolve(self, isbn_13: str) -> str | None:
        hyphenated = self._hyphenate_isbn(isbn_13)
        url = f"{self._settings.cover_service_base_url}/bookcover/{hyphenated}"

        try:
            response = await self._http_client.get(
                url,
                timeout=self._settings.http_timeout,
            )
        except httpx.HTTPError:
            return None

        if response.status_code != 200:
            return None

        try:
            data = response.json()
        except ValueError:
            return None

        url_value = data.get("url")
        if not isinstance(url_value, str) or not url_value:
            return None

        return url_value

    @staticmethod
    def _hyphenate_isbn(isbn_13: str) -> str:
        return f"{isbn_13[:3]}-{isbn_13[3:]}"
