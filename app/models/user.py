from sqlalchemy import Column, String, Boolean, DateTime

from app.models.base import BareBaseModel


class User(BareBaseModel):
    username = Column(String, index=True, unique=True)
    hashed_password = Column(String(255))
    is_active = Column(Boolean, default=True)
    role = Column(String, default='guest')
