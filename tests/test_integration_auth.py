from unittest import mock
from unittest.mock import AsyncMock, MagicMock
import pytest
from fastapi import BackgroundTasks, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

import src.conf.MESSAGES as messages
from src.api.auth import create_user
from src.database.models import UserRole, User
from src.schemas import CreateUser
from src.services.auth import Hash

@pytest.fixture
def mock_db():
    return MagicMock(spec=AsyncSession)

user_data = {"username": "agent007",
             "email": "agent007@gmail.com",
             "password": "12345678"}

@pytest.fixture
def simple_user():
    return User(id=1,
                username="agent007",
                email="agent007@gmail.com",
                hashed_password="12345678",
                avatar="http://example.com/avatar.png",
                confirmed=True,
                role=UserRole.USER)

def user_unconfirmed():
    return User(id=1,
                username="agent007",
                email="agent007@gmail.com",
                hashed_password="12345678",
                avatar="http://example.com/avatar2.png",
                confirmed=False,
                role=UserRole.USER)

@pytest.fixture
def admin_user():
    return User(id=1,
                username="agent007",
                email="agent007@gmail.com",
                hashed_password="12345678",
                avatar="http://cloudinary.com/avatar.png",
                confirmed=True,
                role=UserRole.ADMIN)

def test_signup(client, monkeypatch, simple_user):
    mock_send_email = MagicMock()
    monkeypatch.setattr("src.api.auth.send_email", mock_send_email)

    mock_create_user = AsyncMock()
    mock_create_user.return_value = simple_user
    monkeypatch.setattr("src.api.auth.create_user", mock_create_user)

    response = client.post("api/auth/register", json=user_data)

    mock_create_user.assert_called_once_with(
        CreateUser(username='agent007', email='agent007@gmail.com', password='12345678'),
        mock.ANY,
        mock.ANY,
        UserRole.USER,
        mock.ANY
    )

    assert response.status_code == 201, response.text
    data = response.json()

    assert data["username"] == user_data["username"]
    assert data["email"] == user_data["email"]
    assert "hashed_password" not in data
    assert "avatar" in data

def test_create_admin_user(client, monkeypatch, admin_user):
    mock_send_email = MagicMock()
    monkeypatch.setattr("src.api.auth.send_email", mock_send_email)

    mock_create_user = AsyncMock()
    mock_create_user.return_value = admin_user
    monkeypatch.setattr("src.api.auth.create_user", mock_create_user)

    response = client.post("api/auth/register/admin", json=user_data)

    mock_create_user.assert_called_once_with(
        CreateUser(username='agent007', email='agent007@gmail.com', password='12345678'),
        mock.ANY,
        mock.ANY,
        UserRole.ADMIN,
        mock.ANY
    )

    assert response.status_code == 201, response.text
    data = response.json()

    assert data["username"] == user_data["username"]
    assert data["email"] == user_data["email"]
    assert "hashed_password" not in data
    assert "avatar" in data


@pytest.mark.asyncio
async def test_create_user(client, monkeypatch, mock_db, simple_user):
    mock_send_email = MagicMock()
    monkeypatch.setattr("src.api.auth.send_email", mock_send_email)

    mock_user_service = AsyncMock()
    mock_user_service.get_user_by_email = AsyncMock(return_value=None)
    mock_user_service.get_user_by_username = AsyncMock(return_value=None)
    mock_user_service.create_user = AsyncMock(return_value=simple_user)
    monkeypatch.setattr("src.api.auth.UserService", lambda db: mock_user_service)

    mock_hash = MagicMock()
    monkeypatch.setattr(Hash, "get_password_hash", mock_hash)
    mock_hash.return_value = "12345678"

    background_tasks = BackgroundTasks()

    new_user = await create_user(
        CreateUser(username="agent007", email="agent007@gmail.com", password="12345678"),
        background_tasks,
        request=MagicMock(),
        user_role=UserRole.USER,
        db=mock_db
    )

    mock_user_service.get_user_by_email.assert_called_once_with("agent007@gmail.com")

    mock_user_service.get_user_by_username.assert_awaited_once_with("agent007")

    mock_user_service.create_user.assert_awaited_once_with(
        CreateUser(username="agent007", email="agent007@gmail.com", password="12345678"),
        UserRole.USER
    )

    background_tasks.add_task(mock_send_email, ("agent007@gmail.com", "agent007", "mock_base_url"))
    mock_hash.assert_called_once_with("12345678")

    assert new_user.username == user_data["username"]
    assert new_user.email == user_data["email"]
    assert new_user.hashed_password == user_data["password"]
    assert new_user.role == UserRole.USER
    assert new_user.confirmed is True


@pytest.mark.asyncio
async def test_create_user_email_exists(client, monkeypatch, mock_db, simple_user):
    mock_user_service = AsyncMock()
    mock_user_service.get_user_by_email = AsyncMock(return_value=simple_user)
    monkeypatch.setattr("src.api.auth.UserService", lambda db: mock_user_service)

    background_tasks = BackgroundTasks()

    with pytest.raises(HTTPException) as exc_info:
        await create_user(
            CreateUser(username="new_user", email="agent007@gmail.com", password="12345678"),
            background_tasks,
            request=MagicMock(),
            user_role=UserRole.USER,
            db=mock_db
        )

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == messages.USER_EMAIL_EXISTS


@pytest.mark.asyncio
async def test_create_user_username_exists(client, monkeypatch, mock_db, simple_user):
    mock_user_service = AsyncMock()
    mock_user_service.get_user_by_email = AsyncMock(return_value=None)
    mock_user_service.get_user_by_username = AsyncMock(return_value=simple_user)
    monkeypatch.setattr("src.api.auth.UserService", lambda db: mock_user_service)

    background_tasks = BackgroundTasks()
    mock_db = MagicMock(AsyncSession)

    with pytest.raises(HTTPException) as exc_info:
        await create_user(
            CreateUser(username="agent007", email="new_user@gmail.com", password="12345678"),
            background_tasks,
            request=MagicMock(),
            user_role=UserRole.USER,
            db=mock_db
        )

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == messages.USERNAME_EXISTS



def test_not_confirmed_login(client):
    response = client.post("api/auth/login",
                           data={"username": user_data.get("username"), "password": user_data.get("password")})
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == "Електронна адреса не підтверджена"
#
# @pytest.mark.asyncio
# async def test_login(client):
#     async with TestingSessionLocal() as session:
#         current_user = await session.execute(select(User).where(User.email == user_data.get("email")))
#         current_user = current_user.scalar_one_or_none()
#         if current_user:
#             current_user.confirmed = True
#             await session.commit()
#
#     response = client.post("api/auth/login",
#                            data={"username": user_data.get("username"), "password": user_data.get("password")})
#     assert response.status_code == 200, response.text
#     data = response.json()
#     assert "access_token" in data
#     assert "token_type" in data
#
# def test_wrong_password_login(client):
#     response = client.post("api/auth/login",
#                            data={"username": user_data.get("username"), "password": "password"})
#     assert response.status_code == 401, response.text
#     data = response.json()
#     assert data["detail"] == "Неправильний логін або пароль"
#
# def test_wrong_username_login(client):
#     response = client.post("api/auth/login",
#                            data={"username": "username", "password": user_data.get("password")})
#     assert response.status_code == 401, response.text
#     data = response.json()
#     assert data["detail"] == "Неправильний логін або пароль"
#
# def test_validation_error_login(client):
#     response = client.post("api/auth/login",
#                            data={"password": user_data.get("password")})
#     assert response.status_code == 422, response.text
#     data = response.json()
#     assert "detail" in data

