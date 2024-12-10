"""
Repository for managing users.

This module provides a repository class `UsersRepository` for performing CRUD operations 
on the `User` model, including retrieving users by various attributes, creating users, 
updating user information, and confirming email addresses.
"""

from pydantic import EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import User, UserRole
from src.schemas import CreateUser


class UsersRepository:
    """
    Repository class for handling `User` entities in the database.

    This class provides methods for retrieving, creating, and updating users, as well as 
    confirming user email addresses and updating user avatars.

    Attributes:
        session (AsyncSession): The database session for executing queries.
    """

    def __init__(self, session: AsyncSession):
        """
        Initializes the UsersRepository with a database session.

        Args:
            session (AsyncSession): The database session to be used for queries.
        """
        self.session = session

    async def get_user_by_id(self, user_id: int) -> User | None:
        """
        Retrieves a user by their ID.

        Args:
            user_id (int): The ID of the user to retrieve.

        Returns:
            User | None: The user with the given ID, or None if not found.
        """
        query = select(User).filter_by(id=user_id)
        user = await self.session.execute(query)
        return user.scalar_one_or_none()

    async def get_user_by_username(self, username: str) -> User | None:
        """
        Retrieves a user by their username.

        Args:
            username (str): The username of the user to retrieve.

        Returns:
            User | None: The user with the given username, or None if not found.
        """
        query = select(User).filter_by(username=username)
        user = await self.session.execute(query)
        return user.scalar_one_or_none()

    async def get_user_by_email(self, email: EmailStr | str) -> User | None:
        """
        Retrieves a user by their email address.

        Args:
            email (EmailStr | str): The email address of the user to retrieve.

        Returns:
            User | None: The user with the given email, or None if not found.
        """
        query = select(User).filter_by(email=email)
        user = await self.session.execute(query)
        return user.scalar_one_or_none()

    async def create_user(self, body: CreateUser, role: UserRole = UserRole.USER, avatar: str = None) -> User:
        """
        Creates a new user in the database.

        Args:
            body (CreateUser): The data for the new user.
            role (UserRole, optional): The role of the new user (default is `UserRole.USER`).
            avatar (str, optional): The avatar URL for the new user (default is `None`).

        Returns:
            User: The newly created user.
        """
        user = User(
            **body.model_dump(exclude_unset=True, exclude={'password'}),
            hashed_password=body.password,
            avatar=avatar,
            role=role
        )
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def confirmed_email(self, email: EmailStr | str) -> None:
        """
        Marks a user's email as confirmed.

        Args:
            email (EmailStr | str): The email address of the user to confirm.

        Returns:
            None
        """
        user = await self.get_user_by_email(email)
        user.confirmed = True
        await self.session.commit()

    async def update_avatar_url(self, email: EmailStr | str, url: str) -> User:
        """
        Updates the avatar URL for a user.

        Args:
            email (EmailStr | str): The email address of the user to update.
            url (str): The new avatar URL.

        Returns:
            User: The user with the updated avatar URL.
        """
        user = await self.get_user_by_email(email)
        user.avatar = url
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def update_user_password(self, user_id: int, password: str) -> User:
        """
        Updates the password for a user.

        Args:
            user_id (int): The ID of the user whose password is to be updated.
            password (str): The new password.

        Returns:
            User: The user with the updated password.
        """
        user = await self.get_user_by_id(user_id)
        user.hashed_password = password
        await self.session.commit()
        await self.session.refresh(user)
        return user
