import uuid
from datetime import datetime
from app.core.config import settings

from app.schemas.queue import QueueTimeHandle, QueueStatusHandle, QueueResult


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