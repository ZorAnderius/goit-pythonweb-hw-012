from unittest import mock
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from fastapi import BackgroundTasks, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

import src.conf.MESSAGES as messages
from src.api.auth import create_user
from src.database.models import UserRole, User
from src.schemas import CreateUser
from src.services.auth import Hash, create_access_token

user_data = {"username": "agent007",
             "email": "agent007@gmail.com",
             "password": "12345678"}

wrong_user_data = {"username": "agent007",
             "email": "agent007@gmail.com",
             "password": "11111111"}

@pytest.fixture
def mock_db():
    return MagicMock(spec=AsyncSession)

@pytest.fixture
def simple_user():
    return User(id=1,
                username="agent007",
                email="agent007@gmail.com",
                hashed_password="12345678",
                avatar="http://example.com/avatar.png",
                confirmed=True,
                role=UserRole.USER)

@pytest.fixture
def unconfirmed_user():
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

@pytest.fixture
def mock_user_service(monkeypatch):
    mock_service = AsyncMock()
    monkeypatch.setattr("src.api.auth.UserService", lambda db: mock_service)
    return mock_service

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
async def test_create_user(client, monkeypatch, mock_user_service, mock_db, simple_user):
    mock_send_email = MagicMock()
    monkeypatch.setattr("src.api.auth.send_email", mock_send_email)

    mock_user_service.get_user_by_email = AsyncMock(return_value=None)
    mock_user_service.get_user_by_username = AsyncMock(return_value=None)
    mock_user_service.create_user = AsyncMock(return_value=simple_user)

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
async def test_create_user_email_exists(client, mock_user_service, mock_db, simple_user):
    mock_user_service.get_user_by_email = AsyncMock(return_value=simple_user)

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
async def test_create_user_username_exists(client, mock_user_service, mock_db, simple_user):
    mock_user_service.get_user_by_email = AsyncMock(return_value=None)
    mock_user_service.get_user_by_username = AsyncMock(return_value=simple_user)

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


@pytest.mark.asyncio
async def test_successful_login(client, mock_user_service, simple_user):
    hashed_password = Hash().get_password_hash(simple_user.hashed_password)
    simple_user.hashed_password = hashed_password

    mock_user_service.get_user_by_username.return_value = simple_user

    with patch('src.api.auth.create_access_token', return_value="mocked_access_token"):
        with patch('src.api.auth.UserService', return_value=mock_user_service):
            response = client.post(
                "/api/auth/login",
                data={"username": user_data["username"], "password": user_data["password"], "email": user_data["email"]}
            )

    assert response.status_code == 200, response.text
    data = response.json()
    assert "access_token" in data
    assert data["access_token"] == "mocked_access_token"
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_not_confirmed_login(client, mock_user_service, unconfirmed_user):
    hashed_password = Hash().get_password_hash(unconfirmed_user.hashed_password)
    unconfirmed_user.hashed_password = hashed_password

    mock_user_service.get_user_by_username.return_value =unconfirmed_user

    with patch('src.api.auth.UserService', return_value=mock_user_service):
        response = client.post(
            "/api/auth/login",
            data={"username": user_data["username"], "password": user_data["password"], "email": user_data["email"]}
        )

    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == messages.EMAIL_NOT_CONFIRMED


@pytest.mark.asyncio
async def test_invalid_credentials(client, mock_user_service, simple_user):
    hashed_password = Hash().get_password_hash(simple_user.hashed_password)
    simple_user.hashed_password = hashed_password

    mock_user_service.get_user_by_username.return_value = simple_user

    with patch('src.api.auth.UserService', return_value=mock_user_service):
        response = client.post(
            "/api/auth/login",
            data={"username": wrong_user_data["username"], "password": wrong_user_data["password"], "email": wrong_user_data["email"]}
        )

    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == messages.INCORRECT_CREDENTIALS

def test_validation_error_login(client):
    response = client.post("api/auth/login",
                           data={"password": user_data.get("password")})
    assert response.status_code == 422, response.text
    data = response.json()
    assert "detail" in data

@pytest.mark.asyncio
async def test_confirmed_email(client, mock_user_service, unconfirmed_user):
    with patch("src.api.auth.get_email_from_token", return_value=unconfirmed_user.email):
        mock_user_service.get_user_by_username = AsyncMock(return_value=unconfirmed_user)
        mock_user_service.get_user_by_email.return_value = unconfirmed_user
        mock_user_service.confirmed_email = AsyncMock(return_value=None)

        with patch("src.api.auth.UserService", return_value=mock_user_service):
            response = client.get(f"/api/auth/confirmed_email/{'mocked_token'}")


            assert response.status_code == 200
            assert response.json() == {"message": "Email confirmed"}
            mock_user_service.confirmed_email.assert_called_once_with(unconfirmed_user.email)

@pytest.mark.asyncio
async def test_email_already_confirmed(client, mock_user_service, simple_user):
    with patch("src.api.auth.get_email_from_token", return_value=simple_user.email):
        mock_user_service.get_user_by_email.return_value = simple_user

        with patch("src.api.auth.UserService", return_value=mock_user_service):
            response = client.get(f"/api/auth/confirmed_email/{'mocked_token'}")

            assert response.status_code == 200
            assert response.json() == {"message": "Email already confirmed"}

@pytest.mark.asyncio
async def test_user_not_found(client, mock_user_service):
    with patch("src.api.auth.get_email_from_token", return_value="nonexistent@example.com"):
        mock_user_service.get_user_by_email.return_value = None

        with patch("src.api.auth.UserService", return_value=mock_user_service):
            response = client.get(f"/api/auth/confirmed_email/{'mocked_token'}")

            assert response.status_code == 400
            assert response.json() == {"detail": messages.VERIFICATION_ERROR}


@pytest.mark.asyncio
async def test_request_email_user_not_found(client, mock_user_service):
    mock_user_service.get_user_by_email.return_value = None

    with patch("src.api.auth.UserService", return_value=mock_user_service):
        response = client.post(
            "/api/auth/requset_email",
            json={"email": "nonexistent@example.com"},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {"detail": messages.VERIFICATION_ERROR}


@pytest.mark.asyncio
async def test_request_email_already_confirmed(client, mock_user_service, simple_user):

    mock_user_service.get_user_by_email.return_value = simple_user

    with patch("src.api.auth.UserService", return_value=mock_user_service):
        response = client.post(
            "/api/auth/requset_email",
            json={"email": "confirmed@example.com"},
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"message": "Email already confirmed"}


@pytest.mark.asyncio
async def test_request_email_confirmation_sent(client, monkeypatch, mock_user_service, unconfirmed_user):
    mock_user_service.get_user_by_email.return_value = unconfirmed_user

    with patch("src.api.auth.UserService", return_value=mock_user_service), \
         patch("src.api.auth.send_email") as mock_send_email:
        response = client.post(
            "/api/auth/requset_email",
            json={"email": unconfirmed_user.email},
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"message": "Check your email for confirmation"}

        mock_send_email.assert_called_once_with(
            unconfirmed_user.email,
            unconfirmed_user.username,
            mock.ANY
        )

@pytest.mark.asyncio
async def test_password_reset_request_user_exists(client, mock_user_service, simple_user):
    mock_user_service.get_user_by_email.return_value = simple_user

    with patch("src.api.auth.UserService", return_value=mock_user_service), \
         patch("src.api.auth.send_reset_password_email") as mock_send_reset_email:
        response = client.post(
            "/api/auth/password-reset-request",
            json={"email": simple_user.email},
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"message": "Check your email for reset password"}

        mock_send_reset_email.assert_called_once_with(
            simple_user.email,
            simple_user.username,
            mock.ANY
        )

@pytest.mark.asyncio
async def test_password_reset_request_user_not_found(client, mock_user_service):
    mock_user_service.get_user_by_email.return_value = None

    with patch("src.api.auth.UserService", return_value=mock_user_service):
        response = client.post(
            "/api/auth/password-reset-request",
            json={"email": "nonexistent@example.com"},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json() == {"detail": "User with this email does not exist"}

@pytest.mark.asyncio
async def test_password_reset_verify_valid_token(client):
    data = {"sub": "user@example.com"}
    valid_token = await create_access_token(data, expires_delta=3600)

    with patch("src.api.auth.get_email_from_token", return_value=data["sub"]):
        response = client.get(f"/api/auth/password-reset-verify/{valid_token}")

        assert response.status_code == 200
        assert response.json() == {
            "message": "Token is valid",
            "email": data["sub"],
            "token": valid_token
        }

@pytest.mark.asyncio
async def test_password_reset_verify_invalid_token(client):
    invalid_token = "invalid_token"

    with patch("src.api.auth.get_email_from_token", side_effect=ValueError("Invalid token")):
        response = client.get(f"/api/auth/password-reset-verify/{invalid_token}")

        assert response.status_code == 400
        assert response.json() == {"detail": "Invalid token"}


@pytest.mark.asyncio
async def test_reset_password_valid_token(client, mock_user_service, simple_user):
    data = {"sub": simple_user.email}
    valid_token = await create_access_token(data, expires_delta=3600)
    new_password = "new_secure_password"

    with patch("src.api.auth.get_email_from_token", return_value=simple_user.email):
        mock_user_service.get_user_by_email.return_value = simple_user
        mock_update_password = AsyncMock()
        mock_user_service.update_password = mock_update_password

        body = {
            "token": valid_token,
            "new_password": new_password
        }

        response = client.post("/api/auth/reset_password", json=body)

        assert response.status_code == 200
        assert response.json() == {"message": "Password has been successfully reset"}

        hashed_password = Hash().get_password_hash(new_password)
        assert hashed_password != new_password
        is_valid = Hash().verify_password(new_password, hashed_password)
        assert is_valid is True
        mock_update_password.assert_called_once_with(1, mock.ANY)

        mock_user_service.get_user_by_email.assert_called_once_with(simple_user.email)


@pytest.mark.asyncio
async def test_reset_password_user_not_found(client, mock_user_service, simple_user):
    data = {"sub": simple_user.email}
    valid_token = await create_access_token(data, expires_delta=3600)
    new_password = "new_secure_password"

    with patch("src.api.auth.get_email_from_token", return_value=simple_user.email):
        mock_user_service.get_user_by_email.return_value = None

        mock_update_password = AsyncMock()
        mock_user_service.update_password = mock_update_password

        body = {
            "token": valid_token,
            "new_password": new_password
        }

        response = client.post("/api/auth/reset_password", json=body)

        assert response.status_code == 404
        assert response.json() == {"detail": messages.USER_EMAIL_EXISTS}