from typing import Any

from fastapi import APIRouter, Depends
from fastapi_sqlalchemy import db

from app.helpers.exception_handler import CustomException
from app.models import User
from app.schemas.base import DataResponse
from app.schemas.user import UserItemResponse, UserRegisterRequest
from app.services.user import UserService

router = APIRouter()


@router.post('', response_model=DataResponse[UserItemResponse])
def register(register_data: UserRegisterRequest) -> Any:
    try:
        exist_user = db.session.query(User).filter(User.username == register_data.username).first()
        if exist_user:
            raise Exception('[username] already exists')
        register_user = UserService().register_user(register_data)
        return DataResponse().success_response(data=register_user)
    except Exception as e:
        raise CustomException(http_code=400, code='400', message=str(e))
