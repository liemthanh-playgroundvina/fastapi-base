import inspect
import logging
import json
import os

from app.core.config import settings

from worker.tasks import BaseTask
from worker.celery_app import app
from worker.common import TaskStatusManager, DocumentLoaderService
from celery.exceptions import SoftTimeLimitExceeded
from amqp.exceptions import PreconditionFailed


@app.task(
    bind=True,
    base=BaseTask,
    soft_time_limit=float(settings.QUEUE_TIME_LIMIT),
    time_limit=float(settings.QUEUE_TIME_LIMIT) + 20,
    name="{worker}.{task}".format(
        worker=settings.WORKER_NAME,
        task=os.path.basename(__file__).replace(".py", "")
    ),
    queue=settings.WORKER_NAME
)
def embed_doc_task(self, task_id: str, data: bytes, request: bytes):
    """
        request:
            {
                'chat_type': ['lc', 'rag'],
                'files_path': [],
                'web_urls': [],
            }
    """
    print(f"============= [{task_id}][{inspect.currentframe().f_code.co_name}]: Started ===================")
    try:
        # Load data
        data = json.loads(data)
        request = json.loads(request)
        TaskStatusManager.started(task_id, data)

        # Check task removed
        TaskStatusManager.check_task_removed(task_id)

        # Load file/url
        print("a")
        docs = DocumentLoaderService().loaders(request['files_path'], request['web_urls'])
        print("b")
        docs_cleaned = DocumentLoaderService().cleaners(docs)
        print("c")
        if request['chat_type'] == "lc":
            mds = DocumentLoaderService.docs_to_markdowns(docs_cleaned)
            response = mds
        elif request['chat_type'] == "rag":
            response = []
        print("d")
        # Successful
        metadata = {
            "task": inspect.currentframe().f_code.co_name.replace("_task", ""),
            "request": request
        }
        response = {"data": response, "metadata": metadata}
        TaskStatusManager.success(task_id, data, response)
        return

    except ValueError as e:
        logging.getLogger('celery').error(str(e), exc_info=True)
        err = {'code': "400", 'message': str(e)}
        TaskStatusManager.failed(task_id, data, err)
        return
    except SoftTimeLimitExceeded as e:
        logging.getLogger('celery').error("SoftTimeLimitExceeded: " + str(e), exc_info=True)
        error = "Task was terminated after exceeding the time limit."
        err = {'code': "500", 'message': error}
        TaskStatusManager.failed(task_id, data, err)
        return
    except PreconditionFailed:
        e = "Time out to connect into broker."
        logging.getLogger('celery').error(str(e), exc_info=True)
        err = {'code': "500", 'message': "Internal Server Error"}
        TaskStatusManager.failed(task_id, data, err)
        return
    except Exception as e:
        logging.getLogger('celery').error(str(e), exc_info=True)
        err = {'code': "500", 'message': "Internal Server Error"}
        TaskStatusManager.failed(task_id, data, err)
        return
