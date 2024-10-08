import json
import logging
import os
import mimetypes
import re
import uuid
import httpx
import requests
from datetime import datetime
from urllib.parse import urlparse

from typing import List, Dict, Tuple, Iterator, Any
from fastapi import UploadFile
from requests.exceptions import HTTPError

from app.core.config import settings
from app.schemas.queue import QueueTimeHandle, QueueStatusHandle, QueueResult
from app.schemas.chatbot import BaseChatRequest

from googleapiclient.discovery import build
from bs4 import BeautifulSoup
from openai import OpenAI


class CommonService(object):
    __instance = None

    @staticmethod
    def init_task_queue():
        utc_now = datetime.utcnow()
        task_id = str(uuid.uuid5(uuid.NAMESPACE_OID, settings.WORKER_NAME + "_" + str(utc_now.strftime('%Y%m%d%H%M%S%f'))))
        time_handle = QueueTimeHandle(start_generate=str(datetime.utcnow().timestamp())).__dict__
        status_handle = QueueStatusHandle().__dict__
        data = QueueResult(task_id=task_id, time=time_handle, status=status_handle)
        return utc_now, task_id, data


    @staticmethod
    def save_upload_file(file: UploadFile, save_directory: str = f"{settings.STATIC_URL}/uploads") -> str:
        if not os.path.exists(save_directory):
            os.makedirs(save_directory)

        unique_filename = f"{uuid.uuid4().hex}_{os.path.basename(file.filename)}"
        file_path = os.path.join(save_directory, unique_filename)

        with open(file_path, "wb") as f:
            f.write(file.file.read())

        return file_path

    @staticmethod
    def detect_content_type(file_path):
        """Detect MIME type based on file extension."""

        content_type, _ = mimetypes.guess_type(file_path)
        return content_type

    @staticmethod
    def save_url_file(file_url: str, save_directory: str = f"{settings.STATIC_URL}/uploads") -> str:
        if not os.path.exists(save_directory):
            os.makedirs(save_directory)

        parsed_url = urlparse(file_url)
        unique_filename = f"{uuid.uuid4().hex}_{os.path.basename(parsed_url.path)}"
        file_path = os.path.join(save_directory, unique_filename)

        try:
            response = requests.get(file_url)
            response.raise_for_status()
            with open(file_path, "wb") as f:
                f.write(response.content)

            return file_path
        except HTTPError as http_err:
            raise ValueError(f"Failed to download file: {http_err}")

    @staticmethod
    def classify_urls(urls: List[str]) -> Tuple[List[str], List[str]]:
        file_urls = []
        web_urls = []

        storage_domain_pattern = re.compile(
            r'https?://(.+\.)?(s3\.amazonaws\.com|storage\.googleapis\.com|blob\.core\.windows\.net|dropbox\.com|'
            r'onedrive\.live\.com|box\.com|github\.com|digitaloceanspaces\.com|wasabisys\.com|backblazeb2\.com)'
        )

        file_extension_pattern = re.compile(
            r'.+\.(pdf|doc|docx|txt|xls|xlsx|csv|ppt|pptx|md|html|xml)$'
        )

        for url in urls:
            if storage_domain_pattern.match(url):
                if file_extension_pattern.search(url):
                    file_urls.append(url)
            else:
                if url.startswith("http://") or url.startswith("https://"):
                    web_urls.append(url)

        return file_urls, web_urls


class GoogleSearchService(object):
    __instance = None

    @staticmethod
    def google_search(search_term, api_key = settings.GOOGLE_API_KEY, cse_id = settings.GOOGLE_CSE_ID, **kwargs) -> Tuple[List, Dict]:
        service = build("customsearch", "v1", developerKey=api_key)
        res = service.cse().list(q=search_term,
                                 cx=cse_id,
                                 excludeTerms="youtube.com facebook.com instagram.com",
                                 **kwargs).execute()
        urls = [result["link"] for result in res['items']]
        # urls = list(search(search_term, num_results=3))

        metadata = {
            "task": "google_search",
            "usage": {
                "num_link": kwargs.get('num', None),
            }
        }

        return urls, metadata

    @staticmethod
    def web_scraping(urls) -> List:
        texts = []
        for url in urls:
            try:
                response = requests.get(url)
            except:
                continue
            if response.ok:
                soup = BeautifulSoup(response.content, features="html.parser")
                text = soup.text.replace("\n", " ")
                text = " ".join(text.split())
                if len(text.split()) < 50:
                    continue
                texts.append(text)

        return texts

class ChatOpenAIServices:
    def __init__(self, request: BaseChatRequest):
        self.messages = request.messages
        self.host = request.chat_model.platform
        self.model = request.chat_model.model_name
        self.temperature = request.chat_model.temperature
        self.max_tokens = request.chat_model.max_tokens

        if self.host == "OpenAI":
            self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        elif self.host == 'local':
            self.client = OpenAI(
                base_url=settings.LLM_URL,
                default_headers={"x-foo": "true"},
                http_client=httpx.Client(verify=False)
            )
        else:
            raise ValueError(f"""Don't existed {self.host} platform""")

        self.answer = ""

    def init_system_prompt(self, store_name: str = None, chat_document_mode: bool = False):
        from app.helpers.llm.preprompts.store import get_system_prompt

        if self.messages[0]['role'] != "system":
            self.messages = [{"role": "system", "content": "You are an assistant."}] + self.messages
        if store_name:
            self.messages[0]['content'] = get_system_prompt(store_name=store_name, chat_document_mode=chat_document_mode)
        else:
            self.messages[0]['content'] = get_system_prompt(input_pmt=self.messages[0]['content'], chat_document_mode=chat_document_mode)

    def messages_to_str(self) -> str:
        mess_str = ""
        for mess in self.messages:
            mess_str += "\n" + json.dumps(mess, ensure_ascii=False)
        return mess_str

    @staticmethod
    def stream_data(stream_type: str, message_id: str, data: Any):
        return {
            "event": stream_type,
            "id": message_id,
            "retry": settings.RETRY_TIMEOUT,
            "data": data,
        }

    def stream(self, stream_type: str, message_id: str):
        # Log message
        logging.getLogger('app').info(f"-- TYPE: {stream_type}. PROMPT: ")
        logging.getLogger('app').info(self.messages_to_str())

        stream = self.client.chat.completions.create(
            messages=self.messages,
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            stream=True,
        )

        for line in stream:
            if line.choices[0].delta.content:
                current_response = line.choices[0].delta.content
                self.answer += current_response
                yield self.stream_data(stream_type, message_id, current_response.replace("\n", "<!<newline>!>"))


    def metadata(self, task_name: str):
        return {
            "task": task_name,
            "chat_model":{
                    "platform": self.host,
                    "model_name": self.model,
                    "temperature": self.temperature,
                    "max_tokens": self.max_tokens,
            },
            "response": {
                "input": self.messages_to_str(),
                "output": self.answer,
            },
            "usage": {
                "input": self.num_tokens_from_string_openai(self.messages_to_str()),
                "output": self.num_tokens_from_string_openai(self.answer),
            }
        }

    @staticmethod
    def num_tokens_from_string_openai(string: str) -> int:
        import tiktoken
        encoding_name = "o200k_base"
        encoding = tiktoken.get_encoding(encoding_name)
        num_tokens = len(encoding.encode(string))
        return num_tokens

    def function_calling(self) -> dict:
        # Log message
        logging.getLogger('app').info(f"PROMPT: ")
        logging.getLogger('app').info(self.messages_to_str())

        response = self.client.chat.completions.create(
            model=self.model,
            temperature=self.temperature,
            response_format={"type": "json_object"},
            messages=self.messages
        )
        self.answer = response.choices[0].message.content
        output = json.loads(self.answer, strict=False)

        return output
