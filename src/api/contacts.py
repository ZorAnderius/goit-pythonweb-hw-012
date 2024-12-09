from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, status,HTTPException, Query
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

@router.get("/",
            response_model=List[ContactsResponse],
            response_description="List of all contacts")
async def get_contacts(skip: Optional[int] = Query(0, description="Pagination offset"),
                       limit: Optional[int] = Query(10, description="Pagination limit"),
                       first_name: Optional[str] = Query(None, description="Filtering by first name"),
                       last_name: Optional[str] = Query(None, description="Filtering by last name"),
                       email: Optional[str] = Query(None, description="Filtering by email"),
                       db: AsyncSession = Depends(get_db),
                       user: User = Depends(get_current_user)) -> List[Contact]:
    contacts_service = ContactsServices(db)
    contacts = await contacts_service.get_contacts(user,skip, limit, first_name, last_name, email)
    return contacts

@router.get("/weekly-birthday",
            response_model=List[ContactsResponse],
            response_description="Get contacts for weekly birthday")
async def get_contact_for_weekly_birthday(birthday_date: Optional[date] = Query(date.today(), description="Date from which to get contact's birthdays"),
                                          user: User = Depends(get_current_user),
db: AsyncSession = Depends(get_db)) -> List[Contact]:
    contacts_service = ContactsServices(db)
    contacts = await contacts_service.get_contacts_for_weekly_birthday(user, birthday_date)
    return contacts

@router.get("/{contact_id}",
            response_model=ContactsResponse,
            response_description="Get contact by id")
async def get_contact(contact_id: int,
                      db: AsyncSession = Depends(get_db),
                      user: User = Depends(get_current_user)) -> ContactsResponse:
    contacts_service = ContactsServices(db)
    contact = await contacts_service.get_contact_by_id(user, contact_id)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return contact

@router.post("/", response_model=ContactsResponse,
             status_code=status.HTTP_201_CREATED,
             response_description="Create a new contact")
async def create_contact(body: ContactsModel,
                         db: AsyncSession = Depends(get_db),
                         user: User = Depends(get_current_user)) -> Contact:
    contacts_service = ContactsServices(db)
    contact = await contacts_service.create_contact(body, user)
    return contact

@router.patch("/{contact_id}",
              response_model=ContactsResponse,
              response_description="Update contact by id")
async def update_contact(contact_id: int, body: UpdateContactModel,
                         db: AsyncSession = Depends(get_db),
                         user: User = Depends(get_current_user)) -> Contact:
    contacts_service = ContactsServices(db)
    contact = await contacts_service.update_contact(contact_id, body, user)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return contact

@router.delete("/{contact_id}",
               response_model=ContactsResponse,
               response_description="Delete contact by id")
async def delete_contact(contact_id: int,
                         db: AsyncSession = Depends(get_db),
                         user: User = Depends(get_current_user)):
    contacts_service = ContactsServices(db)
    contact = await contacts_service.delete_contact(contact_id, user)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return contact