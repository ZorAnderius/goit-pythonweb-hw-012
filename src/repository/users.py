from pydantic import EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import User
from src.schemas import CreateUser


class UsersRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user_by_id(self, user_id: int) -> User | None:
        query = select(User).filter_by(id = user_id)
        user = await self.session.execute(query)
        return user.scalar_one_or_none()

    async def get_user_by_username(self, username: str) -> User | None:
        query = select(User).filter_by(username=username)
        user = await self.session.execute(query)
        return user.scalar_one_or_none()

    async def get_user_by_email(self, email: EmailStr | str) -> User | None:
        query = select(User).filter_by(email=email)
        user = await self.session.execute(query)
        return user.scalar_one_or_none()

    async def create_user(self, body: CreateUser, avatar: str = None) -> User:
        user = User(
            **body.model_dump(exclude_unset=True, exclude={'password'}),
            hashed_password=body.password,
            avatar=avatar
        )
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return  user

    async def confirmed_email(self, email: EmailStr | str) -> None:
        user = await self.get_user_by_email(email)
        user.confirmed = True
        await self.session.commit()

    async def update_avatar_url(self, email: EmailStr | str, url: str) -> User:
        user = await self.get_user_by_email(email)
        user.avatar = url
        await self.session.commit()
        await self.session.refresh(user)
        return user