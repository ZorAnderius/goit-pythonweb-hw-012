"""
Contacts Management Endpoints.

This module provides endpoints for managing user contacts, including creating, updating,
deleting, and retrieving contacts, as well as fetching contacts with upcoming birthdays.
"""

from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, status, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.users import get_current_user
from src.database.db import get_db
from src.database.models import Contact, User
from src.schemas import ContactsResponse, UpdateContactModel, ContactsModel
from src.services.contacts import ContactsServices

router = APIRouter(
    prefix="/contacts",
    tags=["contacts"],
    responses={404: {"description": "Not found"}},
)

@router.get(
    "/",
    response_model=List[ContactsResponse],
    response_description="List of all contacts"
)
async def get_contacts(skip: Optional[int] = Query(0, description="Pagination offset"),
                       limit: Optional[int] = Query(10, description="Pagination limit"),
                       first_name: Optional[str] = Query(None, description="Filtering by first name"),
                       last_name: Optional[str] = Query(None, description="Filtering by last name"),
                       email: Optional[str] = Query(None, description="Filtering by email"),
                       db: AsyncSession = Depends(get_db),
                       user: User = Depends(get_current_user)) -> List[Contact]:
    """
    Retrieve a list of all contacts with optional filters and pagination.

    :param skip: Number of contacts to skip for pagination.
    :param limit: Maximum number of contacts to retrieve.
    :param first_name: Filter contacts by first name.
    :param last_name: Filter contacts by last name.
    :param email: Filter contacts by email.
    :param db: Database session dependency.
    :param user: Current authenticated user.
    :return: List of contacts.
    """
    contacts_service = ContactsServices(db)
    contacts = await contacts_service.get_contacts(user, skip, limit, first_name, last_name, email)
    return contacts

@router.get(
    "/weekly-birthday",
    response_model=List[ContactsResponse],
    response_description="Get contacts for weekly birthday"
)
async def get_contact_for_weekly_birthday(birthday_date: Optional[date] = Query(date.today(), description="Date from which to get contact's birthdays"),
                                          user: User = Depends(get_current_user),
                                          db: AsyncSession = Depends(get_db)) -> List[Contact]:
    """
    Retrieve a list of contacts with birthdays in the upcoming week.

    :param birthday_date: Date to calculate upcoming birthdays (default: today).
    :param user: Current authenticated user.
    :param db: Database session dependency.
    :return: List of contacts with upcoming birthdays.
    """
    contacts_service = ContactsServices(db)
    contacts = await contacts_service.get_contacts_for_weekly_birthday(user, birthday_date)
    return contacts

@router.get(
    "/{contact_id}",
    response_model=ContactsResponse,
    response_description="Get contact by id"
)
async def get_contact(contact_id: int,
                      db: AsyncSession = Depends(get_db),
                      user: User = Depends(get_current_user)) -> ContactsResponse:
    """
    Retrieve a contact by its ID.

    :param contact_id: ID of the contact to retrieve.
    :param db: Database session dependency.
    :param user: Current authenticated user.
    :return: Contact details.
    :raises HTTPException: If the contact is not found.
    """
    contacts_service = ContactsServices(db)
    contact = await contacts_service.get_contact_by_id(user, contact_id)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return contact

@router.post(
    "/",
    response_model=ContactsResponse,
    status_code=status.HTTP_201_CREATED,
    response_description="Create a new contact"
)
async def create_contact(body: ContactsModel,
                         db: AsyncSession = Depends(get_db),
                         user: User = Depends(get_current_user)) -> Contact:
    """
    Create a new contact for the current user.

    :param body: Data for the new contact.
    :param db: Database session dependency.
    :param user: Current authenticated user.
    :return: Newly created contact.
    """
    contacts_service = ContactsServices(db)
    contact = await contacts_service.create_contact(body, user)
    return contact

@router.patch(
    "/{contact_id}",
    response_model=ContactsResponse,
    response_description="Update contact by id"
)
async def update_contact(contact_id: int,
                         body: UpdateContactModel,
                         db: AsyncSession = Depends(get_db),
                         user: User = Depends(get_current_user)) -> Contact:
    """
    Update an existing contact by its ID.

    :param contact_id: ID of the contact to update.
    :param body: Updated data for the contact.
    :param db: Database session dependency.
    :param user: Current authenticated user.
    :return: Updated contact details.
    :raises HTTPException: If the contact is not found.
    """
    contacts_service = ContactsServices(db)
    contact = await contacts_service.update_contact(contact_id, body, user)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return contact

@router.delete(
    "/{contact_id}",
    response_model=ContactsResponse,
    response_description="Delete contact by id"
)
async def delete_contact(contact_id: int,
                         db: AsyncSession = Depends(get_db),
                         user: User = Depends(get_current_user)):
    """
    Delete a contact by its ID.

    :param contact_id: ID of the contact to delete.
    :param db: Database session dependency.
    :param user: Current authenticated user.
    :return: Deleted contact details.
    :raises HTTPException: If the contact is not found.
    """
    contacts_service = ContactsServices(db)
    contact = await contacts_service.delete_contact(contact_id, user)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return contact
