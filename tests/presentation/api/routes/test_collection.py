import pytest
from httpx import ASGITransport, AsyncClient

from personal_library.domain.model.collection_book import (
    CollectionBook,
)
from personal_library.domain.model.saga import SagaMembership
from personal_library.domain.ports.collection_repository import CollectionRepository
from personal_library.main import create_app
from personal_library.presentation.api.dependencies import (
    get_collection_repository,
)


class FakeCollectionRepository(CollectionRepository):
    def __init__(self):
        self._books: dict[str, CollectionBook] = {}

    async def save(self, book: CollectionBook) -> None:
        self._books[book.isbn_13] = book

    async def find_by_isbn(self, isbn_13: str) -> CollectionBook | None:
        return self._books.get(isbn_13)

    async def find_all(self) -> list[CollectionBook]:
        return sorted(
            self._books.values(),
            key=lambda b: b.added_at,
            reverse=True,
        )

    async def delete(self, isbn_13: str) -> None:
        self._books.pop(isbn_13, None)


@pytest.mark.asyncio
async def test_save_book_returns_201():
    fake_repo = FakeCollectionRepository()
    app = create_app()
    app.dependency_overrides[get_collection_repository] = lambda: fake_repo

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/collection",
            json={
                "isbn_13": "9788466341172",
                "isbn_10": "846634117X",
                "title": "Medio Mundo",
                "authors": ["Joe Abercrombie"],
                "description": "Una novela.",
                "published_date": "2026-05-19",
                "cover_image_url": "https://example.com/cover.jpg",
                "status": "new",
                "rating": 4.0,
                "tags": ["fantasy"],
                "opinion": "Buenisimo.",
                "reading_periods": [
                    {"start_date": "2026-05-10", "end_date": "2026-05-15"},
                ],
            },
        )

    assert response.status_code == 201
    data = response.json()
    assert data["isbn_13"] == "9788466341172"
    assert data["isbn_10"] == "846634117X"
    assert data["title"] == "Medio Mundo"
    assert data["authors"] == ["Joe Abercrombie"]
    assert data["description"] == "Una novela."
    assert data["published_date"] == "2026-05-19"
    assert data["cover_image_url"] == "https://example.com/cover.jpg"
    assert data["status"] == "new"
    assert data["rating"] == 4.0
    assert data["tags"] == ["fantasy"]
    assert data["opinion"] == "Buenisimo."
    assert "added_at" in data
    assert len(data["reading_periods"]) == 1
    assert data["reading_periods"][0]["start_date"] == "2026-05-10"
    assert data["reading_periods"][0]["end_date"] == "2026-05-15"


@pytest.mark.asyncio
async def test_save_book_minimal_fields():
    fake_repo = FakeCollectionRepository()
    app = create_app()
    app.dependency_overrides[get_collection_repository] = lambda: fake_repo

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/collection",
            json={
                "isbn_13": "9788466341172",
                "title": "Medio Mundo",
                "authors": ["Joe Abercrombie"],
            },
        )

    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "new"
    assert data["rating"] is None
    assert data["tags"] == []
    assert data["opinion"] is None
    assert data["reading_periods"] == []


@pytest.mark.asyncio
async def test_list_collection_returns_books_ordered():
    fake_repo = FakeCollectionRepository()
    book1 = CollectionBook(
        isbn_13="9788466341172",
        isbn_10="846634117X",
        title="Medio Mundo",
        authors=["Joe Abercrombie"],
        added_at="2026-05-10T10:00:00",
    )
    book2 = CollectionBook(
        isbn_13="9780451524935",
        isbn_10="0451524934",
        title="1984",
        authors=["George Orwell"],
        added_at="2026-05-15T16:00:00",
    )
    fake_repo._books["9788466341172"] = book1
    fake_repo._books["9780451524935"] = book2

    app = create_app()
    app.dependency_overrides[get_collection_repository] = lambda: fake_repo

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/collection")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2
    assert data[0]["isbn_13"] == "9780451524935"  # most recent first
    assert data[1]["isbn_13"] == "9788466341172"


def _repo_with_borges_newer_than_allende() -> FakeCollectionRepository:
    fake_repo = FakeCollectionRepository()
    fake_repo._books["9780000000001"] = CollectionBook(
        isbn_13="9780000000001",
        title="La casa de los espíritus",
        authors=["Isabel Allende"],
        added_at="2026-05-10T10:00:00",
    )
    fake_repo._books["9780000000002"] = CollectionBook(
        isbn_13="9780000000002",
        title="Ficciones",
        authors=["Jorge Luis Borges"],
        added_at="2026-05-15T16:00:00",
    )
    return fake_repo


@pytest.mark.asyncio
async def test_list_collection_orden_autor_sorts_by_first_author():
    app = create_app()
    fake_repo = _repo_with_borges_newer_than_allende()
    app.dependency_overrides[get_collection_repository] = lambda: fake_repo

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/collection", params={"orden": "autor"})

    assert response.status_code == 200
    assert [b["authors"][0] for b in response.json()] == [
        "Isabel Allende",
        "Jorge Luis Borges",
    ]


@pytest.mark.asyncio
@pytest.mark.parametrize("orden", ["xyz", ""])
async def test_list_collection_unknown_orden_falls_back_to_default(orden):
    app = create_app()
    fake_repo = _repo_with_borges_newer_than_allende()
    app.dependency_overrides[get_collection_repository] = lambda: fake_repo

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/collection", params={"orden": orden})

    assert response.status_code == 200
    assert [b["authors"][0] for b in response.json()] == [
        "Jorge Luis Borges",
        "Isabel Allende",
    ]


@pytest.mark.asyncio
async def test_list_collection_returns_empty_array():
    fake_repo = FakeCollectionRepository()
    app = create_app()
    app.dependency_overrides[get_collection_repository] = lambda: fake_repo

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/collection")

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_delete_book_returns_204():
    fake_repo = FakeCollectionRepository()
    book = CollectionBook(
        isbn_13="9788466341172",
        isbn_10="846634117X",
        title="Medio Mundo",
        authors=["Joe Abercrombie"],
        added_at="2026-05-15T16:00:00",
    )
    await fake_repo.save(book)

    app = create_app()
    app.dependency_overrides[get_collection_repository] = lambda: fake_repo

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.delete("/api/collection/9788466341172")

    assert response.status_code == 204
    assert response.text == ""


@pytest.mark.asyncio
async def test_delete_book_returns_404_when_not_found():
    fake_repo = FakeCollectionRepository()
    app = create_app()
    app.dependency_overrides[get_collection_repository] = lambda: fake_repo

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.delete("/api/collection/0000000000000")

    assert response.status_code == 404
    assert response.json()["detail"] == "Book not found"


@pytest.mark.asyncio
async def test_delete_book_returns_422_for_invalid_isbn():
    fake_repo = FakeCollectionRepository()
    app = create_app()
    app.dependency_overrides[get_collection_repository] = lambda: fake_repo

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.delete("/api/collection/abc")

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_list_collection_excludes_to_buy_books():
    fake_repo = FakeCollectionRepository()
    fake_repo._books["9780000000001"] = CollectionBook(
        isbn_13="9780000000001",
        title="Mío",
        authors=["Ana"],
        added_at="2026-05-10T10:00:00",
    )
    fake_repo._books["9780000000002"] = CollectionBook(
        isbn_13="9780000000002",
        title="Deseado",
        authors=["Zoe"],
        added_at="2026-05-15T10:00:00",
        status="to_buy",
    )
    app = create_app()
    app.dependency_overrides[get_collection_repository] = lambda: fake_repo

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/collection")

    assert response.status_code == 200
    assert [b["isbn_13"] for b in response.json()] == ["9780000000001"]


@pytest.mark.asyncio
async def test_get_collection_book_returns_saved_book():
    fake_repo = FakeCollectionRepository()
    fake_repo._books["9780000000002"] = CollectionBook(
        isbn_13="9780000000002",
        title="Deseado",
        authors=["Zoe"],
        added_at="2026-05-15T10:00:00",
        status="to_buy",
    )
    app = create_app()
    app.dependency_overrides[get_collection_repository] = lambda: fake_repo

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/collection/9780000000002")

    assert response.status_code == 200
    assert response.json()["status"] == "to_buy"


@pytest.mark.asyncio
async def test_get_collection_book_returns_404_when_not_saved():
    app = create_app()
    fake_repo = FakeCollectionRepository()
    app.dependency_overrides[get_collection_repository] = lambda: fake_repo

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/collection/9780000000002")

    assert response.status_code == 404


# ─── Sagas ───

BASE = {"isbn_13": "9780000000001", "title": "Dune", "authors": ["Frank Herbert"]}


@pytest.fixture
async def saga_client():
    fake_repo = FakeCollectionRepository()
    app = create_app()
    app.dependency_overrides[get_collection_repository] = lambda: fake_repo
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client, fake_repo


async def test_save_book_with_saga_returns_saga(saga_client):
    client, _ = saga_client
    response = await client.post(
        "/api/collection", json={**BASE, "saga": {"name": "Dune", "volume": 1}}
    )
    assert response.status_code == 201
    assert response.json()["saga"] == {"id": None, "name": "Dune", "volume": 1.0}


async def test_save_book_without_saga_returns_null_saga(saga_client):
    client, _ = saga_client
    response = await client.post("/api/collection", json=BASE)
    assert response.json()["saga"] is None


@pytest.mark.parametrize(
    "saga",
    [{"name": "   ", "volume": 2}, {"name": "Dune", "volume": -1}, {"volume": 2}],
)
async def test_save_book_with_invalid_saga_returns_422(saga_client, saga):
    client, fake_repo = saga_client
    response = await client.post("/api/collection", json={**BASE, "saga": saga})
    assert response.status_code == 422
    assert await fake_repo.find_all() == []


async def test_list_collection_includes_saga(saga_client):
    client, fake_repo = saga_client
    await fake_repo.save(
        CollectionBook(
            **BASE,
            added_at="2026-11-12T10:00:00",
            saga=SagaMembership("Dune", 3.5, saga_id=7),
        )
    )
    response = await client.get("/api/collection")
    assert response.json()[0]["saga"] == {"id": 7, "name": "Dune", "volume": 3.5}
