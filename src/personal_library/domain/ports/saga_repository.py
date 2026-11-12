from abc import ABC, abstractmethod

from personal_library.domain.model.saga import Saga


class SagaRepository(ABC):
    @abstractmethod
    async def find_all_sagas(self) -> list[Saga]:
        """Return every saga, sorted by normalized name."""
