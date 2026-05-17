from personal_library.domain.exceptions import BookNotFoundError
from personal_library.domain.ports.collection_repository import CollectionRepository


class DeleteBookFromCollection:
    def __init__(self, collection_repository: CollectionRepository) -> None:
        self._collection_repository = collection_repository

    async def execute(self, isbn_13: str) -> None:
        book = await self._collection_repository.find_by_isbn(isbn_13)
        if book is None:
            raise BookNotFoundError(isbn_13)
        await self._collection_repository.delete(isbn_13)