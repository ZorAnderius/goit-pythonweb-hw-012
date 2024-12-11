"""
This module provides functionality for uploading files to Cloudinary and generating URLs for the uploaded images.

It includes:
- Initializing Cloudinary configuration with cloud name, API key, and secret.
- Uploading a file and generating a URL for accessing the uploaded image.

Dependencies:
- cloudinary library (https://cloudinary.com/documentation/python_integration)
"""

import cloudinary
import cloudinary.uploader


class UploadFileService:
    """
    Service for uploading files to Cloudinary and generating URLs for uploaded images.

    Attributes:
        cloud_name (str): The Cloudinary cloud name.
        api_key (str): The API key for Cloudinary.
        api_secret (str): The API secret for Cloudinary.
    """

    def __init__(self, cloud_name: str, api_key: str, api_secret: str):
        """
        Initializes the UploadFileService with the necessary Cloudinary configuration.

        Args:
            cloud_name (str): The Cloudinary cloud name.
            api_key (str): The API key for Cloudinary.
            api_secret (str): The API secret for Cloudinary.
        """
        self.cloud_name = cloud_name
        self.api_key = api_key
        self.api_secret = api_secret

        # Configuring Cloudinary with provided credentials
        cloudinary.config(
            cloud_name=self.cloud_name,
            api_key=self.api_key,
            api_secret=self.api_secret,
            secure=True,
        )

    @staticmethod
    def upload_file(file, username: str) -> str:
        """
        Uploads a file to Cloudinary and generates a URL for the uploaded image.

        Args:
            file: The file to be uploaded.
            username (str): The username to create a unique public ID for the uploaded file.

        Returns:
            str: A URL pointing to the uploaded image.

        This method uploads the file to Cloudinary, applies a unique public ID based on the username,
        and generates a URL for the uploaded image with specified dimensions.
        """
        # Define the public ID based on the username
        public_id = f"ContactsApp/{username}"

        # Upload the file to Cloudinary and overwrite any existing file with the same public ID
        r = cloudinary.uploader.upload(file.file, public_id=public_id, overwrite=True)

        # Generate the URL for the uploaded image with a width and height of 250px
        src_url = cloudinary.CloudinaryImage(public_id).build_url(
            width=250, height=250, crop="fill", version=r.get("version")
        )

        return src_url