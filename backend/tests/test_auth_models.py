from datetime import timedelta

from sqlalchemy import select

from app.models import RefreshToken, User
from app.utils.datetime import utc_now


async def test_auth_models_persist_public_uuid_and_relationship(async_session_factory) -> None:
    async with async_session_factory() as session:
        user = User(username="keeper", password_hash="hashed")
        session.add(user)
        await session.flush()
        session.add(
            RefreshToken(
                user_id=user.id,
                token_hash="token-hash",
                expires_at=utc_now() + timedelta(days=1),
            )
        )
        await session.commit()
        result = await session.execute(select(User).where(User.username == "keeper"))
        stored_user = result.scalar_one()
        assert stored_user.id > 0
        assert stored_user.uuid is not None
        assert stored_user.password_hash == "hashed"
