from fastapi import APIRouter

from helix_api.modules.auth.dependencies import CurrentContextDependency
from helix_api.modules.auth.schemas import CurrentContextResponse

router = APIRouter(tags=["auth"])


@router.get("/me", response_model=CurrentContextResponse)
async def get_me(context: CurrentContextDependency) -> CurrentContextResponse:
    return CurrentContextResponse(
        user_id=context.user_id,
        tenant_id=context.tenant_id,
        role=context.role,
        email=context.email,
        display_name=context.display_name,
        tenant_name=context.tenant_name,
        tenant_slug=context.tenant_slug,
    )
