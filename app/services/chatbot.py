import json
import logging
from datetime import datetime
from typing import Optional, Tuple, Text, Dict, List, Union

from app.helpers.exception_handler import CustomException
from app.schemas.chatbot import ChatRequest, ChatVisionRequest
from app.services.common import ChatOpenAIServices

from sse_starlette import EventSourceResponse


class ChatService(object):
    __instance = None

    @staticmethod
    def chat(request: Union[ChatRequest, ChatVisionRequest]):
        """
        "example": {
                "messages": [
                    {"role": "user", "content": "Xin chào"},
                    {"role": "assistant", "content": "Chào bạn. Tôi có thể giúp gì cho bạn?"},
                    {"role": "user", "content": "Bạn tên gì?"},
                ],
                "chat_model": {
                    "platform": "OpenAI",
                    "model_name": "gpt-4-1106-preview",
                    "temperature": 0.7,
                    "max_tokens": 4096,
                },
            }
        """
        try:
            # Ask bot
            if request.chat_model.platform in ["OpenAI", "local"]:
                return EventSourceResponse(chat_openai(request))
            # elif request['chat_model']["platform"] == "Google":
            #     ...

        except ValueError as e:
            raise CustomException(http_code=400, code='400', message=str(e))

        except Exception as e:
            logging.getLogger('app').debug(Exception(e), exc_info=True)
            raise CustomException(http_code=500, code='500', message="Internal Server Error")


def chat_openai(request: Union[ChatRequest, ChatVisionRequest]):
    message_id = f"message_id_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}"

    # Init Chat
    chat = ChatOpenAIServices(request)
    chat.init_system_prompt(getattr(request, 'store_name', None))

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
                "language": "en"
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
        urls, gg_metadata = GoogleSearchService().google_search(
            question,
            num=response['request']['num_link'],
            lr=f"lang_{response['request']['language']}",
        )
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
