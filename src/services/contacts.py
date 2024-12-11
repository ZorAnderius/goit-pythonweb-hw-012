"""
This module provides services for managing contacts within the FastAPI application.

It includes:
- Operations to create, update, delete, and retrieve contacts.
- Handling of integrity errors during contact creation.
"""

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import date

from src.database.models import Contact, User
from src.repository.contacts import ContactsRepository
from src.schemas import ContactsModel, UpdateContactModel


def _handle_integrity_error(e: IntegrityError):
    """
    Handles IntegrityErrors raised during database operations, particularly for unique constraint violations.

    Args:
        e (IntegrityError): The IntegrityError raised during the database operation.

    Raises:
        HTTPException: If the error is related to a unique constraint violation, raises a 409 Conflict error.
        HTTPException: For other integrity errors, raises a 400 Bad Request error.
    """
    if "unique_tag_user" in str(e.orig):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Contact with this tag already exists for this user",
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bad request. Invalid data",
        )


class ContactsServices:
    """
    Service class for managing contacts. It provides business logic for handling contact-related operations,
    such as creating, updating, retrieving, and deleting contacts.

    Args:
        db (AsyncSession): The database session used to interact with the database.

    Attributes:
        repository (ContactsRepository): The repository for accessing contact data.
    """

    def __init__(self, db: AsyncSession):
        """
        Initializes the ContactsServices instance with the provided database session.

        Args:
            db (AsyncSession): The database session for performing queries and transactions.
        """
        self.repository = ContactsRepository(db)

    async def get_contacts(self,
                           user: User,
                           skip: Optional[int] = 0,
                           limit: Optional[int] = 10,
                           first_name: Optional[str] = None,
                           last_name: Optional[str] = None,
                           email: Optional[str] = None) -> List[Contact]:
        """
        Retrieves contacts for a specific user with optional filters for first name, last name, and email.

        Args:
            user (User): The user whose contacts are to be retrieved.
            skip (Optional[int], optional): The number of records to skip for pagination. Defaults to 0.
            limit (Optional[int], optional): The maximum number of records to return. Defaults to 10.
            first_name (Optional[str], optional): The first name filter for contacts.
            last_name (Optional[str], optional): The last name filter for contacts.
            email (Optional[str], optional): The email filter for contacts.

        Returns:
            List[Contact]: A list of contacts matching the given filters.
        """
        return await self.repository.get_contacts(user, skip, limit, first_name, last_name, email)

    async def get_contact_by_id(self, user: User, contact_id: int):
        """
        Retrieves a specific contact by its ID for a given user.

        Args:
            user (User): The user to whom the contact belongs.
            contact_id (int): The ID of the contact to retrieve.

        Returns:
            Contact: The contact corresponding to the provided ID, or None if not found.
        """
        return await self.repository.get_contact_by_id(user, contact_id)

    async def create_contact(self, body: ContactsModel, user: User) -> Contact:
        """
        Creates a new contact for a given user based on the provided data model.

        Args:
            body (ContactsModel): The data model containing contact details.
            user (User): The user for whom the contact is being created.

        Returns:
            Contact: The created contact object.

        Raises:
            HTTPException: If there is an IntegrityError (e.g., unique constraint violation), an HTTP error is raised.
        """
        try:
            return await self.repository.create_contact(body, user)
        except IntegrityError as e:
            await self.repository.session.rollback()
            _handle_integrity_error(e)

    async def update_contact(self, contact_id: int, body: UpdateContactModel, user: User) -> Contact:
        """
        Updates an existing contact for a specific user.

        Args:
            contact_id (int): The ID of the contact to update.
            body (UpdateContactModel): The updated contact details.
            user (User): The user who owns the contact.

        Returns:
            Contact: The updated contact object.
        """
        return await self.repository.update_contact(contact_id, body, user)

    async def delete_contact(self, contact_id: int, user: User):
        """
        Deletes a contact for a specific user.

        Args:
            contact_id (int): The ID of the contact to delete.
            user (User): The user who owns the contact.

        Returns:
            Contact: The deleted contact object.
        """
        return await self.repository.delete_contact(contact_id, user)

    async def get_contacts_for_weekly_birthday(self, user: User, birthday_date: Optional[date]) -> List[Contact]:
        """
        Retrieves contacts with birthdays in the upcoming week.

        Args:
            user (User): The user whose contacts' birthdays are being checked.
            birthday_date (Optional[date]): The date from which to calculate the upcoming week.

        Returns:
            List[Contact]: A list of contacts whose birthdays fall within the next week.
        """
        return await self.repository.get_contacts_for_weekly_birthday(user, birthday_date)