from fastapi import APIRouter

cyberherd_messaging_ext: APIRouter
cyberherd_messaging_static_files: list

def cyberherd_messaging_start() -> None: ...
async def cyberherd_messaging_stop() -> None: ...
