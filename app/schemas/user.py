from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr

from app.helpers.enums import UserRole


class UserBase(BaseModel):
    username: Optional[str] = None
    is_active: Optional[bool] = True

    class Config:
        orm_mode = True


class UserItemResponse(UserBase):
    id: int
    username: str
    is_active: bool
    role: str


class UserCreateRequest(UserBase):
    username: Optional[str]
    password: Optional[str]
    is_active: bool = True
    role: UserRole = UserRole.GUEST

    class Config:
        schema_extra = {
            "example": {
                "username": "my_username",
                "password": "my_password",
                "is_active": True,
                "role": UserRole.GUEST,
            }
        }


class UserRegisterRequest(BaseModel):
    username: str
    password: str
    role: UserRole = UserRole.GUEST


class UserUpdateMeRequest(BaseModel):
    username: Optional[str]
    password: Optional[str]

    class Config:
        schema_extra = {
            "example": {
                "username": "my_username",
                "password": "my_password",
            }
        }


class UserUpdateRequest(BaseModel):
    username: Optional[str]
    password: Optional[str]
    is_active: Optional[bool] = True
    role: Optional[UserRole]
