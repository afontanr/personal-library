from fastapi import APIRouter, Depends

from personal_library.application.use_cases.list_collection import CollectionOrder
from personal_library.application.use_cases.list_to_buy import ListToBuy
from personal_library.presentation.api.dependencies import get_list_to_buy_use_case
from personal_library.presentation.api.schemas import CollectionBookResponse

router = APIRouter(prefix="/api/to-buy", tags=["to-buy"])


@router.get("", response_model=list[CollectionBookResponse])
async def list_to_buy(
    orden: str | None = None,
    use_case: ListToBuy = Depends(get_list_to_buy_use_case),
) -> list[CollectionBookResponse]:
    books = await use_case.execute(CollectionOrder.from_param(orden))
    return [CollectionBookResponse.from_book(b) for b in books]
