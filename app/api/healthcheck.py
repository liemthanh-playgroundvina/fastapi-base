from fastapi import APIRouter

from app.schemas.base import ResponseSchemaBase

router = APIRouter()


@router.get("", response_model=ResponseSchemaBase)
async def get():
    return {"message": "Health check success"}