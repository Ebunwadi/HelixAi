from fastapi import APIRouter, Depends

from helix_api.modules.auth.dependencies import get_current_context
from helix_api.modules.auth.schemas import CurrentContext, CurrentContextResponse

router = APIRouter(tags=["auth"])


@router.get("/me", response_model=CurrentContextResponse)
async def get_me(context: CurrentContext = Depends(get_current_context)) -> CurrentContextResponse:
    return CurrentContextResponse(
        user_id=context.user_id,
        tenant_id=context.tenant_id,
        role=context.role,
        email=context.email,
        display_name=context.display_name,
        tenant_name=context.tenant_name,
        tenant_slug=context.tenant_slug,
    )
