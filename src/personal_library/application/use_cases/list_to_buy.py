from personal_library.application.use_cases.list_collection import (
    CollectionOrder,
    sort_books,
)
from personal_library.domain.model.collection_book import CollectionBook
from personal_library.domain.ports.collection_repository import CollectionRepository


class ListToBuy:
    def __init__(self, collection_repository: CollectionRepository) -> None:
        self._collection_repository = collection_repository

    async def execute(
        self, order: CollectionOrder = CollectionOrder.DEFAULT
    ) -> list[CollectionBook]:
        books = await self._collection_repository.find_all()
        to_buy = [b for b in books if b.is_to_buy]
        return sort_books(to_buy, order)
