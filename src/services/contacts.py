from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import date

from src.database.models import Contact, User
from src.repository.contacts import ContactsRepository
from src.schemas import ContactsModel, UpdateContactModel

def _handle_integrity_error(e: IntegrityError):
    if "unique_tag_user" in str(e.orig):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail= "Contact with this tag already exists for this user",
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail= "Bad request. Invalid data",
        )

class ContactsServices:
    def __init__(self, db: AsyncSession):
        self.repository = ContactsRepository(db)

    async def get_contacts(self,
                           user: User,
                           skip: Optional[int] = 0,
                           limit: Optional[int] = 10,
                           first_name: Optional[str] = None,
                           last_name: Optional[str] = None,
                           email: Optional[str] = None) -> List[Contact]:
        return await self.repository.get_contacts(user, skip, limit, first_name, last_name, email)

    async def get_contact_by_id(self, user: User, contact_id: int):
        return await self.repository.get_contact_by_id(user, contact_id)

    async def create_contact(self, body: ContactsModel, user: User) -> Contact:
        try:
            return await self.repository.create_contact(body, user)
        except IntegrityError as e:
            await self.repository.session.rollback()
            _handle_integrity_error(e)

    async def update_contact(self, contact_id: int, body: UpdateContactModel, user: User) -> Contact:
        return await self.repository.update_contact(contact_id, body, user)

    async def delete_contact(self, contact_id: int, user: User):
        return await self.repository.delete_contact(contact_id, user)

    async def get_contacts_for_weekly_birthday(self, user: User, birthday_date: Optional[date]) -> List[Contact]:
        return await self.repository.get_contacts_for_weekly_birthday(user,birthday_date)