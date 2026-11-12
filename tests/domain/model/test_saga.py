import pytest

from personal_library.domain.model.collection_book import CollectionBook
from personal_library.domain.model.saga import SagaMembership


def test_membership_strips_name_and_exposes_normalized_name():
    m = SagaMembership(name="  El Señor de los Anillos ", volume=2)
    assert m.name == "El Señor de los Anillos"
    assert m.normalized_name == "el senor de los anillos"


@pytest.mark.parametrize("volume", [None, 0, 3.5])
def test_membership_accepts_valid_volumes(volume):
    assert SagaMembership(name="Dune", volume=volume).volume == volume


def test_membership_rejects_blank_name():
    with pytest.raises(ValueError):
        SagaMembership(name="   ")


def test_membership_rejects_negative_volume():
    with pytest.raises(ValueError):
        SagaMembership(name="Dune", volume=-1)


def test_collection_book_has_no_saga_by_default():
    book = CollectionBook(isbn_13="9780000000001", title="T", authors=[], added_at="x")
    assert book.saga is None
