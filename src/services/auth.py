"""
This module provides utilities for authentication, token creation, password hashing, 
and user validation in the FastAPI application.

It includes:
- Password hashing and verification functionality.
- JWT token generation and validation.
- Functions to get the current authenticated user and ensure the user has admin privileges.
"""

import json
from datetime import datetime, timedelta, UTC
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from src.conf.config import settings
from src.conf.redis_config import get_redis_variable
from src.database.db import get_db
from src.database.models import User
from src.schemas import UserResponse
from src.services.users import UserService


class Hash:
    """
    Provides utilities for password hashing and verification.

    Attributes:
        pwd_context (CryptContext): Context for bcrypt password hashing.
    """

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verifies if the plain password matches the hashed password.

        Args:
            plain_password (str): The plain password to verify.
            hashed_password (str): The hashed password to compare against.

        Returns:
            bool: True if passwords match, otherwise False.
        """
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """
        Hashes the plain password.

        Args:
            password (str): The plain password to hash.

        Returns:
            str: The hashed password.
        """
        return self.pwd_context.hash(password)


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

async def create_access_token(data: dict, expires_delta: Optional[int] = None) -> str:
    """
    Creates a JWT access token.

    Args:
        data (dict): The payload data to include in the token.
        expires_delta (Optional[int], optional): The expiration time in seconds. Defaults to None.

    Returns:
        str: The generated JWT token.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + timedelta(seconds=expires_delta)
    else:
        expire_minutes = int(settings.JWT_EXPIRATION_TIME)
        expire = datetime.now(UTC) + timedelta(seconds=expire_minutes)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


async def get_current_user(
        token: str = Depends(oauth2_scheme),
        db: Session = Depends(get_db)
) -> User:
    """
    Retrieves the current user from the JWT token.

    Args:
        token (str): The JWT token of the authenticated user.
        db (Session): The database session for querying users.

    Raises:
        HTTPException: If the token is invalid or the user does not exist.

    Returns:
        User: The authenticated user.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )

        username = payload.get("sub")
        user_id = payload.get("id")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    redis_client = await get_redis_variable()
    user_cache = await redis_client.get(f"user:{user_id}")
    if user_cache:
        return User(**json.loads(user_cache))

    user_service = UserService(db)
    user = await user_service.get_user_by_username(username)
    if user is None:
        raise credentials_exception

    user_response = UserResponse.model_validate(user)
    await redis_client.set(f"user:{user.id}",
                           user_response.model_dump_json(),
                           ex=500)

    return user


def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Ensures that the current user has admin privileges.

    Args:
        current_user (User): The current authenticated user.

    Raises:
        HTTPException: If the user is not an admin.

    Returns:
        User: The current user if they have admin privileges.
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can perform this action",
        )
    return current_user


def create_email_token(data: dict) -> str:
    """
    Creates a JWT token for email verification.

    Args:
        data (dict): The payload data to include in the email token.

    Returns:
        str: The generated email verification token.
    """
    to_encode = data.copy()
    expire = datetime.now(UTC) + timedelta(days=7)
    to_encode.update({"iat": datetime.now(UTC), "exp": expire})
    token = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return token


async def get_email_from_token(token: str) -> str:
    """
    Extracts the email from the email verification token.

    Args:
        token (str): The JWT email verification token.

    Raises:
        HTTPException: If the token is invalid.

    Returns:
        str: The email extracted from the token.
    """
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        email = payload["sub"]
        return email
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid token",
        )
