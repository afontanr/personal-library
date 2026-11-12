from personal_library.domain.model.saga import Saga
from personal_library.domain.ports.saga_repository import SagaRepository


class ListSagas:
    def __init__(self, saga_repository: SagaRepository) -> None:
        self._saga_repository = saga_repository

    async def execute(self) -> list[Saga]:
        return await self._saga_repository.find_all_sagas()
