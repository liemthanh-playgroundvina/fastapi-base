import inspect
import json
import logging

from typing import Any
from fastapi import APIRouter, BackgroundTasks
from app.schemas.queue import QueueResponse, QueueResult
from app.schemas.base import ResponseSchemaBase
from app.schemas.base import DataResponse
from app.services.common import CommonService
from app.core.config import settings

from app.mq_main import celery_execute, redis


router = APIRouter()


@router.get("", response_model=ResponseSchemaBase)
async def healthcheck():
    return {"message": "Health check success"}


@router.post(
    "/queue",
    response_model=DataResponse[QueueResponse]
)
def healthcheck_queue(bg_task: BackgroundTasks) -> Any:
    """
    """
    utc_now, task_id, data = CommonService().init_task_queue()
    redis.set(task_id, json.dumps(data.__dict__))
    bg_task.add_task(HealthCheckServices.healthcheck_queue, task_id, data)
    return DataResponse().success_response(data=QueueResponse(status="PENDING", time=utc_now, task_id=task_id))


class HealthCheckServices(object):
    __instance = None

    @staticmethod
    def healthcheck_queue(task_id: str, data: QueueResult):
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
