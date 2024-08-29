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

class BaseChatRequest(BaseModel):
    messages: List[Dict[str, Union[str, List[Dict[str, Union[str, Dict[str, str]]]]]]]
    chat_model: Dict[str, any]

    @classmethod
    def validate_messages(cls, messages: List[Dict[str, Union[str, List[Dict[str, Union[str, Dict[str, str]]]]]]]) -> None:
        valid_roles = {"user", "assistant", "system"}
        for msg in messages:
            if msg['role'] not in valid_roles:
                raise CustomException(http_code=400, code='400', message=f"Invalid role '{msg['role']}' in messages.")

    @classmethod
    def validate_chat_model(cls, chat_model: Dict[str, any]) -> None:
        required_fields = ["platform", "model_name", "temperature", "max_tokens"]
        for field in required_fields:
            if field not in chat_model:
                raise CustomException(http_code=400, code='400', message=f"Missing field '{field}' in chat_model.")

        platform = chat_model['platform']
        model_name = chat_model['model_name']
        temperature = chat_model['temperature']
        max_tokens = chat_model['max_tokens']

        if platform not in model_data:
            raise CustomException(http_code=400, code='400', message=f"Unsupported platform '{platform}'.")

        if model_name not in model_data[platform]:
            raise CustomException(http_code=400, code='400', message=f"Unsupported model '{model_name}' for platform '{platform}'.")

        if not (0 <= temperature <= 1.0):
            raise CustomException(http_code=400, code='400', message=f"Temperature must be between 0.0 and 1.0.")

        max_token_limit = model_data[platform][model_name]
        if not (256 <= max_tokens <= max_token_limit):
            raise CustomException(http_code=400, code='400', message=f"max_tokens must be between 256 and {max_token_limit}.")


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

    @root_validator()
    def validate(cls, values):
        # Message
        cls.validate_messages(values['messages'])
        # Store
        store_name = values.get('store_name', "")
        if store_name.strip() and store_name not in STORES:
            raise CustomException(http_code=400, code='400', message=f"Invalid store name '{store_name}'.")
        # Model
        cls.validate_chat_model(values.get('chat_model', {}))
        return values


class ChatVisionRequest(BaseChatRequest):
    @root_validator()
    def validate(cls, values):
        cls.validate_messages(values['messages'])
        cls.validate_chat_model(values.get('chat_model', {}))
        return values
