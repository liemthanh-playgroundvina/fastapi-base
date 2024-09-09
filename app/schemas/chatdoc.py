import json
from typing import List, Dict, Optional, Union
from pydantic import BaseModel, root_validator, validator
from app.helpers.exception_handler import CustomException
from app.schemas.chatbot import BaseChatRequest



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


class ChatDocLCRequest(BaseChatRequest):
    data_id: str

    class Config:
        schema_extra = {
            "example": {
                "data_id": "",
                "messages": [
                    {"role": "system", "content": "You are an assistant."},
                    {"role": "user", "content": "Xin chào"},
                    {"role": "assistant", "content": "Chào bạn. Tôi có thể giúp gì cho bạn?"},
                    {"role": "user", "content": "Cho tôi danh sách các câu hỏi về RAG."},
                ],
                "chat_model": {
                    "platform": "OpenAI",
                    "model_name": "gpt-4o",
                    "temperature": 0.7,
                    "max_tokens": 2048,
                },
            }
        }

    @root_validator(pre=True)
    def validate(cls, values):
        values = super().validate(values)
        data_id = values.get('data_id', "")
        if not data_id.strip():
            raise CustomException(http_code=400, code='400', message=f"[data_id] is not empty.")

        if not os.path.exists(os.path.join(settings.WORKER_DIRECTORY, "chatdoc/lc", f"{data_id}.md")):
            raise ValueError(f"[data_id] does not exist. Must 'embed before'")

        return values
