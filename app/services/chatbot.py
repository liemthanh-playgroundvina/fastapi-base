import json
import logging
from datetime import datetime
from typing import Optional, Tuple, Text, Dict, List

from app.helpers.exception_handler import CustomException
from app.core.config import settings
from app.helpers.llm.preprompts.store import get_system_prompt_follow_name
from app.services.common import CommonService, GoogleSearchService

from openai import OpenAI
import tiktoken
from sse_starlette import EventSourceResponse


class ChatService(object):
    __instance = None

    @staticmethod
    def chat(request):
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
            if request['chat_model']["platform"] in ["OpenAI", "local"]:
                return EventSourceResponse(chat_openai(request))
            # elif request['chat_model']["platform"] == "Google":
            #     ...

        except ValueError as e:
            raise CustomException(http_code=400, code='400', message=str(e))

        except Exception as e:
            logging.getLogger('app').debug(Exception(e), exc_info=True)
            raise CustomException(http_code=500, code='500', message="Internal Server Error")


def chat_openai(request: dict):
    logging.getLogger('app').info(
        f"*** AI Center - Chat: {request['chat_model']['model_name']} ***")

    message_id = f"message_id_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}"

    # Check host
    if request['chat_model']["platform"] in ["OpenAI"]:
        client = OpenAI(api_key=settings.OPENAI_KEY)
        model = request['chat_model']['model_name']
    elif request['chat_model']["platform"] in ["local"]:
        client = OpenAI(
            base_url=settings.LLM_URL,
        )
        model = request['chat_model']['model_name']
    else:
        raise ValueError(f"""Don't existed {request['chat_model']["platform"]} platform""")

    # Get system prompt follow store name
    messages = request['messages']
    if messages[0]['role'] != "system":
        messages = [{"role": "system", "content": "You are an assistant."}] + messages

    store_name = request.get("store_name", "")
    if store_name:
        messages[0]['content'] = get_system_prompt_follow_name("", store_name)
    else:
        messages[0]['content'] = get_system_prompt_follow_name(messages[0]['content'], None)

    # Check check_web_browser
    logging.getLogger('app').info("-- CHECK MODE WEB SEARCH:")

    response, res_metadata = check_web_browser(messages[1:])
    logging.getLogger('app').info(str(response))

    if response['web_browser_mode']:
        request['chat_model']['temperature'] = 0.5
        yield {
            "event": "new_message",
            "id": message_id,
            "retry": settings.RETRY_TIMEOUT,
            "data": "[SEARCHING]",
        }
        question = f"{response['request']['query']} {response['request']['time']}"
        urls = GoogleSearchService().google_search(question, settings.GOOGLE_API_KEY, settings.GOOGLE_CSE_ID,
                             num=response['request']['num_link'])
        messages[-1]['content'] = update_query_web_browsing(messages[-1]['content'], urls)
        yield {
            "event": "new_message",
            "id": message_id,
            "retry": settings.RETRY_TIMEOUT,
            "data": f"[END_SEARCHING]{json.dumps(urls)}",
        }

    # Log message
    logging.getLogger('app').info("-- PROMPT AI CENTER: " + (store_name or ""))
    mess_str = ""
    for mess in messages:
        mess_str += "\n" + json.dumps(mess, ensure_ascii=False)
    logging.getLogger('app').info(mess_str)

    # Model
    yield {
        "event": "new_message",
        "id": message_id,
        "retry": settings.RETRY_TIMEOUT,
        "data": "[DATA_STREAMING]",
    }
    openai_stream = client.chat.completions.create(
        model=model,
        temperature=request['chat_model']['temperature'],
        messages=messages,
        max_tokens=request['chat_model']['max_tokens'],
        stream=True,
    )

    answer = ""
    for line in openai_stream:
        if line.choices[0].delta.content:
            current_response = line.choices[0].delta.content
            answer += current_response
            yield {
                "event": "new_message",
                "id": message_id,
                "retry": settings.RETRY_TIMEOUT,
                "data": current_response.replace("\n", "<!<newline>!>"),
            }
    # End stream
    yield {
        "event": "new_message",
        "id": message_id,
        "retry": settings.RETRY_TIMEOUT,
        "data": "[DONE]",
    }
    # Metadata
    yield {
        "event": "new_message",
        "id": message_id,
        "retry": settings.RETRY_TIMEOUT,
        "data": "[METADATA]",
    }
    input_str = ""
    for mess in messages:
        input_str += f"{mess['content']}\n"
    input_str = input_str.strip()

    input_tokens = num_tokens_from_string_openai(input_str, request['chat_model']['model_name'])
    output_tokens = num_tokens_from_string_openai(answer, request['chat_model']['model_name'])

    metadata = {
        "platform": request['chat_model']['platform'],
        "model": request['chat_model']['model_name'],
        "temperature": request['chat_model']['temperature'],
        "max_tokens": request['chat_model']['max_tokens'],
        "input": input_str,
        "output": answer,
        "usage": {
            "input_tokens": input_tokens + 24,
            "output_tokens": output_tokens,
            "search_tokens": res_metadata,
        },
    }
    yield {
        "event": "new_message",
        "id": message_id,
        "retry": settings.RETRY_TIMEOUT,
        "data": metadata,
    }


def check_web_browser(list_message: list):
    """Using OpenAI check query need using web browser or not"""

    # System prompt
    system_prompt = f"""You are a GPT, a large language model created by PlayGround.
Knowledge cutoff: 10/2023
Current date: {datetime.now().strftime("%d/%m/%Y %H:%M:%S")} with (dd/mm/yyyy h:m:s) format"""
    system_prompt += """
You are a checker query for Web Browser tool from user query input. Web browser mode will enable in the following circumstances:
- User is asking about current events or something that requires real-time information (weather, sports scores, etc.)
- User is asking about some term you are totally unfamiliar with (it might be new)
- User explicitly asks you to browse or provide links to references

The format json output include:
- web_browser_mode (bool): true when web browser mode enable
- request (dict): is {} when web_browser_mode is false. When web_browser_mode is true, it's required:
    + query (str): is user query input. Query must optimized can be search Google Search. Time cannot appear in the query. 
    + time (str): is the time mentioned in the query input starting from the current time with dd/mm/yyyy format (day and month can null). Time is '' if user query input does not mention time.
    + num_link (int): The number of reference links requested by the user, default is 3.

Example for format GPT outputs:
{
    "web_browser_mode": true,
    "request": {
        "query": "Event",
        "time": "20/10/2020",
        "num_link": 3
    } 
}
"""
    # User prompt
    messages_str = ""
    for messa in list_message:
        messages_str += "\n" + json.dumps(messa, ensure_ascii=False)
    user_prompt = f"""Check mode with user query input is: \n{messages_str}\n"""
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    # Log message
    logging.getLogger('app').info("-- PROMPT WEB_BROWSER_MODE:")
    mess_str = ""
    for mess in messages:
        mess_str += "\n" + json.dumps(mess, ensure_ascii=False)
    logging.getLogger('app').info(mess_str)

    # Model
    client = OpenAI(api_key=settings.OPENAI_KEY)
    response = client.chat.completions.create(
        model="gpt-4o",
        temperature=0.5,
        response_format={"type": "json_object"},
        messages=messages
    )
    output = json.loads(response.choices[0].message.content, strict=False)

    input_str = ""
    for mess in messages:
        input_str += f"{mess['content']}\n"
    input_str = input_str.strip()

    metadata = {
        "task": "generate_prompt",
        "model": "gpt-4o",
        "usage": {
            "openAI": {"unit": "tokens/$",
                       "input": num_tokens_from_string_openai(input_str, "gpt-4o"),
                       "output": num_tokens_from_string_openai(response.choices[0].message.content, "gpt-4o"),
                       "price": "https://openai.com/api/pricing/"
                       }
        }
    }

    return output, metadata


def update_query_web_browsing(user_query: str, urls: list):
    """Web Search & Update Context-Query"""
    texts = GoogleSearchService().web_scraping(urls)

    user_prompt = """Using data was searched on the internet to answer of user query:
[Internet_Data]
"""
    for i in range(0, len(urls)):
        try:
            user_prompt += f"""- URL_{str(i + 1)}: {urls[i]}\n{texts[i].strip()}\n"""
        except:
            pass

    user_prompt += f"""<\End_Internet_Data>

User query input: {user_query}  
"""

    return user_prompt


def num_tokens_from_string_openai(string: str, model_name: str) -> int:
    encoding_name = "o200k_base"
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens
