from fastapi import APIRouter

from helix_api.ai.factory import get_model_gateway
from helix_api.modules.ai.schemas import (
    InvestigationInterpretRequest,
    InvestigationInterpretResponse,
)
from helix_api.modules.ai.service import InvestigationInterpretService
from helix_api.modules.auth.dependencies import CurrentContextDependency

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/interpret-investigation", response_model=InvestigationInterpretResponse)
async def interpret_investigation(
    body: InvestigationInterpretRequest,
    _context: CurrentContextDependency,
) -> InvestigationInterpretResponse:
    return await InvestigationInterpretService(get_model_gateway()).interpret(body.text)
