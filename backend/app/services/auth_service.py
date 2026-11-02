from __future__ import annotations
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.user_repository import UserRepository
from app.models.user import User
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token
from app.core.exceptions import ConflictError, UnauthorizedError, NotFoundError

class AuthService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)

    async def register(self, email: str, password: str, display_name: str | None = None) -> User:
        clean_email = email.lower().strip()
        existing = await self.user_repo.get_by_email(clean_email)
        if existing:
            raise ConflictError("A user with this email address already exists")

        pw_hash = hash_password(password)
        user = await self.user_repo.create(
            email=clean_email,
            password_hash=pw_hash,
            display_name=display_name.strip() if display_name else None
        )
        await self.session.commit()
        return user

    async def authenticate(self, email: str, password: str) -> tuple[User, str, str]:
        clean_email = email.lower().strip()
        user = await self.user_repo.get_by_email(clean_email)
        if not user or not verify_password(password, user.password_hash):
            raise UnauthorizedError("Invalid email or password")

        access_token, refresh_token = self.generate_tokens(user)
        return user, access_token, refresh_token

    async def refresh_session(self, refresh_token: str) -> tuple[User, str, str]:
        try:
            payload = decode_token(refresh_token)
            user_id_str = payload.get("sub")
            if not user_id_str:
                raise UnauthorizedError("Invalid refresh token")
            user = await self.user_repo.get_by_id(uuid.UUID(str(user_id_str)))
            if not user:
                raise UnauthorizedError("User no longer exists")
            new_access_token, new_refresh_token = self.generate_tokens(user)
            return user, new_access_token, new_refresh_token
        except Exception as e:
            if isinstance(e, UnauthorizedError):
                raise
            raise UnauthorizedError("Invalid or expired refresh token")

    def generate_tokens(self, user: User) -> tuple[str, str]:
        token_data = {"sub": str(user.id), "email": user.email}
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)
        return access_token, refresh_token

    async def get_user_by_id(self, user_id: uuid.UUID) -> User:
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")
        return user

    async def get_or_create_default_user(self) -> User:
        user = await self.user_repo.get_first_user()
        if user:
            return user
        # Auto-create local default user
        default_user = await self.user_repo.create(
            email="local@smritix.internal",
            password_hash=hash_password("smritix-local-default"),
            display_name="Local SMRITIX User"
        )
        await self.session.commit()
        return default_user
