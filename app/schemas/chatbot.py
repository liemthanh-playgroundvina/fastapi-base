import os
import json
from typing import Optional
from pydantic import BaseModel, root_validator
from app.core.config import settings
from app.helpers.exception_handler import CustomException
from app.helpers.llm.preprompts.store import STORES

with open(os.path.join(settings.STATIC_URL, "files/app", "chatbot.json"), 'r') as f:
    model_data = json.load(f)


class ChatRequest(BaseModel):
    messages: list
    store_name: Optional[str] = ""
    chat_model: dict

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
        messages = values['messages']
        store_name = values.get('store_name', "")
        chat_model = values.get('chat_model', {})

    # Handler
        # role
        list_role = ["user", "assistant", "system"]
        for mess in messages:
            if mess['role'] not in list_role:
                message = f'[role] in messages must in {list_role}'
                raise CustomException(http_code=400, code='400', message=message)

        # store_name
        if store_name.strip():
            if store_name not in STORES:
                message = f'[store_name] in messages must in {STORES}'
                raise CustomException(http_code=400, code='400', message=message)

        # chat_model
        if chat_model:
            # Fields required
            required_fields = ["platform", "model_name", "temperature", "max_tokens"]
            missing_fields = [field for field in required_fields if field not in chat_model]
            if missing_fields:
                message = f"Missing fields in [chat_model]: {', '.join(missing_fields)}"
                raise CustomException(http_code=400, code='400', message=message)
            platform = chat_model['platform']
            model_name = chat_model['model_name']
            temperature = chat_model['temperature']
            max_tokens = chat_model['max_tokens']

            # platform & model & temperature & max_tokens
            list_platform = list(model_data.keys())

            if platform not in list_platform:
                message = f"Don't support '{platform}'.\n{list_platform} is supported."
                raise CustomException(http_code=400, code='400', message=message)

            if model_name not in model_data[platform]:
                message = f"Don't support '{model_name}'.\n{list(model_data[platform].keys())} is supported."
                raise CustomException(http_code=400, code='400', message=message)

            if not (0 <= temperature <= 1.0):
                message = f"[temperature] must be in [0.0, 1.0]. Your current temperature is {temperature}."
                raise CustomException(http_code=400, code='400', message=message)

            max_token_limit = model_data[platform][model_name]
            if not (256 <= max_tokens <= max_token_limit):
                message = f"[max_tokens] of '{model_name}' must be between [256, {max_token_limit}]"
                raise CustomException(http_code=400, code='400', message=message)

        return values


class ChatVisionRequest(BaseModel):
    messages: list
    chat_model: dict

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

    @root_validator()
    def validate(cls, values):
        messages = values['messages']
        chat_model = values.get('chat_model', {})

    # Handler
        # role
        list_role = ["user", "assistant", "system"]
        for mess in messages:
            if mess['role'] not in list_role:
                message = f'[role] in messages must in {list_role}'
                raise CustomException(http_code=400, code='400', message=message)

        # chat_model
        if chat_model:
            # Fields required
            required_fields = ["platform", "model_name", "temperature", "max_tokens"]
            missing_fields = [field for field in required_fields if field not in chat_model]
            if missing_fields:
                message = f"Missing fields in [chat_model]: {', '.join(missing_fields)}"
                raise CustomException(http_code=400, code='400', message=message)
            platform = chat_model['platform']
            model_name = chat_model['model_name']
            temperature = chat_model['temperature']
            max_tokens = chat_model['max_tokens']

            # platform & model & temperature & max_tokens
            list_platform = list(model_data.keys())

            if platform not in list_platform:
                message = f"Don't support '{platform}'.\n{list_platform} is supported."
                raise CustomException(http_code=400, code='400', message=message)

            if model_name not in model_data[platform]:
                message = f"Don't support '{model_name}'.\n{list(model_data[platform].keys())} is supported."
                raise CustomException(http_code=400, code='400', message=message)

            if not (0 <= temperature <= 1.0):
                message = f"[temperature] must be in [0.0, 1.0]. Your current temperature is {temperature}."
                raise CustomException(http_code=400, code='400', message=message)

            max_token_limit = model_data[platform][model_name]
            if not (256 <= max_tokens <= max_token_limit):
                message = f"[max_tokens] of '{model_name}' must be between [256, {max_token_limit}]"
                raise CustomException(http_code=400, code='400', message=message)

        return values
