import logging
from typing import Optional, List, Any

from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Request, Body, BackgroundTasks

from app.helpers.exception_handler import CustomException
from app.helpers.login_manager import login_required, PermissionRequired
from app.schemas.base import DataResponse

from app.schemas.chatbot import ChatRequest, ChatVisionRequest
from app.services.chatbot import ChatService


logger = logging.getLogger()
router = APIRouter()


@router.post(
    "/chat",
    dependencies=[Depends(login_required)],
    # response_model=DataResponse[]
)
def chat(request: ChatRequest) -> Any:
    """
    Chatbot & GPTs & Web Search

    Params:

        - messages (list): Message of user
        - store_name (optional): is GPTs.
        - chat_model (dict):
            + platform (str)
            + model_name (str):
            + temperature (float): [0 -> 1.0]
            + max_tokens (int):
    Returns:

        - response:
            [METADATA] -> [CHATTING]... -> [METADATA] -> [DONE]

        - in <CHATTING>:
            - '\\n' is replaced to '<!<newline>!>'
            - With Draw Plot Tool: <PLOT> json_plot <\PLOT>
    Note:

        - When Web Search is enabled (auto check):
            [SEARCHING] -> [SEARCHED]... -> [METADATA] -> [CHATTING]... -> [METADATA] -> [DONE]

    """
    request = ChatRequest(**request)
    return ChatService().chat(request)


@router.post(
    "/chat-vision",
    dependencies=[Depends(login_required)],
    # response_model=DataResponse[]
)
def chat_vision(request: ChatVisionRequest) -> Any:
    """
    Chat Vision

    Params:

        messages (list): Message of user
        chat_model (dict):
            - platform (str):
            - model_name (str):
            - temperature (float): [0 -> 1.0]
            - max_tokens (int):

    Returns:

        - response:
            [METADATA] -> [CHATTING]... -> [METADATA] -> [DONE]

        - in <CHATTING>:
            - '\\n' is replaced to '<!<newline>!>'
            - With Draw Plot Tool: <PLOT> json_plot <\PLOT>
    Note:

        - When Web Search is enabled (auto check):
            [SEARCHING] -> [SEARCHED]... -> [METADATA] -> [CHATTING]... -> [METADATA] -> [DONE]


        - Example for message with image: https://readme.fireworks.ai/docs/querying-vision-language-models#chat-completions-api

        - We currently support .png, .jpg/.jpeg, .gif, .bmp, .tiff and .ppm format images.

        - Limit: 10MB (Base64 image), 5MB (URL image)
    """
    request = ChatVisionRequest(**request)
    return ChatService().chat(request)
