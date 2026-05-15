from datetime import datetime, timezone

import pytest

from personal_library.application.use_cases.save_book import (
    SaveBookInput,
    SaveBookToCollection,
)
from personal_library.domain.model.collection_book import (
    CollectionBook,
    ReadingPeriod,
)
from personal_library.domain.ports.collection_repository import CollectionRepository


class FakeCollectionRepository(CollectionRepository):
    def __init__(self):
        self.saved: list[CollectionBook] = []

    async def save(self, book: CollectionBook) -> None:
        self.saved.append(book)

    async def find_by_isbn(self, isbn_13: str) -> CollectionBook | None:
        for b in self.saved:
            if b.isbn_13 == isbn_13:
                return b
        return None

    async def find_all(self) -> list[CollectionBook]:
        return list(self.saved)


@pytest.mark.asyncio
async def test_save_book_persists_collection_book():
    repo = FakeCollectionRepository()
    use_case = SaveBookToCollection(collection_repository=repo)

    book_input = SaveBookInput(
        isbn_13="9788466341172",
        isbn_10="846634117X",
        title="Medio Mundo",
        authors=["Joe Abercrombie"],
        description="Una novela.",
        published_date="2026-05-19",
        cover_image_url="https://example.com/cover.jpg",
        status="new",
        rating=4.0,
        tags=["fantasy"],
        opinion="Buenisimo.",
        reading_periods=[
            SaveBookInput.ReadingPeriodInput(
                start_date="2026-05-10",
                end_date="2026-05-15",
            ),
        ],
    )

    result = await use_case.execute(book_input)

    assert result.isbn_13 == "9788466341172"
    assert result.isbn_10 == "846634117X"
    assert result.title == "Medio Mundo"
    assert result.authors == ["Joe Abercrombie"]
    assert result.description == "Una novela."
    assert result.published_date == "2026-05-19"
    assert result.cover_image_url == "https://example.com/cover.jpg"
    assert result.status == "new"
    assert result.rating == 4.0
    assert result.tags == ["fantasy"]
    assert result.opinion == "Buenisimo."
    assert result.added_at is not None
    assert len(result.reading_periods) == 1
    assert result.reading_periods[0].start_date == "2026-05-10"
    assert result.reading_periods[0].end_date == "2026-05-15"

    assert len(repo.saved) == 1
    assert repo.saved[0].isbn_13 == "9788466341172"


@pytest.mark.asyncio
async def test_save_book_sets_added_at_to_now():
    repo = FakeCollectionRepository()
    use_case = SaveBookToCollection(collection_repository=repo)

    before = datetime.now(timezone.utc).isoformat()

    book_input = SaveBookInput(
        isbn_13="9788466341172",
        title="Medio Mundo",
        authors=["Joe Abercrombie"],
    )

    result = await use_case.execute(book_input)

    assert result.added_at >= before


@pytest.mark.asyncio
async def test_save_book_defaults_empty_fields():
    repo = FakeCollectionRepository()
    use_case = SaveBookToCollection(collection_repository=repo)

    book_input = SaveBookInput(
        isbn_13="9788466341172",
        title="Medio Mundo",
        authors=["Joe Abercrombie"],
    )

    result = await use_case.execute(book_input)

    assert result.status == "new"
    assert result.rating is None
    assert result.tags == []
    assert result.opinion is None
    assert result.reading_periods == []
    assert result.isbn_10 is None
    assert result.description is None
    assert result.published_date is None
    assert result.cover_image_url is None
