"""
Database Models.

This module defines the database models for the application, including `User` and `Contact`.
The models are implemented using SQLAlchemy ORM with support for mappings and relationships.
"""

from enum import Enum
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy import Integer, String, DateTime, Date, func, ForeignKey, Boolean, Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column

class UserRole(str, Enum):
    """
    Enum representing the roles of a user in the application.

    Attributes:
        USER (str): Regular user role.
        ADMIN (str): Admin user role.
    """
    USER = "user"
    ADMIN = "admin"

class Base(DeclarativeBase):
    """
    Base class for all database models.

    This class serves as the foundation for all ORM models in the application.
    """
    pass

class Contact(Base):
    """
    Represents a contact entity in the database.

    Attributes:
        id (int): Primary key of the contact.
        first_name (str): First name of the contact.
        last_name (str): Last name of the contact.
        email (str): Email address of the contact.
        phone (str): Phone number of the contact.
        dob (Optional[datetime]): Date of birth of the contact.
        user_id (int): Foreign key referencing the owning user.
        user (User): Relationship to the User model.
        created_at (datetime): Timestamp of when the contact was created.
        updated_at (datetime): Timestamp of the last update to the contact.
    """
    __tablename__ = 'contacts'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    first_name: Mapped[str] = mapped_column(String(50), nullable=False)
    last_name: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    phone: Mapped[str] = mapped_column(String(15), nullable=False)
    dob: Mapped[Optional[datetime]] = mapped_column("date_of_birth", Date, nullable=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        name="user_id",
        default=None
    )
    user: Mapped["User"] = relationship("User", backref="contacts")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now()
    )

class User(Base):
    """
    Represents a user entity in the database.

    Attributes:
        id (int): Primary key of the user.
        username (str): Unique username of the user.
        email (str): Unique email address of the user.
        hashed_password (str): Hashed password of the user.
        avatar (Optional[str]): URL of the user's avatar image.
        created_at (datetime): Timestamp of when the user was created.
        updated_at (datetime): Timestamp of the last update to the user.
        role (UserRole): Role of the user, either `USER` or `ADMIN`.
        confirmed (bool): Whether the user's email is confirmed.
    """
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    avatar: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now()
    )
    role: Mapped[UserRole] = mapped_column(SqlEnum(UserRole), nullable=False, default=UserRole.USER)
    confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
