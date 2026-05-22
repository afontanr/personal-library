from abc import ABC, abstractmethod


class CoverResolver(ABC):
    @abstractmethod
    async def resolve(self, isbn_13: str) -> str | None:
        """Resolve a cover image URL for the given ISBN-13.

        Returns the URL string if found, None otherwise.
        """
