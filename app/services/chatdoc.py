import json
import inspect
import logging
import os
from datetime import datetime

from app.core.config import settings
from app.helpers.exception_handler import CustomException
from app.helpers.llm.preprompts.store import user_prompt_add_document_lc
from app.mq_main import celery_execute, redis
from app.schemas.base import DataResponse
from app.schemas.chatdoc import ChatDocLCRequest, ChatDocRAGRequest
from app.schemas.queue import QueueResult

from sse_starlette import EventSourceResponse

from app.services.common import ChatOpenAIServices


class ChatDocService(object):
    __instance = None

    @staticmethod
    def embed_doc_queue(task_id: str, data: QueueResult, request):
        try:

            data_dump = json.dumps(data.__dict__)
            # Send task
            celery_execute.send_task(
                name="{worker}.{task}".format(
                    worker=settings.WORKER_NAME,
                    task=inspect.currentframe().f_code.co_name.replace("_queue", "")
                ),
                kwargs={
                    'task_id': task_id,
                    'data': data_dump,
                    'request': request,
                },
                queue=settings.WORKER_NAME
            )
        except ValueError as e:
            logging.getLogger('app').debug(e, exc_info=True)
            data.status['general_status'] = "FAILED"
            data.error = {'code': "400", 'message': str(e)}
            redis.set(task_id, json.dumps(data.__dict__))

        except Exception as e:
            logging.getLogger('app').debug(e, exc_info=True)
            data.status['general_status'] = "FAILED"
            data.error = {'code': "500", 'message': "Internal Server Error"}
            redis.set(task_id, json.dumps(data.__dict__))


    @staticmethod
    def chat_doc_lc(request: ChatDocLCRequest):
        """
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
        """
        try:
            # Ask bot
            if request.chat_model.platform in ["OpenAI", "local"]:
                return EventSourceResponse(chatdoclc_openai(request))
            # elif request.chat_model.platform == "Google":
            #     ...

        except ValueError as e:
            raise CustomException(http_code=400, code='400', message=str(e))

        except Exception as e:
            logging.getLogger('app').debug(Exception(e), exc_info=True)
            raise CustomException(http_code=500, code='500', message="Internal Server Error")

    @staticmethod
    def chat_doc_rag(request: ChatDocRAGRequest):
        """
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
        """
        try:
            # Ask bot
            if request.chat_model.platform in ["OpenAI", "local"]:
                return EventSourceResponse(chatdocrag_openai(request))
            # elif request.chat_model.platform == "Google":
            #     ...

        except ValueError as e:
            raise CustomException(http_code=400, code='400', message=str(e))

        except Exception as e:
            logging.getLogger('app').debug(Exception(e), exc_info=True)
            raise CustomException(http_code=500, code='500', message="Internal Server Error")



def chatdoclc_openai(request: ChatDocLCRequest):
    message_id = f"message_id_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}"

    # Init Chat
    chatdoc = ChatOpenAIServices(request)
    chatdoc.init_system_prompt(chat_document_mode=True)

    # Add document into LLM
    with open(os.path.join(settings.WORKER_DIRECTORY, "chatdoc/lc", f"{request.data_id}.md"), 'r', encoding='utf-8') as file:
        document = file.read()
    chatdoc.messages[-1]['content'] = user_prompt_add_document_lc(chatdoc.messages[-1]['content'], document)

    # Chatting
    yield from chatdoc.stream(stream_type="CHATTING", message_id=message_id)
    chat_metadata = [chatdoc.metadata('chatdoc')]
    yield chatdoc.stream_data(stream_type="METADATA", message_id=message_id, data=json.dumps(chat_metadata))

    # Done
    yield chatdoc.stream_data(stream_type="DONE", message_id=message_id, data="DONE")


def chatdocrag_openai(request: ChatDocRAGRequest):
    message_id = f"message_id_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}"

    # Init Chat
    chatdoc = ChatOpenAIServices(request)
    chatdoc.init_system_prompt(chat_document_mode=True)

    # Retrieval
    document = retrieval_document(request.data_id, request.messages)
    chatdoc.messages[-1]['content'] = user_prompt_add_document_lc(chatdoc.messages[-1]['content'], document)

    # Chatting
    yield from chatdoc.stream(stream_type="CHATTING", message_id=message_id)
    chat_metadata = [chatdoc.metadata('chatdoc')]
    yield chatdoc.stream_data(stream_type="METADATA", message_id=message_id, data=json.dumps(chat_metadata))

    # Done
    yield chatdoc.stream_data(stream_type="DONE", message_id=message_id, data="DONE")


def retrieval_document(data_id: str, messages: list) -> str:
    return ""
