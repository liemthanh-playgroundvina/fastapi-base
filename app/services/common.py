import os
import time
import uuid
import requests
from datetime import datetime
from typing import List, Dict, Tuple
import re
from fastapi import UploadFile
from urllib.parse import urlparse
from requests.exceptions import HTTPError

from app.core.config import settings
from app.schemas.queue import QueueTimeHandle, QueueStatusHandle, QueueResult

from googleapiclient.discovery import build
from bs4 import BeautifulSoup


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

        unique_filename = f"{int(time.time())}_{os.path.basename(file.filename)}"
        file_path = os.path.join(save_directory, unique_filename)

        with open(file_path, "wb") as f:
            f.write(file.file.read())

        return file_path

    @staticmethod
    def save_url_file(file_url: str, save_directory: str = f"{settings.STATIC_URL}/uploads") -> str:
        if not os.path.exists(save_directory):
            os.makedirs(save_directory)

        parsed_url = urlparse(file_url)
        unique_filename = f"{int(time.time())}_{os.path.basename(parsed_url.path)}"
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

        file_pattern = re.compile(
            r'^https?://(.+\.)?(s3\.amazonaws\.com|storage\.googleapis\.com|blob\.core\.windows\.net|dropbox\.com|'
            r'onedrive\.live\.com|box\.com|github\.com|digitaloceanspaces\.com|wasabisys\.com|backblazeb2\.com|.+\.(pdf|doc|docx|txt|xls|xlsx|csv|ppt|pptx|md|html|xml))$'
        )
        web_pattern = re.compile(r'^https?://')

        for url in urls:
            if file_pattern.match(url):
                file_urls.append(url)
            elif web_pattern.match(url):
                web_urls.append(url)

        return file_urls, web_urls


class GoogleSearchService(object):
    __instance = None

    @staticmethod
    def google_search(search_term, api_key = settings.GOOGLE_API_KEY, cse_id = settings.GOOGLE_CSE_ID, **kwargs):
        service = build("customsearch", "v1", developerKey=api_key)
        res = service.cse().list(q=search_term, cx=cse_id, excludeTerms="youtube.com", **kwargs).execute()
        urls = [result["link"] for result in res['items']]
        # urls = list(search(search_term, num_results=3))

        return urls

    @staticmethod
    def web_scraping(urls):
        texts = []
        for url in urls:
            try:
                response = requests.get(url)
            except:
                continue
            if response.ok:
                soup = BeautifulSoup(response.content)
                text = soup.text.replace("\n", " ")
                text = " ".join(text.split())
                if len(text.split()) < 50:
                    continue
                texts.append(text)

        return texts

