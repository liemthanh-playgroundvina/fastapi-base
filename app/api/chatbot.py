import json
import logging
from typing import Optional, List, Any

from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Request, Body, BackgroundTasks

from app.core.config import settings
from app.helpers.exception_handler import CustomException
from app.helpers.login_manager import login_required, PermissionRequired
from app.mq_main import redis
from app.schemas.base import DataResponse

from app.schemas.chatbot import ChatRequest, ChatVisionRequest, EmbedDocRequest
from app.schemas.queue import QueueResponse
from app.services.chatbot import ChatService
from app.services.chatdoc import ChatDocService
from app.services.common import CommonService

logger = logging.getLogger()
router = APIRouter()


@router.post(
    "/chat",
    dependencies=[Depends(login_required)],
    # response_model=DataResponse[]
)
def chat(request: ChatRequest) -> Any:
    """
    Chatbot & GPTs

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
            [DATA_STREAMING] <string_data> [DONE] [METADATA] <json_metadata>

        - in <string_data>:
            - '\\n' is replaced to '<!<newline>!>'

    Note:

        - With Web Browser Tool:
            [SEARCHING] [END_SEARCHING]<list_url> [DATA_STREAMING] <string_data> [DONE] [METADATA] <json_metadata>

        - With Draw Plot Tool:
            <PLOT> json_plot <\PLOT>
    """
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

        response: [DATA_STREAMING] <string_data> [DONE] [METADATA] <json_metadata>

        in <string_data>: '\\n' is replaced to '<!<newline>!>'

    Note:

        - With Web Browser Tool:
            [SEARCHING] [END_SEARCHING]<list_url> [DATA_STREAMING] <string_data> [DONE] [METADATA] <json_metadata>

        - With Draw Plot Tool:
            <PLOT> json_plot <\PLOT>

        - Example for message with image: https://readme.fireworks.ai/docs/querying-vision-language-models#chat-completions-api

        - We currently support .png, .jpg/.jpeg, .gif, .bmp, .tiff and .ppm format images.

        - Limit: 10MB (Base64 image), 5MB (URL image)
    """
    return ChatService().chat(request)


@router.post(
    "/chat-doc/embed/queue",
    dependencies=[Depends(login_required)],
    # response_model=DataResponse[]
)
def embed_doc_queue(
        bg_task: BackgroundTasks,
        request: EmbedDocRequest = Body(...),
        files: Optional[List[UploadFile]] = File(None)) -> Any:
    """
    API Embed Document for Chat Document

    Params:
        files: pdf|doc|docx|txt|xls|xlsx|csv|ppt|pptx|md|html|xml
        urls (list): [file, web].
            - file: pdf|doc|docx|txt|xls|xlsx|csv|ppt|pptx|md|html|xml

    Returns:

        data_id (str): The collection name to chat

    Note:
    """
    try:
        # Handler file
        types = [
            "application/pdf", "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "text/plain", "application/vnd.ms-excel", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "text/csv", "application/vnd.ms-powerpoint",
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            "text/markdown", "text/html", "application/xml", "text/xml"
        ]
        for file in files:
            if file.content_type not in types:
                message = f"Invalid file format. Only {types} type files are supported (current format is '{file.content_type}')"
                raise ValueError(message)

        files_path = []
        for file in files:
            files_path.append(CommonService().save_upload_file(file, save_directory=settings.WORKER_DIRECTORY))

        # Handler urls
        file_urls, web_urls = CommonService().classify_urls(request.urls)
        for url in file_urls:
            files_path.append(CommonService().save_url_file(url, save_directory=settings.WORKER_DIRECTORY))

        # Handler both when empty
        if not files_path and not web_urls:
            message = "Don't find your [files, urls]. Please check your input."
            raise ValueError(message)

        utc_now, task_id, data = CommonService().init_task_queue()
        redis.set(task_id, json.dumps(data.__dict__))
        bg_task.add_task(ChatDocService.embed_doc_queue, task_id, data, web_urls, files_path)
        return DataResponse().success_response(data=QueueResponse(status="PENDING", time=utc_now, task_id=task_id))

    except ValueError as e:
        raise CustomException(http_code=400, code='400', message=str(e))

    except Exception as e:
        logging.getLogger('app').debug(Exception(e), exc_info=True)
        raise CustomException(http_code=500, code='500', message="Internal Server Error")
