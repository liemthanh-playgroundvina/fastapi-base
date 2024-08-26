from fastapi import APIRouter

from app.api import healthcheck, login, register, user

router = APIRouter()

router.include_router(healthcheck.router, tags=["health-check"], prefix="/healthcheck")
router.include_router(login.router, tags=["login"], prefix="/login")
# router.include_router(register.router, tags=["register"], prefix="/register")
router.include_router(user.router, tags=["user"], prefix="/users")
