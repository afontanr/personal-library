from dataclasses import dataclass

from personal_library.domain.model.text import normalize_text


@dataclass(frozen=True)
class Saga:
    id: int
    name: str


@dataclass(frozen=True)
class SagaMembership:
    name: str
    volume: float | None = None
    saga_id: int | None = None

    def __post_init__(self) -> None:
        name = self.name.strip()
        if not name:
            raise ValueError("Saga name must not be blank")
        if self.volume is not None and self.volume < 0:
            raise ValueError("Saga volume must be >= 0")
        object.__setattr__(self, "name", name)

    @property
    def normalized_name(self) -> str:
        return normalize_text(self.name)
