import inspect
import logging
import json
import os
import uuid

from app.core.config import settings

from worker.tasks import BaseTask
from worker.celery_app import app
from worker.common import TaskStatusManager, DocumentLoaderService, WorkerCommonService
from celery.exceptions import SoftTimeLimitExceeded
from amqp.exceptions import PreconditionFailed

from unstructured.documents.elements import Element


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
        print("Document Loader: ...")
        docs = DocumentLoaderService().loaders(request['files_path'], request['web_urls'])
        docs_cleaned = DocumentLoaderService().cleaners(docs)
        # Save/Embed follow chat type
        if request['chat_type'] == "lc":
            print("Save data with [chat_type] 'Long Context'")
            data_id = save_file_for_chatlc(docs_cleaned)
        elif request['chat_type'] == "rag":
            print("Save data with [chat_type] 'RAG'")
            data_id = embed_data_for_chatrag(docs_cleaned)
        else:
            raise ValueError(f"Don't support [chat_type] '{request['chat_type']}'")
        print("Document Loader: Done")

        response = {"data_id": data_id}

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


def save_file_for_chatlc(docs_cleaned: list[list[Element]]) -> str:
    # Convert to .md
    mds = DocumentLoaderService.docs_to_markdowns(docs_cleaned)
    md_content = '\n\n'.join(mds)

    # Save to .md
    data_id = str(uuid.uuid4())

    file_name = os.path.join(settings.WORKER_DIRECTORY, "chatdoc/lc", f"{data_id}.md")
    WorkerCommonService().save_file(file_name, md_content)

    return data_id

def embed_data_for_chatrag(docs_cleaned: list[list[Element]]) -> str:
    from langchain_huggingface.embeddings import HuggingFaceEndpointEmbeddings
    from langchain_qdrant import QdrantVectorStore

    data_id = str(uuid.uuid4())
    chunks = DocumentLoaderService().chunker(docs_cleaned)

    documents = DocumentLoaderService().elements_to_documents(chunks)
    for doc in documents:
        print(doc.page_content)
        print("\n\n" + "-" * 80)
    embeddings = HuggingFaceEndpointEmbeddings(model=settings.EM_URL)
    QdrantVectorStore.from_documents(
        documents,
        embeddings,
        url=settings.VDB_URL,
        prefer_grpc=False,
        collection_name=data_id,
    )
    return data_id
