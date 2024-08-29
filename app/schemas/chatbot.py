import os
import json
from typing import List, Dict, Optional, Union
from pydantic import BaseModel, root_validator
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

    def validate(self) -> None:
        if self.platform not in model_data:
            raise CustomException(http_code=400, code='400', message=f"Unsupported platform '{self.platform}'.")

        if self.model_name not in model_data[self.platform]:
            raise CustomException(http_code=400, code='400', message=f"Unsupported model '{self.model_name}' for platform '{self.platform}'.")

        if not (0 <= self.temperature <= 1.0):
            raise CustomException(http_code=400, code='400', message=f"Temperature must be between 0.0 and 1.0.")

        max_token_limit = model_data[self.platform][self.model_name]
        if not (256 <= self.max_tokens <= max_token_limit):
            raise CustomException(http_code=400, code='400', message=f"max_tokens must be between 256 and {max_token_limit}.")

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
        cls.validate_messages(values['messages'])
        chat_model = ChatModel(**values.get('chat_model', {}))
        chat_model.validate()
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
        super().validate(values)
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
        super().validate(values)
        return values
