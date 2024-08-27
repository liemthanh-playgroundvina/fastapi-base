import logging
import json

from app.core.config import settings

from worker.tasks import BaseTask
from worker.celery_app import app
from worker.common import TaskStatusManager
from celery.exceptions import SoftTimeLimitExceeded
from amqp.exceptions import PreconditionFailed


@app.task(
    bind=True,
    base=BaseTask,
    soft_time_limit=float(settings.QUEUE_TIME_LIMIT),
    time_limit=float(settings.QUEUE_TIME_LIMIT) + 20,
    name=f"{settings.WORKER_NAME}.healthcheck",
    queue=settings.WORKER_NAME
)
def healthcheck_task(self, task_id: str, data: bytes):
    """
    """
    print(f"============= HealthCheck task {task_id}: Started ===================")
    try:
        # Load data
        data = json.loads(data)
        TaskStatusManager.started(task_id, data)

        # Check task removed
        TaskStatusManager.check_task_removed(task_id)

        # Check GPU
        gpus = {
            "nvidia-smi": check_nvidia_smi(),
            "nvcc -V": check_nvcc_version(),
            "pytorch-gpu": check_torch_gpu(),
            "onnxruntime-gpu": check_onnxruntime_gpu(),
        }

        # Successful
        metadata = {
            "task": "healthcheck",
        }
        response = {"data": {"healthcheck": True, 'gpu': gpus}, "metadata": metadata}
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


def check_nvidia_smi():
    import subprocess

    try:
        result = subprocess.run(['nvidia-smi'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode == 0:
            return str(result.stdout)
        else:
            return "Failed to run nvidia-smi:", result.stderr
    except FileNotFoundError:
        return "nvidia-smi is not installed or not in PATH"


def check_nvcc_version():
    import subprocess

    try:
        result = subprocess.run(['nvcc', '-V'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode == 0:
            return str(result.stdout)
        else:
            return "Failed to run nvcc -V:", result.stderr
    except FileNotFoundError:
        return "nvcc is not installed or not in PATH"


def check_torch_gpu():
    import torch
    if torch.cuda.is_available():
        return {
            "gpu_available": True,
            "torch_version": torch.__version__,
            "cuda_version": torch.version.cuda,
            "cudnn_version": torch.backends.cudnn.version(),
            "gpu_name": torch.cuda.get_device_name(0),
        }
    else:
        return "No GPU available"

def check_onnxruntime_gpu():
    import onnxruntime as ort

    providers = ort.get_all_providers()

    if 'CUDAExecutionProvider' in providers:
        return "ONNX is using GPU"
    else:
        return "ONNX is not using GPU"
