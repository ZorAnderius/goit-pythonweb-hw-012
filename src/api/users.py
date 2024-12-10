"""
User Management Endpoints.

This module provides endpoints for managing user data, including fetching the current user
and updating user avatars. It includes rate limiting for specific operations.
"""

from typing import Union

from fastapi import APIRouter, Depends, Request, UploadFile, File, HTTPException, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession

from src.conf.config import settings
from src.database.db import get_db
from src.database.models import User, UserRole
from src.schemas import UserResponse
from src.services.auth import get_current_user
from src.services.upload_file import UploadFileService
from src.services.users import UserService

router = APIRouter(prefix="/users", tags=["user"])
limiter = Limiter(key_func=get_remote_address)

@router.get(
    '/me',
    response_description="Get current user info (no more than 10 requests per minute)"
)
@limiter.limit("10/minute")
async def get_current_user(request: Request, user: UserResponse = Depends(get_current_user)) -> UserResponse:
    """
    Retrieve information about the currently authenticated user.

    :param request: The incoming HTTP request.
    :param user: The currently authenticated user (dependency).
    :return: Details of the current user.
    """
    return user

@router.patch(
    "/avatar",
    response_model=UserResponse,
    response_description="Update user's avatar"
)
async def update_avatar_user(
    file: UploadFile = File(),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """
    Update the avatar for the current user. Only admins are allowed to update the default avatar.

    :param file: The uploaded avatar file.
    :param user: The currently authenticated user (dependency).
    :param db: Database session dependency.
    :return: Updated user details with the new avatar URL.
    :raises HTTPException: If the user is not an admin.
    """
    if user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin can update the default avatar"
        )
    avatar_url = UploadFileService(
        settings.CLOUDINARY_CLOUD_NAME,
        settings.CLOUDINARY_API_KEY,
        settings.CLOUDINARY_API_SECRET
    ).upload_file(file, user.username)

    user_service = UserService(db)
    user = await user_service.update_avatar_url(user.email, avatar_url)

    return user
