from datetime import date
from typing import Optional
from pydantic import BaseModel, Field, EmailStr, ConfigDict

from src.database.models import UserRole


class UpdateContactModel(BaseModel):
    """
    Model for updating contact information.

    Attributes:
        first_name (str, optional): The first name of the contact. Should be between 2 and 50 characters.
        last_name (str, optional): The last name of the contact. Should be between 2 and 50 characters.
        email (str, optional): The email address of the contact. Should be a valid email address with a max length of 50 characters.
        phone (str, optional): The phone number of the contact. Should be between 10 and 15 characters.
        dob (date, optional): The date of birth of the contact. The format should be YYYY-MM-DD.
    """

    first_name: Optional[str] = Field(None, max_length=50, min_length=2, description="First name")
    last_name: Optional[str] = Field(None, max_length=50, min_length=2, description="Last name")
    email: Optional[EmailStr] = Field(None, max_length=50, description="Email")
    phone: Optional[str] = Field(None, max_length=15, min_length=10, description="Phone")
    dob: Optional[date] = Field(None, description='Date of birth (YYYY-MM-DD)')


class ContactsModel(UpdateContactModel):
    """
    Model for creating a contact. Inherits from UpdateContactModel and requires all fields.

    Attributes:
        first_name (str): The first name of the contact. Should be between 2 and 50 characters.
        last_name (str): The last name of the contact. Should be between 2 and 50 characters.
        email (str): The email address of the contact. Should be a valid email address with a max length of 50 characters.
        phone (str): The phone number of the contact. Should be between 10 and 15 characters.
    """

    first_name: str = Field(..., max_length=50, min_length=2, description="First name")
    last_name: str = Field(..., max_length=50, min_length=2, description="Last name")
    email: EmailStr = Field(..., max_length=50, description="Email")
    phone: str = Field(..., max_length=15, min_length=10, description="Phone")


class ContactBirthdayModel(BaseModel):
    """
    Model for handling a contact's date of birth.

    Attributes:
        dob (date, optional): The date of birth of the contact. The format should be YYYY-MM-DD. Default is today's date.
    """

    dob: Optional[date] = Field(default=date.today(), description='Date of birth (YYYY-MM-DD)')


class ContactsResponse(ContactsModel):
    """
    Model for returning a contact's details along with its ID.

    Attributes:
        id (int): The unique identifier of the contact.
    """

    id: int

    model_config = ConfigDict(from_attributes=True)


class UpdateUser(BaseModel):
    """
    Model for updating a user's username and email.

    Attributes:
        username (str, optional): The username of the user. Should be between 2 and 50 characters.
        email (str, optional): The email address of the user. Should be a valid email address with a max length of 50 characters.
    """

    username: str = Field(None, max_length=50, min_length=2, description="User name")
    email: EmailStr = Field(None, max_length=50, description="User email")


class CreateUser(BaseModel):
    """
    Model for creating a new user.

    Attributes:
        username (str): The username of the user. Should be between 2 and 50 characters.
        email (str): The email address of the user. Should be a valid email address with a max length of 50 characters.
        password (str): The password for the user. Should be a max length of 50 characters.
    """

    username: str = Field(..., max_length=50, min_length=2, description="User name")
    email: EmailStr = Field(..., max_length=50, description="User email")
    password: str = Field(..., max_length=50, description="User password")


class UserResponse(UpdateUser):
    """
    Model for representing a user's information in the response.

    Attributes:
        id (int): The unique identifier of the user.
        role (UserRole): The role of the user, defined by UserRole enum.
        avatar (str): The avatar URL of the user.
    """

    id: int
    role: UserRole
    avatar: str

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    """
    Model for representing an authentication token.

    Attributes:
        access_token (str): The access token returned after successful authentication.
        token_type (str): The type of token (usually "bearer").
    """

    access_token: str = Field(..., description="Access token")
    token_type: str = Field(..., description="Token type")


class RequestEmail(BaseModel):
    """
    Model for requesting an email.

    Attributes:
        email (str): The email address to which a request is associated.
    """

    email: EmailStr


class ResetPassword(BaseModel):
    """
    Model for resetting a user's password using a token.

    Attributes:
        token (str): The token used for resetting the password.
        new_password (str): The new password that will replace the old one.
    """

    token: str = Field(..., description="Reset password token")
    new_password: str = Field(..., max_length=50, description="New password")