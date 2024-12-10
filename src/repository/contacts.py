"""
Repository for managing contacts.

This module provides a repository class `ContactsRepository` for performing CRUD operations
on the `Contact` model, including filtering, updating, and deleting contacts. It also includes
a method for retrieving contacts with upcoming birthdays for the next week.
"""

from typing import List, Optional
from datetime import date, timedelta
from calendar import monthrange

from sqlalchemy import select, extract, asc
from sqlalchemy.sql import and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import Contact, User
from src.schemas import ContactsModel


class ContactsRepository:
    """
    Repository class for handling `Contact` entities in the database.

    This class provides methods for retrieving, creating, updating, and deleting contacts
    in relation to a specific user, and for querying contacts with upcoming birthdays.

    Attributes:
        session (AsyncSession): The database session for executing queries.
    """

    def __init__(self, session: AsyncSession):
        """
        Initializes the ContactsRepository with a database session.

        Args:
            session (AsyncSession): The database session to be used for queries.
        """
        self.session = session

    async def get_contacts(self,
                           user: User,
                           skip: Optional[int] = 0,
                           limit: Optional[int] = 10,
                           first_name: Optional[str] = None,
                           last_name: Optional[str] = None,
                           email: Optional[str] = None,
                          ) -> List[Contact]:
        """
        Retrieves a list of contacts for a specific user, with optional filters.

        Args:
            user (User): The user for whom to retrieve contacts.
            skip (Optional[int]): The offset for pagination.
            limit (Optional[int]): The maximum number of contacts to retrieve.
            first_name (Optional[str]): Filter by contact's first name.
            last_name (Optional[str]): Filter by contact's last name.
            email (Optional[str]): Filter by contact's email.

        Returns:
            List[Contact]: A list of contacts matching the given filters.
        """
        query = select(Contact).filter_by(user=user).offset(skip).limit(limit)
        if first_name:
            query = query.where(Contact.first_name.ilike(f"%{first_name}%"))
        if last_name:
            query = query.where(Contact.last_name.ilike(f"%{last_name}%"))
        if email:
            query = query.where(Contact.email.ilike(f"%{email}%"))

        contacts = await self.session.execute(query)
        return list(contacts.scalars().all())

    async def get_contact_by_id(self, user: User, contact_id: int) -> Contact:
        """
        Retrieves a contact by its ID for a specific user.

        Args:
            user (User): The user whose contact is being retrieved.
            contact_id (int): The ID of the contact to retrieve.

        Returns:
            Contact: The contact matching the given ID, or None if not found.
        """
        query = select(Contact).filter_by(id=contact_id, user=user)
        contact = await self.session.execute(query)
        return contact.scalar_one_or_none()

    async def create_contact(self, body: ContactsModel, user: User) -> Contact:
        """
        Creates a new contact for a specific user.

        Args:
            body (ContactsModel): The data for the new contact.
            user (User): The user who owns the contact.

        Returns:
            Contact: The newly created contact.
        """
        contact = Contact(**body.model_dump(exclude_unset=True), user=user)
        self.session.add(contact)
        await self.session.commit()
        await self.session.refresh(contact)
        return contact

    async def update_contact(self, contact_id: int, body: ContactsModel, user: User) -> Contact:
        """
        Updates an existing contact for a specific user.

        Args:
            contact_id (int): The ID of the contact to update.
            body (ContactsModel): The new data to update the contact with.
            user (User): The user who owns the contact.

        Returns:
            Contact: The updated contact.
        """
        contact = await self.get_contact_by_id(user, contact_id)
        if contact:
            for key, value in body.model_dump(exclude_unset=True).items():
                setattr(contact, key, value)
        await self.session.commit()
        await self.session.refresh(contact)
        return contact

    async def delete_contact(self, contact_id: int, user: User):
        """
        Deletes an existing contact for a specific user.

        Args:
            contact_id (int): The ID of the contact to delete.
            user (User): The user who owns the contact.

        Returns:
            Contact: The deleted contact, or None if it was not found.
        """
        contact = await self.get_contact_by_id(user, contact_id)
        if contact:
            await self.session.delete(contact)
            await self.session.commit()
        return contact

    async def get_contacts_for_weekly_birthday(self, user: User, birthday_date: Optional[date]):
        """
        Retrieves contacts with birthdays occurring within the next week.

        This method calculates the range of dates (from today to 7 days ahead), as well as
        considering birthdays that fall at the end of the current month and in the first days
        of the next month.

        Args:
            user (User): The user whose contacts are being checked.
            birthday_date (Optional[date]): The date to start checking birthdays from.

        Returns:
            List[Contact]: A list of contacts with birthdays within the next week.
        """
        today = birthday_date
        last_day_of_current_month = date(today.year, today.month, monthrange(today.year, today.month)[1])
        days_until_end_of_month = (last_day_of_current_month - today).days

        if days_until_end_of_month < 7:
            next_month = today.month + 1
            if today.month == 12:
                next_year = today.year + 1
                next_month = 1
            else:
                next_year = today.year
            first_day_of_next_month = date(next_year, next_month, 1)
            end_day_of_rang_month = date(next_year, next_month, (7 - days_until_end_of_month))

            query = select(Contact).filter(
                or_(
                    and_(
                        extract('month', Contact.dob) == today.month,
                        extract('day', Contact.dob) >= today.day,
                        extract('day', Contact.dob) <= last_day_of_current_month.day,
                    ),
                    and_(
                        extract('month', Contact.dob) == next_month,
                        extract('day', Contact.dob) >= first_day_of_next_month.day,
                        extract('day', Contact.dob) <= end_day_of_rang_month.day,
                    )
                ),
                Contact.user_id == user.id
            )
        else:
            query = select(Contact).filter(
                and_(
                    extract('month', Contact.dob) == today.month,
                    extract('day', Contact.dob) >= today.day,
                    extract('day', Contact.dob) <= (today + timedelta(days=7)).day,
                ),
                Contact.user_id == user.id
            )

        contacts = await self.session.execute(query)
        return contacts.scalars().all()