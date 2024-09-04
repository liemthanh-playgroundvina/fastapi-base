import json
import inspect
import logging

from app.core.config import settings
from app.mq_main import celery_execute, redis
from app.schemas.base import DataResponse
from app.schemas.queue import QueueResult
from app.services.common import DocumentLoaderService

from sse_starlette import EventSourceResponse


class ChatDocService(object):
    __instance = None

    @staticmethod
    def chat_doc_lc(request, web_urls: list, files_path: list):
        # Load file/url
        docs = DocumentLoaderService().loaders(files_path, web_urls)
        mds = DocumentLoaderService.docs_to_markdowns(docs)
        # elements = DocumentLoaderService().cleaner(elements)

        return DataResponse().success_response(data=[docs, mds])

        # return EventSourceResponse(chat_doc_lc_openai(request))

    @staticmethod
    def embed_doc_queue(task_id: str, data: QueueResult,
                          web_urls: list, files_path: list):
        try:

            data_dump = json.dumps(data.__dict__)
            request = json.dumps({"files_path": files_path, "web_urls": web_urls})
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
