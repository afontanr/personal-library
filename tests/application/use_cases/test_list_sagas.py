from personal_library.application.use_cases.list_sagas import ListSagas
from personal_library.domain.model.saga import Saga
from personal_library.domain.ports.saga_repository import SagaRepository


class FakeSagaRepository(SagaRepository):
    def __init__(self, sagas: list[Saga]):
        self._sagas = sagas

    async def find_all_sagas(self) -> list[Saga]:
        return list(self._sagas)


async def test_list_sagas_returns_repository_sagas():
    fake = FakeSagaRepository([Saga(id=1, name="Dune")])
    assert await ListSagas(saga_repository=fake).execute() == [Saga(id=1, name="Dune")]
