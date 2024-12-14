from datetime import datetime, timedelta
from unittest.mock import patch, AsyncMock, MagicMock

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import User, UserRole
from src.schemas import ContactsResponse, UserResponse
from src.services.auth import create_access_token
from tests.conftest import test_contact

test_user = {'username':"agent007",
             'email':"agent007@gmail.com",
             'hashed_password':"12345678",}

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
def sample_contact():
    return ContactsResponse(id=1,
                         first_name="John",
                         last_name="Doe",
                         email="john.doe@example.com",
                         phone="1234567890",
                         dob= test_contact['dob'])

@pytest.fixture
def updated_contact():
    return ContactsResponse(id=1,
                         first_name="Jane",
                         last_name="Smith",
                         email="john.doe@example.com",
                         phone="1234567890",
                         dob= test_contact['dob'])

@pytest_asyncio.fixture()
async def get_token():
    token = await create_access_token(data={"sub": test_user['username'], "id": 1})
    return token


@pytest.fixture
def mock_db():
    return MagicMock(spec=AsyncSession)

@pytest.mark.asyncio
async def test_get_contacts_no_filters(client, monkeypatch, mock_user, sample_contact, get_token):
    mock_redis_client = AsyncMock()
    mock_redis_client.get.return_value = None
    mock_redis_client.set.return_value = True
    monkeypatch.setattr("src.services.auth.get_redis_variable", AsyncMock(return_value=mock_redis_client))

    with patch("src.services.auth.get_current_user", return_value=mock_user):
        with patch("src.services.contacts.ContactsServices.get_contacts", return_value=[sample_contact]):
            response = client.get(
                "/api/contacts/",
                headers={"Authorization": f"Bearer {get_token}"}
            )

            assert response.status_code == 200
            assert response.json() == [
                {
                    "id": 1,
                    "first_name": test_contact['first_name'],
                    "last_name": test_contact['last_name'],
                    "email": test_contact['email'],
                    "phone": test_contact['phone'],
                    "dob": test_contact['dob'].isoformat(),
                },
            ]


@pytest.mark.asyncio
async def test_get_contacts_for_weekly_birthday(client, monkeypatch, mock_user, sample_contact, get_token, mock_db):
    mock_redis_client = AsyncMock()
    mock_redis_client.get.return_value = None
    mock_redis_client.set.return_value = True
    monkeypatch.setattr("src.services.auth.get_redis_variable", AsyncMock(return_value=mock_redis_client))

    with patch("src.services.auth.get_current_user", return_value=mock_user):
        with patch("src.services.contacts.ContactsServices.get_contacts_for_weekly_birthday", return_value=[sample_contact]):
            response = client.get(
                "api/contacts/weekly-birthday",
                headers={"Authorization": f"Bearer {get_token}"}
            )

        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["first_name"] == test_contact['first_name']


@pytest.mark.asyncio
async def test_get_contact_success(client, monkeypatch, mock_user, sample_contact, get_token, mock_db):
    mock_redis_client = AsyncMock()
    mock_redis_client.get.return_value = None
    mock_redis_client.set.return_value = True
    monkeypatch.setattr("src.services.auth.get_redis_variable", AsyncMock(return_value=mock_redis_client))

    with patch("src.services.auth.get_current_user", return_value=mock_user):
        with patch("src.services.contacts.ContactsServices.get_contact_by_id", return_value=sample_contact):
            response = client.get(
                "api/contacts/1",
                headers={"Authorization": f"Bearer {get_token}"}
            )

        assert response.status_code == 200
        assert response.json() == {
            "id": 1,
            "first_name": test_contact['first_name'],
            "last_name": test_contact['last_name'],
            "email": test_contact['email'],
            "phone": test_contact['phone'],
            "dob": test_contact['dob'].isoformat(),
        }

@pytest.mark.asyncio
async def test_get_contact_not_found(client, monkeypatch, mock_user, get_token, mock_db):
    mock_redis_client = AsyncMock()
    mock_redis_client.get.return_value = None
    mock_redis_client.set.return_value = True
    monkeypatch.setattr("src.services.auth.get_redis_variable", AsyncMock(return_value=mock_redis_client))

    with patch("src.services.auth.get_current_user", return_value=mock_user):
        with patch("src.services.contacts.ContactsServices.get_contact_by_id", return_value=None):
            response = client.get(
                "api/contacts/999",
                headers={"Authorization": f"Bearer {get_token}"}
            )

        assert response.status_code == 404
        assert response.json() == {"detail": "Contact not found"}


@pytest.mark.asyncio
async def test_create_contact_success(client, monkeypatch, mock_user, get_token):
    new_contact_data = {
        "first_name": "Jane",
        "last_name": "Doe",
        "email": "jane.doe@example.com",
        "phone": "9876543210",
        "dob": "1990-05-01"
    }

    mock_redis_client = AsyncMock()
    mock_redis_client.get.return_value = None
    mock_redis_client.set.return_value = True
    monkeypatch.setattr("src.services.auth.get_redis_variable", AsyncMock(return_value=mock_redis_client))

    with patch("src.services.auth.get_current_user", return_value=mock_user):
        with patch("src.services.contacts.ContactsServices.create_contact") as mock_create_contact:
            mock_create_contact.return_value = {**new_contact_data, "id": 1}

            response = client.post(
                "api/contacts/",
                json=new_contact_data,
                headers={"Authorization": f"Bearer {get_token}"}
            )

        assert response.status_code == 201
        assert response.json() == {**new_contact_data, "id": 1}

@pytest.mark.asyncio
async def test_update_contact_success(client, monkeypatch, mock_user, get_token, updated_contact):
    updated_contact_data = {
        "first_name": "Jane",
        "last_name": "Smith"
    }

    mock_redis_client = AsyncMock()
    mock_redis_client.get.return_value = None
    mock_redis_client.set.return_value = True
    monkeypatch.setattr("src.services.auth.get_redis_variable", AsyncMock(return_value=mock_redis_client))

    with patch("src.services.auth.get_current_user", return_value=mock_user):
        with patch("src.services.contacts.ContactsServices.update_contact") as mock_update_contact:
            mock_update_contact.return_value = updated_contact

            response = client.patch(
                "/api/contacts/1",
                json=updated_contact_data,
                headers={"Authorization": f"Bearer {get_token}"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data['first_name'] == updated_contact_data['first_name']
        assert data['last_name'] == updated_contact_data['last_name']
        assert data['id'] == 1
        assert data['email'] == test_contact['email']
        assert data['phone'] == test_contact['phone']
        assert data['dob'] == test_contact['dob'].isoformat()

@pytest.mark.asyncio
async def test_update_contact_not_found(client, monkeypatch, mock_user, get_token):
    updated_contact_data = {
        "first_name": "Jane",
        "last_name": "Smith",
    }

    mock_redis_client = AsyncMock()
    mock_redis_client.get.return_value = None
    mock_redis_client.set.return_value = True
    monkeypatch.setattr("src.services.auth.get_redis_variable", AsyncMock(return_value=mock_redis_client))

    with patch("src.services.auth.get_current_user", return_value=mock_user):
        with patch("src.services.contacts.ContactsServices.update_contact") as mock_update_contact:
            mock_update_contact.return_value = None

            response = client.patch(
                "/api/contacts/999",
                json=updated_contact_data,
                headers={"Authorization": f"Bearer {get_token}"}
            )

            assert response.status_code == 404
            assert response.json() == {"detail": "Contact not found"}

@pytest.mark.asyncio
async def test_update_contact_invalid_data(client, monkeypatch, mock_user, get_token):
    invalid_contact_data = {
        "last_name": "",
        "email": "",
    }

    mock_redis_client = AsyncMock()
    mock_redis_client.get.return_value = None
    mock_redis_client.set.return_value = True
    monkeypatch.setattr("src.services.auth.get_redis_variable", AsyncMock(return_value=mock_redis_client))

    with patch("src.services.auth.get_current_user", return_value=mock_user):
        with patch("src.services.contacts.ContactsServices.update_contact") as mock_update_contact:
            mock_update_contact.return_value = None

            response = client.patch(
                "/api/contacts/1",
                json=invalid_contact_data,
                headers={"Authorization": f"Bearer {get_token}"}
            )

            assert response.status_code == 422

@pytest.mark.asyncio
async def test_delete_contact_success(client, monkeypatch, mock_user, sample_contact, get_token):
    contact_id_to_delete = 1

    mock_redis_client = AsyncMock()
    mock_redis_client.get.return_value = None
    monkeypatch.setattr("src.services.auth.get_redis_variable", AsyncMock(return_value=mock_redis_client))

    with patch("src.services.auth.get_current_user", return_value=mock_user):
        with patch("src.services.contacts.ContactsServices.delete_contact") as mock_delete_contact:
            mock_delete_contact.return_value = sample_contact
            response = client.delete(
                f"/api/contacts/{contact_id_to_delete}",
                headers={"Authorization": f"Bearer {get_token}"}
            )

            assert response.status_code == 200
            expected_response = {**sample_contact.model_dump(), "dob": sample_contact.dob.strftime('%Y-%m-%d')}
            assert response.json() == expected_response

@pytest.mark.asyncio
async def test_delete_contact_not_found(client, monkeypatch, mock_user, get_token):
    contact_id_to_delete = 999
    mock_redis_client = AsyncMock()
    mock_redis_client.get.return_value = None
    monkeypatch.setattr("src.services.auth.get_redis_variable", AsyncMock(return_value=mock_redis_client))

    with patch("src.services.auth.get_current_user", return_value=mock_user):
        with patch("src.services.contacts.ContactsServices.delete_contact") as mock_delete_contact:
            mock_delete_contact.return_value = None

            response = client.delete(
                f"/api/contacts/{contact_id_to_delete}",
                headers={"Authorization": f"Bearer {get_token}"}
            )

            assert response.status_code == 404
            assert response.json() == {"detail": "Contact not found"}
