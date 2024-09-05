import json
import logging
from datetime import datetime
import requests
from requests.auth import HTTPBasicAuth
from fastapi import APIRouter, Depends, status

from app.core.config import settings
from app.helpers.exception_handler import CustomException
from app.helpers.login_manager import login_required, PermissionRequired
from app.schemas.base import DataResponse
from app.schemas.queue import QueueResult
from app.mq_main import redis

logger = logging.getLogger()
router = APIRouter()


@router.get(
    "/status/{task_id}",
    dependencies=[Depends(login_required)],
    response_model=DataResponse[QueueResult]
)
def queue_status(
        *,
        task_id: str,
):
    """## Check status of task

    ### Args:  
    - task_id (str): task id

    ### Status:
    - PENDING:
    - SUCCESS:
    - FAILED:
    - TIMEOUT:
    - TIMELIMIT:
    - KILLED:

    """
    data = redis.get(task_id)
    if data is None:
        return DataResponse().success_response(
            data=QueueResult(task_id='', error={'code': "404", 'message': "task_id not found!"}))

    message = json.loads(data)
    message["queue"] = get_list_tasks_queue_rabbitmq()

    # Handler if you don't have status_general, start_time
    if not message["status"]["general_status"] or not message["status"]["general_status"].strip():
        message["status"]["general_status"] = "PENDING"
        data_dump = json.dumps(message)
        redis.set(task_id, data_dump)

    if not message["time"]["start_generate"] or not message["time"]["start_generate"].strip():
        message["time"]["start_generate"] = str(datetime.utcnow().timestamp())
        data_dump = json.dumps(message)
        redis.set(task_id, data_dump)

    # Check >QUEUE_TIMEOUT is still pending -> failed (don't come into worker)
    status_general = message["status"]["general_status"]
    start_time = float(message["time"]["start_generate"])
    curr_time = datetime.utcnow().timestamp()
    # print(start_time, curr_time)
    # print(type(start_time), type(curr_time))
    if curr_time - start_time > float(settings.QUEUE_TIMEOUT) and status_general == "PENDING":
        logging.getLogger('app').debug(Exception(f"{task_id}: Worker is don't working, or queue time out!"), exc_info=True)
        message["status"]["general_status"] = "TIMEOUT"
        message["time"]["end_generate"] = str(curr_time)
        message['error'] = {'code': "502", 'message': "Internal Server Error!"}
        data_dump = json.dumps(message)
        redis.set(task_id, data_dump)

    # Check task is working -> dead -> failed ()
    status_task = message["status"]["task_status"]
    if (status_general == "SUCCESS" and status_task != "SUCCESS") and curr_time - start_time > float(settings.QUEUE_TIME_LIMIT) * 2:
        logging.getLogger('app').debug(Exception(f"{task_id}: Task failed after work, maybe worker dead when processing"), exc_info=True)
        message["status"]["general_status"] = "TIMELIMIT"
        message["time"]["end_generate"] = str(curr_time)
        message['error'] = {'code': "503", 'message': "Internal Server Error!"}
        data_dump = json.dumps(message)
        redis.set(task_id, data_dump)

    return DataResponse().success_response(data=message)


@router.put(
    "/status/{task_id}",
    dependencies=[Depends(login_required)],
    response_model=DataResponse[QueueResult]
)
def delete_task(
        *,
        task_id: str,
):
    """
    Only case:

        "general_status": "PENDING"
        "task_status": None

    """
    data = redis.get(task_id)
    if data is None:
        return DataResponse().success_response(
            data=QueueResult(task_id='', error={'code': "404", 'message': "task_id not found!"}))

    message = json.loads(data)
    general_status = message["status"]["general_status"]

    if general_status == "PENDING":
        message["status"]["general_status"] = "KILLED"
        message["time"]["end_generate"] = str(datetime.utcnow().timestamp())
        message['error'] = {'code': "200", 'message': "Task Killed!"}
        data_dump = json.dumps(message)
        redis.set(task_id, data_dump)

        # init redis task
        json_tasks_removed = redis.get("tasks_removed")
        if not json_tasks_removed:
            tasks_removed = []
            redis.set("tasks_removed", json.dumps(tasks_removed))
        else:
            tasks_removed = json.loads(json_tasks_removed)

        # Add to list task removed into 'tasks_removed' in redis
        tasks_removed.append(task_id)
        redis.set("tasks_removed", json.dumps(tasks_removed))

    else:
        return DataResponse().success_response(
            data=QueueResult(task_id=task_id, error={'code': "400", 'message': "Task must is 'PENDING'"}))

    return DataResponse().success_response(data=message)


def get_list_tasks_queue_rabbitmq():
    username = settings.RABBITMQ_USER
    password = settings.RABBITMQ_PASS
    server = f'http://{settings.RABBITMQ_HOST}:15672'

    response = requests.get(f'{server}/api/queues', auth=HTTPBasicAuth(username, password))

    if response.status_code == 200:
        queues = response.json()
        final_queues = []
        for queue in queues:
            if "." not in queue['name'] and "@" not in queue['name']:
                final_queues.append({"name": queue['name'], "num_task_queueing": queue.get('messages', 0)})
    else:
        raise Exception("Can't connect to RabbitMQ")

    return final_queues