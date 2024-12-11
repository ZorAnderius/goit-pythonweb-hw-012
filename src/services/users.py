"""
This module provides the UserService which contains various methods for handling user-related operations,
such as creating users, retrieving user data by different identifiers, confirming email, and updating user data.

Dependencies:
- libgravatar: Used for fetching Gravatar images based on the user's email.
- pydantic: Provides validation for user data.
- sqlalchemy: ORM used for interacting with the database.
"""

from libgravatar import Gravatar
from pydantic import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import User, UserRole
from src.repository.users import UsersRepository
from src.schemas import CreateUser


class UserService:
    """
    Service for handling user-related operations.

    Attributes:
        repository (UsersRepository): The repository used to interact with the database for user data.

    Methods:
        create_user: Creates a new user with an optional role and avatar.
        get_user_by_id: Retrieves a user by their ID.
        get_user_by_username: Retrieves a user by their username.
        get_user_by_email: Retrieves a user by their email address.
        confirmed_email: Marks a user's email as confirmed.
        update_avatar_url: Updates the avatar URL of a user.
        update_password: Updates the password of a user.
    """

    def __init__(self, db: AsyncSession):
        """
        Initializes the UserService with the provided database session.

        Args:
            db (AsyncSession): The database session used for interacting with the user repository.
        """
        self.repository = UsersRepository(db)

    async def create_user(self, body: CreateUser, role: UserRole = UserRole.USER) -> User:
        """
        Creates a new user, optionally generating an avatar using Gravatar.

        Args:
            body (CreateUser): The user data required to create a new user.
            role (UserRole, optional): The role assigned to the user. Defaults to UserRole.USER.

        Returns:
            User: The newly created user.

        This method tries to fetch a Gravatar image based on the user's email.
        If successful, the avatar is assigned to the user.
        If an error occurs while fetching the Gravatar image, no avatar is set.
        """
        avatar = None
        try:
            g = Gravatar(body.email)
            avatar = g.get_image()
        except Exception as e:
            # Log the error if Gravatar fetch fails
            print(e)
        return await self.repository.create_user(body, role, avatar)

    async def get_user_by_id(self, user_id: int) -> User | None:
        """
        Retrieves a user by their ID.

        Args:
            user_id (int): The ID of the user to retrieve.

        Returns:
            User | None: The user if found, or None if no user with the given ID exists.
        """
        return await self.repository.get_user_by_id(user_id)

    async def get_user_by_username(self, username: str) -> User | None:
        """
        Retrieves a user by their username.

        Args:
            username (str): The username of the user to retrieve.

        Returns:
            User | None: The user if found, or None if no user with the given username exists.
        """
        return await self.repository.get_user_by_username(username)

    async def get_user_by_email(self, email: EmailStr | str) -> User | None:
        """
        Retrieves a user by their email address.

        Args:
            email (EmailStr | str): The email of the user to retrieve.

        Returns:
            User | None: The user if found, or None if no user with the given email exists.
        """
        return await self.repository.get_user_by_email(email)

    async def confirmed_email(self, email: str):
        """
        Marks a user's email as confirmed.

        Args:
            email (str): The email address of the user whose email is to be confirmed.

        Returns:
            None: This method performs the update in the repository, marking the email as confirmed.
        """
        return await self.repository.confirmed_email(email)

    async def update_avatar_url(self, email: str, url: str):
        """
        Updates the avatar URL of a user.

        Args:
            email (str): The email address of the user whose avatar URL is to be updated.
            url (str): The new avatar URL.

        Returns:
            User: The user with the updated avatar URL.
        """
        return await self.repository.update_avatar_url(email, url)

    async def update_password(self, user_id: int, password: str):
        """
        Updates the password of a user.

        Args:
            user_id (int): The ID of the user whose password is to be updated.
            password (str): The new password.

        Returns:
            User: The user with the updated password.
        """
        return await self.repository.update_user_password(user_id, password)