import sys
import os
import pytest

from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from src.schemas import CreateUser

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from src.repository.users import UsersRepository
from src.database.models import User, UserRole

@pytest.fixture
def mock_session():
    mock_session = AsyncMock(spec=AsyncSession)
    return mock_session

@pytest.fixture
def users_repository(mock_session):
    return UsersRepository(mock_session)

@pytest.fixture
def user():
    return User(id=1,
                username="John Doe",
                email="john@example.com",
                hashed_password="password123",
                avatar="http://example.com/avatar.png",
                confirmed=True,
                role=UserRole.ADMIN)
@pytest.fixture
def user_unconfirmed():
    return User(id=1,
                username="John Doe",
                email="john@example.com",
                hashed_password="password123",
                avatar="http://example.com/avatar2.png",
                confirmed=False,
                role=UserRole.USER)

@pytest.mark.asyncio
async def test_get_user_by_id(users_repository, mock_session, user):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = user
    mock_session.execute = AsyncMock(return_value=mock_result)

    result = await users_repository.get_user_by_id(user.id)

    assert result.id == user.id
    assert result.email == user.email
    assert result.username == user.username

    mock_session.execute.assert_called_once()

@pytest.mark.asyncio
async def test_get_user_by_username(users_repository, mock_session, user):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = user
    mock_session.execute = AsyncMock(return_value=mock_result)

    result = await users_repository.get_user_by_username(user.username)

    assert result.id == user.id
    assert result.email == user.email
    assert result.username == user.username

    mock_session.execute.assert_called_once()

@pytest.mark.asyncio
async def test_get_user_by_email(users_repository, mock_session, user):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = user
    mock_session.execute = AsyncMock(return_value=mock_result)

    result = await users_repository.get_user_by_email(user.email)
    assert result.id == user.id
    assert result.email == user.email
    assert result.username == user.username

    mock_session.execute.assert_called_once()

@pytest.mark.asyncio
async def test_create_user(users_repository, mock_session):
    create_user_data = CreateUser(
        email="testuser@example.com",
        username="Test User",
        password="hashedpassword123"
    )
    role = UserRole.USER
    avatar = "http://example.com/avatar11.png"

    created_user = User(
        id=1,
        email=create_user_data.email,
        username=create_user_data.username,
        hashed_password=create_user_data.password,
        role=role,
        avatar = avatar
    )

    mock_session.add = MagicMock()
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock()

    result = await users_repository.create_user(create_user_data, role, avatar)

    assert isinstance(result, User)
    assert result.email == created_user.email
    assert result.username == created_user.username
    assert result.hashed_password == created_user.hashed_password
    assert result.avatar == created_user.avatar
    assert result.role == created_user.role

    mock_session.add.assert_called_once_with(result)
    mock_session.commit.assert_awaited_once()
    mock_session.refresh.assert_awaited_once_with(result)

@pytest.mark.asyncio
async def test_confirmed_email(users_repository, mock_session, user_unconfirmed):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = user_unconfirmed
    mock_session.execute = AsyncMock(return_value=mock_result)
    mock_session.commit = AsyncMock()

    email = "testuser@example.com"

    await users_repository.confirmed_email(email)

    assert user_unconfirmed.confirmed is True

    mock_session.execute.assert_called_once()
    mock_session.commit.assert_awaited_once()

@pytest.mark.asyncio
async def test_update_avatar_url(users_repository, mock_session, user):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = user
    mock_session.execute = AsyncMock(return_value=mock_result)

    new_avatar_url = "http://cloudinary.com/avatar.png"

    result = await users_repository.update_avatar_url(user.email, new_avatar_url)

    assert result.avatar == new_avatar_url
    assert result.email == user.email

    mock_session.execute.assert_called_once()
    mock_session.commit.assert_awaited_once()
    mock_session.refresh.assert_awaited_once_with(user)

@pytest.mark.asyncio
async def test_update_user_password(users_repository, mock_session, user):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = user
    mock_session.execute = AsyncMock(return_value=mock_result)

    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock()

    user_id = user.id
    new_password = "new_secure_password"

    result = await users_repository.update_user_password(user_id, new_password)

    assert result.hashed_password == new_password
    assert result.id == user_id

    mock_session.execute.assert_called_once()
    mock_session.commit.assert_awaited_once()
    mock_session.refresh.assert_awaited_once_with(user)
