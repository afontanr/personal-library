from fastapi import APIRouter, Depends

from personal_library.application.use_cases.list_sagas import ListSagas
from personal_library.presentation.api.dependencies import get_list_sagas_use_case
from personal_library.presentation.api.schemas import SagaSummaryResponse

router = APIRouter(prefix="/api/sagas", tags=["sagas"])


@router.get("", response_model=list[SagaSummaryResponse])
async def list_sagas(
    use_case: ListSagas = Depends(get_list_sagas_use_case),
) -> list[SagaSummaryResponse]:
    sagas = await use_case.execute()
    return [SagaSummaryResponse(id=s.id, name=s.name) for s in sagas]
