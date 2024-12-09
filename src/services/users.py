from libgravatar import Gravatar
from pydantic import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import User, UserRole
from src.repository.users import UsersRepository
from src.schemas import CreateUser


class UserService:
    def __init__(self, db: AsyncSession):
        self.repository = UsersRepository(db)

    async def create_user(self, body: CreateUser, role: UserRole = UserRole.USER) -> User:
        avatar = None
        try:
            g = Gravatar(body.email)
            avatar = g.get_image()
        except Exception as e:
            print(e)
        return await self.repository.create_user(body, role, avatar)

    async def get_user_by_id(self, user_id: int) -> User | None:
        return await self.repository.get_user_by_id(user_id)

    async def get_user_by_username(self, username: str) -> User | None:
        return await self.repository.get_user_by_username(username)

    async def get_user_by_email(self, email: EmailStr | str) -> User | None:
        return await self.repository.get_user_by_email(email)

    async def confirmed_email(self, email: str):
        return await self.repository.confirmed_email(email)

    async def update_avatar_url(self, email: str, url: str):
        return await self.repository.update_avatar_url(email, url)