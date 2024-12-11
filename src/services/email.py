"""
This module provides email sending functionality using FastAPI and FastMail.

It includes:
- Sending emails for various purposes such as email confirmation and password reset.
- Template-based email sending using HTML templates.
"""

from pathlib import Path
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from fastapi_mail.errors import ConnectionErrors
from pydantic import EmailStr
from src.conf.config import settings
from src.services.auth import create_email_token

# Email connection configuration
conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
    MAIL_STARTTLS=settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
    USE_CREDENTIALS=settings.USE_CREDENTIALS,
    VALIDATE_CERTS=settings.VALIDATE_CERTS,
    TEMPLATE_FOLDER=Path(__file__).parent / "templates",
)


async def send_email(email: EmailStr, username: str, host: str) -> None:
    """
    Sends a confirmation email for the provided email address and username.

    Args:
        email (EmailStr): The recipient's email address.
        username (str): The username of the recipient.
        host (str): The host URL used for generating the verification link.
    """
    await send_email_template(email, username, host, "Email confirmation", "verify_email.html")


async def send_reset_password_email(email: EmailStr, username: str, host: str) -> None:
    """
    Sends a password reset email for the provided email address and username.

    Args:
        email (EmailStr): The recipient's email address.
        username (str): The username of the recipient.
        host (str): The host URL used for generating the reset link.
    """
    await send_email_template(email, username, host, "Reset password", "reset_password.html")


async def send_email_template(email: EmailStr,
                              username: str,
                              host: str,
                              email_subject: str,
                              template_html: str) -> None:
    """
    Sends an email using a template and the provided subject and parameters.

    Args:
        email (EmailStr): The recipient's email address.
        username (str): The username of the recipient.
        host (str): The host URL used for generating the link (e.g., for verification or reset).
        email_subject (str): The subject of the email.
        template_html (str): The name of the HTML template to use for the email body.

    Raises:
        ConnectionErrors: If there is an error while trying to connect to the mail server.
    """
    try:
        # Generate the email token (used for verification or reset)
        token_verification = create_email_token({"sub": email})

        # Create the email message schema
        message = MessageSchema(
            subject=email_subject,
            recipients=[email],
            template_body={
                "host": host,
                "username": username,
                "token": token_verification,
            },
            subtype=MessageType.html,
        )

        # Initialize FastMail and send the message
        fm = FastMail(conf)
        await fm.send_message(message, template_name=template_html)

    except ConnectionErrors as err:
        print(f"Error sending email: {err}")
