import os
import json
from typing import List, Dict, Optional, Union
from pydantic import BaseModel, root_validator, validator
from app.core.config import settings
from app.helpers.exception_handler import CustomException
from app.helpers.llm.preprompts.store import STORES

# Load model data
with open(os.path.join(settings.STATIC_URL, "files/app", "chatbot.json"), 'r') as f:
    model_data = json.load(f)

class ChatModel(BaseModel):
    platform: str
    model_name: str
    temperature: float
    max_tokens: int

    @validator('platform')
    def check_platform(cls, value):
        if value not in model_data:
            raise CustomException(http_code=400, code='400', message=f"Unsupported platform '{value}'.")
        return value

    @validator('model_name')
    def check_model_name(cls, value, values):
        platform = values.get('platform')
        if platform and value not in model_data.get(platform, {}):
            raise CustomException(http_code=400, code='400', message=f"Unsupported model '{value}' for platform '{platform}'.")
        return value

    @validator('temperature')
    def check_temperature(cls, value):
        if not (0 <= value <= 1.0):
            raise CustomException(http_code=400, code='400', message=f"Temperature must be between 0.0 and 1.0.")
        return value

    @validator('max_tokens')
    def check_max_tokens(cls, value, values):
        platform = values.get('platform')
        model_name = values.get('model_name')
        if platform and model_name:
            max_token_limit = model_data.get(platform, {}).get(model_name)
            if not (256 <= value <= max_token_limit):
                raise CustomException(http_code=400, code='400', message=f"max_tokens must be between 256 and {max_token_limit}.")
        return value

class BaseChatRequest(BaseModel):
    messages: List[Dict[str, Union[str, List[Dict[str, Union[str, Dict[str, str]]]]]]]
    chat_model: ChatModel

    @classmethod
    def validate_messages(cls, messages: List[Dict[str, Union[str, List[Dict[str, Union[str, Dict[str, str]]]]]]]) -> None:
        valid_roles = {"user", "assistant", "system"}
        for msg in messages:
            if msg['role'] not in valid_roles:
                raise CustomException(http_code=400, code='400', message=f"Invalid role '{msg['role']}' in messages.")

    @root_validator(pre=True)
    def validate(cls, values):
        cls.validate_messages(values.get('messages', []))
        chat_model = values.get('chat_model')
        if chat_model:
            ChatModel(**chat_model)
        return values

class ChatRequest(BaseChatRequest):
    store_name: Optional[str] = ""

    class Config:
        schema_extra = {
            "example": {
                "messages": [
                    {"role": "system", "content": "You are an assistant."},
                    {"role": "user", "content": "Xin chào"},
                    {"role": "assistant", "content": "Chào bạn. Tôi có thể giúp gì cho bạn?"},
                    {"role": "user", "content": "Bạn tên gì?"},
                ],
                "store_name": "Write For Me",
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
        store_name = values.get('store_name', "")
        if store_name.strip() and store_name not in STORES:
            raise CustomException(http_code=400, code='400', message=f"Invalid store name '{store_name}'.")
        return values

class ChatVisionRequest(BaseChatRequest):
    class Config:
        schema_extra = {
            "example": {
                "messages": [
                    {"role": "system", "content": "You are an assistant."},
                    {"role": "user", "content": "Xin chào"},
                    {"role": "assistant", "content": "Chào bạn. Tôi có thể giúp gì cho bạn?"},
                    {"role": "user", "content": [
                        {
                            "type": "text",
                            "text": "Bạn có thể mô tả hình ảnh này?",
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": "https://images.unsplash.com/photo-1582538885592-e70a5d7ab3d3?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=1770&q=80"},
                        }
                    ]}
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
        return values
