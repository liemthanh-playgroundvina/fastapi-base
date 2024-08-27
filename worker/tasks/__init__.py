from celery import Task

class BaseTask(Task):
    abstract = True

    def __init__(self):
        super().__init__()

    def __call__(self, *args, **kwargs):
        return self.run(*args, **kwargs)
