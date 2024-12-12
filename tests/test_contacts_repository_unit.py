import sys
import os
import pytest

from datetime import datetime, date
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import dialect

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from src.schemas import ContactsModel, UpdateContactModel
from src.database.models import User, UserRole, Contact
from src.repository.contacts import ContactsRepository


@pytest.fixture
def mock_session():
    mock_session = AsyncMock(spec=AsyncSession)
    return mock_session

@pytest.fixture
def contacts_repository(mock_session):
    return ContactsRepository(mock_session)

@pytest.fixture
def user():
    return User(id=1,
                username="John Doe",
                email="john@example.com",
                hashed_password="password123",
                confirmed=True,
                role=UserRole.USER)

@pytest.fixture
def contact(user):
    return Contact (id=1,
                  first_name="Nick",
                  last_name="Wayne",
                  email="wayne@example.com",
                  phone="1234567890",
                  dob=datetime(1990, 1, 1),
                  user=user)

@pytest.fixture
def contact_model(user):
    return ContactsModel( first_name="Nick",
                  last_name="Wayne",
                  email="wayne@example.com",
                  phone="1234567890",
                  dob=datetime(1990, 1, 1),
                  user=user)

@pytest.fixture
def update_model(user):
    return UpdateContactModel( first_name="John",
                  phone="2234567890",
                  dob=datetime(1992, 2, 2),)

@pytest.mark.asyncio
async def test_get_contacts(contacts_repository, mock_session, user, contact):
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [contact]
    mock_session.execute = AsyncMock(return_value=mock_result)


    contacts = await contacts_repository.get_contacts(user, 0, 10)

    assert len(contacts) == 1
    assert contacts[0].email == 'wayne@example.com'
    assert contacts[0].first_name == 'Nick'
    assert contacts[0].last_name == 'Wayne'
    assert contacts[0].phone == '1234567890'
    assert contacts[0].dob == datetime(1990, 1, 1)

    mock_session.execute.assert_called_once()

@pytest.mark.asyncio
async def test_get_contacts_with_multiple_filters(contacts_repository, mock_session, user, contact):
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [contact]
    mock_session.execute = AsyncMock(return_value=mock_result)

    result = await contacts_repository.get_contacts(
        user=user, first_name="Nick", last_name="Doe", email="test@example.com"
    )

    assert mock_session.execute.await_count == 1
    executed_query = mock_session.execute.await_args.args[0]
    sql_query = str(executed_query.compile(dialect=dialect())).lower()
    assert "ilike" in sql_query

    params = executed_query.compile().params
    assert params["first_name_1"] == "%Nick%"
    assert params["last_name_1"] == "%Doe%"
    assert params["email_1"] == "%test@example.com%"

    assert result == [contact]


@pytest.mark.asyncio
async def test_get_contact_by_id(contacts_repository, mock_session, user, contact):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = contact
    mock_session.execute = AsyncMock(return_value=mock_result)

    result = await contacts_repository.get_contact_by_id(user, contact.id)

    assert result.email == 'wayne@example.com'
    assert result.first_name == 'Nick'
    assert result.last_name == 'Wayne'
    assert result.phone == '1234567890'
    assert result.dob == datetime(1990, 1, 1)

    mock_session.execute.assert_called_once()

@pytest.mark.asyncio
async def test_create_contact(contacts_repository, mock_session, user, contact_model,contact):
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock()
    mock_session.add = MagicMock()
    mock_session.execute = AsyncMock(
        return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=contact))
    )

    result = await contacts_repository.create_contact(contact_model, user)

    assert isinstance(result, Contact)
    assert result.first_name == contact.first_name
    assert result.last_name == contact.last_name
    assert result.email == contact.email
    assert result.phone == contact.phone
    assert result.dob == contact.dob.date()

    mock_session.add.assert_called_once()
    mock_session.commit.assert_awaited_once()
    mock_session.refresh.assert_awaited_once_with(result)

@pytest.mark.asyncio
async def test_update_contact(contacts_repository, mock_session, user, contact, update_model):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = contact
    mock_session.execute = AsyncMock(return_value=mock_result)

    result = await contacts_repository.update_contact(contact_id=1, body=update_model, user=user)

    mock_session.commit.assert_called_once()
    mock_session.refresh.assert_called_once_with(contact)

    assert result is not None
    assert result.email == 'wayne@example.com'
    assert result.first_name == 'John'
    assert result.last_name == 'Wayne'
    assert result.phone == '2234567890'
    assert result.dob == date(1992, 2, 2)

    mock_session.commit.assert_awaited_once()
    mock_session.refresh.assert_awaited_once_with(contact)

@pytest.mark.asyncio
async def test_delete_contact(contacts_repository, mock_session, user, contact):
    contacts_repository.get_contact_by_id = AsyncMock(return_value=contact)

    mock_session.delete = AsyncMock()
    mock_session.commit = AsyncMock()

    result = await contacts_repository.delete_contact(contact_id=1, user=user)

    contacts_repository.get_contact_by_id.assert_called_once_with(user, contact.id)

    mock_session.delete.assert_called_once_with(contact)
    mock_session.commit.assert_awaited_once()

    assert result == contact


@pytest.mark.asyncio
async def test_delete_contact_not_found(contacts_repository, mock_session, user):
    contacts_repository.get_contact_by_id = AsyncMock(return_value=None)

    result = await contacts_repository.delete_contact(contact_id=999, user=user)

    contacts_repository.get_contact_by_id.assert_called_once_with(user, 999)

    mock_session.delete.assert_not_called()
    mock_session.commit.assert_not_called()

    assert result is None

@pytest.mark.asyncio
async def test_birthdays_in_current_month(mock_session, user):
    birthday_date = date(2024, 5, 20)
    contacts = [
        Contact(
            id=1,
            first_name="Nick",
            last_name="Wayne",
            email="nick@example.com",
            phone="1234567890",
            dob=datetime(1990, 5, 21),
            user=user
        ),
        Contact(
            id=2,
            first_name="Jane",
            last_name="Doe",
            email="jane@example.com",
            phone="0987654321",
            dob=datetime(1985, 5, 25),
            user=user
        ),
    ]

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = contacts
    mock_session.execute = AsyncMock(return_value=mock_result)

    repository = ContactsRepository(mock_session)
    result = await repository.get_contacts_for_weekly_birthday(user, birthday_date)

    assert result == contacts
    mock_session.execute.assert_called_once()

@pytest.mark.asyncio
async def test_birthdays_crossing_month_boundary(mock_session, user):
    birthday_date = date(2024, 12, 28)
    contacts = [
        Contact(
            id=1,
            first_name="Nick",
            last_name="Wayne",
            email="nick@example.com",
            phone="1234567890",
            dob=datetime(1990, 12, 29),
            user=user
        ),
        Contact(
            id=2,
            first_name="Alice",
            last_name="Smith",
            email="alice@example.com",
            phone="5555555555",
            dob=datetime(1985, 1, 2),
            user=user
        ),
    ]

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = contacts
    mock_session.execute = AsyncMock(return_value=mock_result)

    repository = ContactsRepository(mock_session)
    result = await repository.get_contacts_for_weekly_birthday(user, birthday_date)

    assert result == contacts
    mock_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_birthdays_crossing_year_boundary(mock_session, user):
    birthday_date = date(2024, 12, 30)
    contacts = [
        Contact(
            id=1,
            first_name="Nick",
            last_name="Wayne",
            email="nick@example.com",
            phone="1234567890",
            dob=datetime(1990, 12, 31),
            user=user
        ),
        Contact(
            id=2,
            first_name="Bob",
            last_name="Brown",
            email="bob@example.com",
            phone="7777777777",
            dob=datetime(1985, 1, 3),
            user=user
        ),
    ]

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = contacts
    mock_session.execute = AsyncMock(return_value=mock_result)

    repository = ContactsRepository(mock_session)
    result = await repository.get_contacts_for_weekly_birthday(user, birthday_date)

    assert result == contacts
    mock_session.execute.assert_called_once()

@pytest.mark.asyncio
async def test_no_birthdays(mock_session, user):
    birthday_date = date(2024, 6, 10)

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_session.execute = AsyncMock(return_value=mock_result)

    repository = ContactsRepository(mock_session)
    result = await repository.get_contacts_for_weekly_birthday(user, birthday_date)

    assert result == []
    mock_session.execute.assert_called_once()


