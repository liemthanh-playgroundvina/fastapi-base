import uuid
import requests
from datetime import datetime

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
