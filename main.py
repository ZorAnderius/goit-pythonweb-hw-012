from typing import Callable
from ipaddress import ip_address, ip_network

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from starlette.responses import JSONResponse

from src.api import utils, contacts, auth, users

app = FastAPI()

origins = [
    "<http://localhost:3000>"
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ALLOWED_IPS = [
    ip_address("127.0.0.1")
]

ALLOWED_NETWORKS = [
    ip_network('192.168.0.0/16'),
    ip_network('172.16.0.0/12')
]

@app.middleware("http")
async def limit_access_by_ip(request: Request, call_next: Callable):
    ip = ip_address(request.client.host)

    allowed = ip in ALLOWED_IPS

    allowed = allowed or any(ip in network for network in ALLOWED_NETWORKS)

    if not allowed:
        return JSONResponse(status_code=status.HTTP_403_FORBIDDEN, content={"detail": "Not allowed IP address"})
    response = await call_next(request)
    return response

@app.exception_handler(RateLimitExceeded)
async def rate_limit_exception_handler(request: Request,
                                       exc: RateLimitExceeded):
    return JSONResponse(status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        content={"detail": "Too many requests"})
app.include_router(utils.router, prefix='/api')
app.include_router(contacts.router, prefix='/api')
app.include_router(auth.router, prefix='/api')
app.include_router(users.router, prefix='/api')

if __name__ == '__main__':
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)