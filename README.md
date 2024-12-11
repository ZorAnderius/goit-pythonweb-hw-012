# Contacts App - Python Web Application

## Content

- [Contacts App Installation](#contacts-app-installation)
- [Reset Password Instructions](#reset-password-instructions)
- [Generate Sphinx Documentation](#generate-sphinx-documentation)

## Contacts App Installation

### 1. Clone the repository
    
```bash
        git clone https://github.com/ZorAnderius/goit-pythonweb-hw-10.git
        cd goit-pythonweb-hw-10
```
    
### 2. Add environment variables
    
```bash
        POSTGRES_USER=<YOUR_USERNAME>
        POSTGRES_PASSWORD=<YOUR_PASSWORD>
        POSTGRES_DB=<YOUR_DB_NAME>
        
        JWT_SECRET_KEY=<YOUR_JWT_SECRET_KEY>
        JWT_ALGORITHM=<YOUR_JWT_ALGORITHM>
        JWT_TOKEN_EXPIRE_SECONDS=<YOUR_JWT_EXPIRE_SECONDS>
        
        MAIL_USERNAME=<YOUR_MAIL_USERNAME>
        MAIL_PASSWORD=<YOUR_MAIL_PASSWORD>
        MAIL_FROM=<YOUR_MAIL_FROM>
        MAIL_PORT=<YOUR_MAIL_PORT>
        MAIL_SERVER=<YOUR_MAIL_SERVER>
        
        CLOUDINARY_CLOUD_NAME=<YOUR_CLOUDINARY_CLOUD_NAME>
        CLOUDINARY_API_KEY=<YOUR_CLOUDINARY_API_KEY>
        CLOUDINARY_API_SECRET=<YOUR_CLOUDINARY_API_SECRET>
```
    
where 
    
    
| Name | Type | Description |
| --- | --- | --- |
| POSTGRES_USER | str | User name for accessing the database |
| POSTGRES_PASSWORD | str | Password for accessing the database |
| POSTGRES_DB | str | Database name |
| JWT_SECRET_KEY | str | Secret key for JWT tokens |
| JWT_ALGORITHM | str | Algorithm for JWT tokens |
| JWT_TOKEN_EXPIRE_SECONDS | int | Token expiration time in seconds |
| MAIL_USERNAME | str | Email address |
| MAIL_PASSWORD | str | Email password |
| MAIL_FROM | str | Email address |
| MAIL_PORT | int | Email port |
| MAIL_SERVER | str | Email server |
| CLOUDINARY_CLOUD_NAME | str | Cloudinary cloud name |
| CLOUDINARY_API_KEY | str | Cloudinary API key |
| CLOUDINARY_API_SECRET | str | Cloudinary API secret |
    
### 3. Run the application
    
```bash
       docker-compose up --build
```
    
### 4. Open the browser and go to http://localhost:8000
    
    
### 5. Swagger documentation: http://localhost:8000/docs


## Reset Password Instructions


1. Run  the application
2. Open the browser and go to http://localhost:8000/docs
3. Choose the "/password-reset-request" endpoint
4. Click the "Try it out" button.
5. Enter the email address of the user you want to reset the password.
6. Click the "Execute" button.
7. Check your email for the reset password link.
8. Click the link to reset the password.
9. Copy the token from the opened page (the link should be in the format "/password-reset-verify/{token}").
10. Open the browser and go to http://localhost:8000/docs
12. Choose the "/reset_password" endpoint.
12. Click the "Try it out" button.
13. Enter the token you copied from the email and the new password.
14. Click the "Execute" button.
15. The password has been successfully reset.

## Generate Sphinx Documentation

1. Copy project to your local machine

2. Create a virtual environment.

2.1. If you don't have poetry installed, run the following command (If you have skipped this step and go to step 2.2)

```bash
    pip install poetry
```

2.2. Create a virtual environment

```bash
    poetry install
```
2.3. Activate the virtual environment

```bash
    poetry shell
```

3. Install Sphinx

```bash
    poetry add sphinx -G dev
```

4. Go to the docs directory

```bash
        cd docs
```

5. Generate the documentation

- for Windows
```bash
        .\\make.bat html
```

- for Linux
```bash
         make html
``` 

6. Run index.html file to see the documentation in the browser (path docs/_build/html/index.html)
