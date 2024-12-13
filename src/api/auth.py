"""
Authentication and Authorization Endpoints.

This module provides routes for user registration, login, email confirmation,
password reset, and related operations.
"""

from fastapi import APIRouter, status, Depends, HTTPException, BackgroundTasks, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

import src.conf.MESSAGES as messages
from src.database.db import get_db
from src.database.models import User, UserRole
from src.schemas import CreateUser, UserResponse, Token, RequestEmail, ResetPassword
from src.services.auth import Hash, create_access_token, get_email_from_token
from src.services.email import send_email, send_reset_password_email
from src.services.users import UserService

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post(
    "/register",
    response_model=UserResponse,
    response_description="Create a new user",
    status_code=status.HTTP_201_CREATED
)
async def register_user(user_data: CreateUser, background_tasks: BackgroundTasks, request: Request, db: AsyncSession = Depends(get_db)) -> User:
    """
    Register a new user.

    :param user_data: Data required to create a new user.
    :param background_tasks: Background tasks for sending confirmation email.
    :param request: Current HTTP request.
    :param db: Database session dependency.
    :return: Newly created user.
    """
    new_user = await create_user(user_data, background_tasks, request, UserRole.USER, db)
    return new_user

@router.post(
    "/register/admin",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    response_description="Create a new admin user"
)
async def create_admin_user(user_data: CreateUser, background_tasks: BackgroundTasks, request: Request, db: AsyncSession = Depends(get_db)) -> User:
    """
    Register a new admin user.

    :param user_data: Data required to create an admin user.
    :param background_tasks: Background tasks for sending confirmation email.
    :param request: Current HTTP request.
    :param db: Database session dependency.
    :return: Newly created admin user.
    """
    new_admin = await create_user(user_data, background_tasks, request, UserRole.ADMIN, db)
    return new_admin

async def create_user(user_data: CreateUser, background_tasks: BackgroundTasks, request: Request, user_role: UserRole, db: AsyncSession = Depends(get_db)) -> User:
    """
    Create a user with the specified role.

    :param user_data: Data required to create a user.
    :param background_tasks: Background tasks for sending confirmation email.
    :param request: Current HTTP request.
    :param user_role: Role of the user to be created.
    :param db: Database session dependency.
    :return: Newly created user.
    """
    user_service = UserService(db)
    email_user = await user_service.get_user_by_email(user_data.email)
    if email_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=messages.USER_EMAIL_EXISTS)
    username_user = await user_service.get_user_by_username(user_data.username)
    if username_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=messages.USERNAME_EXISTS)
    user_data.password = Hash().get_password_hash(user_data.password)

    new_user = await user_service.create_user(user_data, user_role)
    background_tasks.add_task(send_email, new_user.email, new_user.username, str(request.base_url))
    return new_user

@router.post(
    "/login",
    response_model=Token,
    response_description="Login user",
    status_code=status.HTTP_200_OK
)
async def login_user(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)) -> dict:
    """
    Authenticate a user and provide an access token.

    :param form_data: OAuth2 password request form containing username and password.
    :param db: Database session dependency.
    :return: Dictionary with access token and token type.
    """
    user_service = UserService(db)
    user = await user_service.get_user_by_username(form_data.username)
    if not user or not Hash().verify_password(form_data.password, str(user.hashed_password)):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=messages.INCORRECT_CREDENTIALS, headers={"WWW-Authenticate": "Bearer"})

    if not user.confirmed:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=messages.EMAIL_NOT_CONFIRMED, headers={"WWW-Authenticate": "Bearer"})

    access_token = await create_access_token(data={"sub": user.username, "id": user.id})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/confirmed_email/{token}", response_description="Confirm email")
async def confirmed_email(token: str, db: Session = Depends(get_db)):
    """
    Confirm a user's email using a token.

    :param token: Confirmation token.
    :param db: Database session dependency.
    :return: Success message or error details.
    """
    email = await get_email_from_token(token)
    user_service = UserService(db)
    user = await user_service.get_user_by_email(email)
    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=messages.VERIFICATION_ERROR)

    if user.confirmed:
        return {"message": "Email already confirmed"}
    await user_service.confirmed_email(email)
    return {"message": "Email confirmed"}

@router.post("/requset_email", response_description="Request email")
async def request_email(body: RequestEmail, background_tasks: BackgroundTasks, request: Request, db: Session = Depends(get_db)):
    """
    Request email confirmation to be resent.

    :param body: Request body containing the email.
    :param background_tasks: Background tasks for sending confirmation email.
    :param request: Current HTTP request.
    :param db: Database session dependency.
    :return: Message indicating the confirmation email status.
    """
    user_service = UserService(db)
    user = await user_service.get_user_by_email(body.email)

    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=messages.VERIFICATION_ERROR)
    if user.confirmed:
        return {"message": "Email already confirmed"}

    background_tasks.add_task(send_email, user.email, user.username, str(request.base_url))
    return {"message": "Check your email for confirmation"}

@router.post("/password-reset-request", response_description="Reset password")
async def password_reset_request(body: RequestEmail, background_tasks: BackgroundTasks, request: Request, db: Session = Depends(get_db)):
    """
    Request a password reset email.

    :param body: Request body containing the email.
    :param background_tasks: Background tasks for sending the reset password email.
    :param request: Current HTTP request.
    :param db: Database session dependency.
    :return: Message indicating the reset email status.
    """
    user_service = UserService(db)
    user = await user_service.get_user_by_email(body.email)

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User with this email does not exist")
    background_tasks.add_task(send_reset_password_email, user.email, user.username, str(request.base_url))
    return {"message": "Check your email for reset password"}

@router.get("/password-reset-verify/{token}", response_description="Verify reset password token")
async def password_reset_verify(token: str):
    """
    Verify the password reset token.

    :param token: Reset password token.
    :return: Message indicating token validity.
    """
    try:
        email = await get_email_from_token(token)
        return {"message": "Token is valid", "email": email, "token": token}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/reset_password", response_description="Reset password token")
async def reset_password(body: ResetPassword, db: Session = Depends(get_db)) -> dict:
    """
    Reset a user's password using a token.

    :param body: Request body containing the token and new password.
    :param db: Database session dependency.
    :return: Success message after password reset.
    """
    email = await get_email_from_token(body.token)
    user_service = UserService(db)
    user = await user_service.get_user_by_email(email)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.USER_EMAIL_EXISTS)
    hashed_password = Hash().get_password_hash(body.new_password)
    await user_service.update_password(user.id, hashed_password)
    return {"message": "Password has been successfully reset"}
