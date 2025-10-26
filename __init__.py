"""CyberHerd Messaging extension

Provides generic messaging utilities for LNbits extensions:
- publish notes to nostr using the nostrclient (in-process or websocket)
- broadcast JSON payloads to websocket clients via LNbits core updater

Exposes both importable functions (services) and an HTTP API.
"""

from fastapi import APIRouter

from .crud import db
from .views import cyberherd_messaging_generic_router
from .views_api import cyberherd_messaging_api_router

cyberherd_messaging_static_files = [
    {
        "path": "/cyberherd_messaging/static",
        "name": "cyberherd_messaging_static",
    }
]

cyberherd_messaging_ext: APIRouter = APIRouter(prefix="/cyberherd_messaging", tags=["cyberherd_messaging"])
cyberherd_messaging_ext.include_router(cyberherd_messaging_generic_router)
cyberherd_messaging_ext.include_router(cyberherd_messaging_api_router)


async def cyberherd_messaging_stop():
    # nothing to stop for now
    return None


def cyberherd_messaging_start():
    # nothing to schedule for now
    return None


__all__ = [
    "cyberherd_messaging_ext",
    "cyberherd_messaging_static_files",
    "cyberherd_messaging_start",
    "cyberherd_messaging_stop",
    "db",
]
