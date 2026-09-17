from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from helix_api.modules.users.models import User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_external_identity(self, external_identity_id: str) -> User | None:
        result = await self.session.execute(
            select(User).where(User.external_identity_id == external_identity_id)
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        *,
        external_identity_id: str,
        email: str | None,
        display_name: str | None,
    ) -> User:
        user = User(
            external_identity_id=external_identity_id,
            email=email,
            display_name=display_name,
        )
        self.session.add(user)
        await self.session.flush()
        return user
