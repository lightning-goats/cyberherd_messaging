from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from lnbits.core.models import User
from lnbits.decorators import check_user_exists
from lnbits.helpers import template_renderer

cyberherd_messaging_generic_router = APIRouter()


def cyberherd_messaging_renderer():
    return template_renderer(["cyberherd_messaging/templates"])


@cyberherd_messaging_generic_router.get("/", response_class=HTMLResponse)
async def index(request: Request, user: User = Depends(check_user_exists)):
    return cyberherd_messaging_renderer().TemplateResponse(
        "cyberherd_messaging/index.html", {"request": request, "user": user.json()}
    )
