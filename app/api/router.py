from fastapi import APIRouter

from app.api import (
    healthcheck,
    login,
    # register,
    user,
    queue,

    chatbot,
    chatdoc,

)

router = APIRouter()

router.include_router(healthcheck.router, tags=["health-check"], prefix="/healthcheck")
router.include_router(login.router, tags=["login"], prefix="/login")
# router.include_router(register.router, tags=["register"], prefix="/register")
router.include_router(user.router, tags=["user"], prefix="/users")
router.include_router(queue.router, tags=["queue"], prefix="/queue")

# Chatbot
router.include_router(chatbot.router, tags=["chatbot"], prefix="/chatbot")
router.include_router(chatdoc.router, tags=["chatdoc"], prefix="/chatdoc")
