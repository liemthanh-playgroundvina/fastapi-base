import json
import inspect
import logging
from datetime import datetime

from app.core.config import settings
from app.helpers.exception_handler import CustomException
from app.mq_main import celery_execute, redis
from app.schemas.base import DataResponse
from app.schemas.chatdoc import ChatDocLCRequest
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


def chatdoclc_openai(request: ChatDocLCRequest):
    message_id = f"message_id_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}"

    # Init Chat
    chat = ChatOpenAIServices(request)
    chat.init_system_prompt()

    # Searching
    yield from search_mode(message_id, chat.messages)

    # Chatting
    yield from chat.stream(stream_type="CHATTING", message_id=message_id)
    yield chat.stream_data(stream_type="METADATA", message_id=message_id, data=[chat.metadata('chatdoc')])


def search_mode(message_id: str, messages: list):
    """
     Search data from user input

     response:
        {
            "web_browser_mode": true,
            "request": {
                "query": "Event",
                "time": "20/10/2020",
                "num_link": 3
            }
        }

    """
    from app.schemas.chatbot import BaseChatRequest
    from app.helpers.llm.preprompts.store import check_web_browser_prompt, user_prompt_checked_web_browser
    from app.services.common import GoogleSearchService

    logging.getLogger('app').info("-- CHECK MODE WEB SEARCH:")

    # Check search mode
    search_model = {
        "platform": "OpenAI",
        "model_name": "gpt-4o-mini",
        "temperature": 0.5,
        "max_tokens": 4096,
    }
    search_request = BaseChatRequest(messages=messages[1:], chat_model=search_model)
    search = ChatOpenAIServices(search_request)
    search.messages = [
        {"role": "system", "content": check_web_browser_prompt()},
        {"role": "user", "content": f"""Check mode with user query input is: \n{search.messages_to_str()}\n"""}
    ]
    response = search.function_calling()

    # Stream search mode
    if response['web_browser_mode']:
        yield search.stream_data(stream_type="SEARCHING", message_id=message_id, data="Searching...")
        question = f"{response['request']['query']} {response['request']['time']}"
        urls, gg_metadata = GoogleSearchService().google_search(question, num=response['request']['num_link'])
        yield search.stream_data(stream_type="SEARCHED", message_id=message_id, data=json.dumps(urls))
        metadata = [search.metadata('check_web_search'), gg_metadata]
        yield search.stream_data(stream_type="METADATA", message_id=message_id, data=json.dumps(metadata))

        texts_searched = GoogleSearchService().web_scraping(urls)
        logging.getLogger('app').info("-- DATA SEARCHED: ")
        logging.getLogger('app').info(texts_searched)

        # Update message when have data browser
        messages[-1]['content'] = user_prompt_checked_web_browser(messages[-1]['content'], urls, texts_searched)

    else:
        metadata = [search.metadata('check_web_search')]
        yield search.stream_data(stream_type="METADATA", message_id=message_id, data=json.dumps(metadata))
