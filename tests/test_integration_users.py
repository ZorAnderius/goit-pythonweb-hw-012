from unittest.mock import MagicMock, patch, AsyncMock

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import UserRole, User
from src.schemas import UserResponse
from src.services.auth import create_access_token

test_user = {'username':"agent007",
             'email':"agent007@gmail.com",
             'hashed_password':"12345678",}

new_avatar_url = "https://res.cloudinary.com/dxlahrm0m/image/upload/c_fill,h_250,w_250/v1/ContactsApp/agent007"

@pytest.fixture
def mock_user():
    return UserResponse(id=1,
                username="agent007",
                email="agent007@gmail.com",
                hashed_password="12345678",
                avatar="http://example.com/avatar.png",
                confirmed=True,
                role=UserRole.USER)

@pytest.fixture
def admin_user():
    return User(id=1,
                username="agent007",
                email="agent007@gmail.com",
                hashed_password="12345678",
                avatar="http://example.com/avatar.png",
                confirmed=True,
                role=UserRole.ADMIN)

@pytest_asyncio.fixture()
async def get_token():
    token = await create_access_token(data={"sub": test_user["username"], "id": 1})
    return token


@pytest.fixture
def mock_db():
    return MagicMock(spec=AsyncSession)

@pytest.fixture
def mock_user_service(monkeypatch):
    mock_service = AsyncMock()
    monkeypatch.setattr("src.api.auth.UserService", lambda db: mock_service)
    return mock_service


@pytest.mark.asyncio
async def test_get_current_user_success(client, monkeypatch, get_token, mock_user, mock_db):
    mock_redis_client = AsyncMock()
    mock_redis_client.get.return_value = None
    mock_redis_client.set.return_value = True
    monkeypatch.setattr("src.services.auth.get_redis_variable", AsyncMock(return_value=mock_redis_client))

    mock_payload = {"sub": test_user["username"], "id": 1}
    with patch("src.services.auth.jwt.decode", return_value=mock_payload):
        with patch('src.services.users.UserService') as MockUserService:
            mock_user_service = AsyncMock()
            mock_user_service.get_user_by_username.return_value = mock_user
            MockUserService.return_value = mock_user_service

            response = client.get(
                "/api/users/me",
                headers={"Authorization": f"Bearer {get_token}"}
            )

        assert response.status_code == 200, response.text
        data = response.json()
        assert data["username"] == mock_user.username
        assert data["email"] == mock_user.email
        assert data["id"] == mock_user.id

@pytest.mark.asyncio
async def test_update_avatar_admin(client, monkeypatch, mock_user_service, admin_user, get_token, mock_db):
    mock_redis_client = AsyncMock()
    mock_redis_client.get.return_value = None
    mock_redis_client.set.return_value = True
    monkeypatch.setattr("src.services.auth.get_redis_variable", AsyncMock(return_value=mock_redis_client))

    with patch("src.services.auth.get_current_user", return_value=admin_user):
        with patch("src.services.upload_file", return_value=new_avatar_url):
            mock_user_service.update_avatar_url.return_value = admin_user
            with patch("cloudinary.uploader.upload", return_value={
                "url": new_avatar_url}):
                file_data = {'file': ('avatar.jpg', b'\x89PNG\r\n\x1a\n...', 'image/jpeg')}
                response = client.patch("/api/users/avatar",
                                        files=file_data,
                                        headers={"Authorization": f"Bearer {get_token}"})

                assert response.status_code == 200
                assert response.json()[
                           "avatar"] == new_avatar_url