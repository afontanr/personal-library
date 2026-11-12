from httpx import ASGITransport, AsyncClient

from personal_library.domain.model.saga import Saga
from personal_library.domain.ports.saga_repository import SagaRepository
from personal_library.main import create_app
from personal_library.presentation.api.dependencies import get_saga_repository


class FakeSagaRepository(SagaRepository):
    async def find_all_sagas(self) -> list[Saga]:
        return [Saga(id=1, name="Dune")]


async def test_list_sagas_returns_id_and_name():
    app = create_app()
    app.dependency_overrides[get_saga_repository] = FakeSagaRepository
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/sagas")
    assert response.status_code == 200
    assert response.json() == [{"id": 1, "name": "Dune"}]
