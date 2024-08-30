import json
from typing import List, Dict, Optional, Union
from pydantic import BaseModel, root_validator, validator

from app.schemas.chatbot import BaseChatRequest

class ChatDocLCRequest(BaseChatRequest):
    urls: Optional[List[str]] = []

    class Config:
        schema_extra = {
            "example": {
                "urls": [
                    "https://aiservices-bucket.s3.amazonaws.com/chat-vision/screen.jpg",
                    "https://python.langchain.com/v0.2/docs/how_to/#document-loaders"
                ],
                "messages": [
                    {"role": "system", "content": "You are an assistant."},
                    {"role": "user", "content": "Xin chào"},
                    {"role": "assistant", "content": "Chào bạn. Tôi có thể giúp gì cho bạn?"},
                    {"role": "user", "content": "Tóm tắt văn bản đã đưa"},
                ],
                "chat_model": {
                    "platform": "local",
                    "model_name": "qwen2-7b",
                    "temperature": 0.7,
                    "max_tokens": 2048,
                },
            }
        }

    @root_validator(pre=True)
    def validate(cls, values):
        values = super().validate(values)
        return values

    @classmethod
    def __get_validators__(cls):
        yield cls.validate_to_json

    @classmethod
    def validate_to_json(cls, value):
        if isinstance(value, str):
            return cls(**json.loads(value))
        return value


class EmbedDocRequest(BaseModel):
    urls: Optional[List[str]] = []

    class Config:
        schema_extra = {
            "example": {
                "urls": [
                    "https://aiservices-bucket.s3.amazonaws.com/chat-vision/screen.jpg",
                    "https://python.langchain.com/v0.2/docs/how_to/#document-loaders"
                ],
            }
        }

    @classmethod
    def __get_validators__(cls):
        yield cls.validate_to_json

    @classmethod
    def validate_to_json(cls, value):
        if isinstance(value, str):
            return cls(**json.loads(value))
        return value
