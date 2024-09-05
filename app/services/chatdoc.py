import json
import inspect
import logging

from app.core.config import settings
from app.helpers.exception_handler import CustomException
from app.mq_main import celery_execute, redis
from app.schemas.base import DataResponse
from app.schemas.queue import QueueResult

from sse_starlette import EventSourceResponse


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
    def chat_doc_lc(request):
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
            return DataResponse().success_response(data=request)
            # # Ask bot
            # if request['chat_model']["platform"] in ["OpenAI", "local"]:
            #     return EventSourceResponse(chat_openai(request))
            # # elif request['chat_model']["platform"] == "Google":
            # #     ...

        except ValueError as e:
            raise CustomException(http_code=400, code='400', message=str(e))

        except Exception as e:
            logging.getLogger('app').debug(Exception(e), exc_info=True)
            raise CustomException(http_code=500, code='500', message="Internal Server Error")
