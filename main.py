from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from starlette.responses import JSONResponse

from src.api import utils, contacts, auth, users
# Create FastAPI application
app = FastAPI()

# List of allowed origins for CORS
origins = [
    "http://localhost:3000",
]

# Add CORSMiddleware to handle CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limit exceeded exception handler
@app.exception_handler(RateLimitExceeded)
async def rate_limit_exception_handler(request: Request, exc: RateLimitExceeded):
    """
    Exception handler for rate limit exceeded.

    This handler is invoked when the user exceeds the request rate limit
    (rate limit). It returns a 429 Too Many Requests response.

    Parameters:
        request (Request): The client request.
        exc (RateLimitExceeded): The exception raised when rate limit is exceeded.

    Returns:
        JSONResponse: A response with 429 (Too Many Requests) status and message.
    """
    return JSONResponse(status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        content={"detail": "Too many requests"})

# Include routers for API
app.include_router(utils.router, prefix='/api')
app.include_router(contacts.router, prefix='/api')
app.include_router(auth.router, prefix='/api')
app.include_router(users.router, prefix='/api')

if __name__ == '__main__':
    """
    Runs the server using Uvicorn on port 8000.

    If this file is run as the main program, the server will be available
    on host 127.0.0.1 and port 8000.

    Enables automatic reloading when code changes.
    """
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)