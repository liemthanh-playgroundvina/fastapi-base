import json
from typing import List, Dict, Optional, Union
from pydantic import BaseModel, root_validator, validator
from app.helpers.exception_handler import CustomException


class EmbedDocRequest(BaseModel):
    chat_type: str
    urls: Optional[List[str]] = []

    class Config:
        schema_extra = {
            "example": {
                "chat_type": "lc",
                "urls": [
                    "https://aiservices-bucket.s3.amazonaws.com/chat-vision/screen.jpg",
                    "https://python.langchain.com/v0.2/docs/how_to/#document-loaders"
                ],
            }
        }

    @root_validator(pre=True)
    def validate(cls, values):
        chat_type = values.get('chat_type', "")
        types = ['lc', 'rag']
        if chat_type.strip() not in types:
            raise CustomException(http_code=400, code='400', message=f"Invalid chat type '{chat_type}'.")
        return values

    @classmethod
    def __get_validators__(cls):
        yield cls.validate_to_json

    @classmethod
    def validate_to_json(cls, value):
        if isinstance(value, str):
            return cls(**json.loads(value))
        return value
