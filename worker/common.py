import os
import json
from copy import deepcopy
from datetime import datetime
from typing import Union
from app.mq_main import redis


class TaskStatusManager(object):
    __instance = None

    @staticmethod
    def started(task_id: str, data: dict):
        data['status']['general_status'] = "SUCCESS"
        data['status']['task_status'] = "STARTED"
        data_dump = json.dumps(data)
        redis.set(task_id, data_dump)

    @staticmethod
    def failed(task_id: str, data: dict, err: dict):
        data['time']['end_generate'] = str(datetime.utcnow().timestamp())
        data['status']['task_status'] = "FAILED"
        data['error'] = err
        data_dump = json.dumps(data)
        redis.set(task_id, data_dump)

    @staticmethod
    def success(task_id: str, data: dict, response: dict):
        data['time']['end_generate'] = str(datetime.utcnow().timestamp())
        data['status']['task_status'] = "SUCCESS"
        data['task_result'] = response
        data_dump = json.dumps(data)
        redis.set(task_id, data_dump)

    @staticmethod
    def check_task_removed(task_id: str):
        json_tasks_removed = redis.get("tasks_removed")
        if not json_tasks_removed:
            tasks_removed = []
            redis.set("tasks_removed", json.dumps(tasks_removed))
        else:
            tasks_removed = json.loads(json_tasks_removed)

        if task_id in tasks_removed:
            tasks_removed.remove(task_id)
            raise ValueError("Task killed!")


class WorkerCommonService(object):
    __instance = None

    @staticmethod
    def upload_s3_file(file_path: str, content_type: str, folder_in_s3: str):
        from worker.upload_s3 import upload_file

        with open(file_path, "rb") as file:
            file_to_upload = S3UploadFileObject(filename=os.path.basename(file_path), file=file, mimetype=content_type)
            uploaded = upload_file(file_to_upload, folder_in_s3)
            if uploaded['success']:
                return {'url': uploaded['data']['url'],
                        'meta_data': {
                            'filename': os.path.basename(file_path),
                            'storage': 's3'
                        }}
            else:
                raise Exception(f"Failed to upload s3 file:\n {uploaded}")

    @staticmethod
    def fast_upload_s3_files(files_path: Union[list, dict], folder_in_s3: str):
        from worker.upload_s3 import fast_upload_files
        if isinstance(files_path, list):
            urls = fast_upload_files(files_path, folder_in_s3)
        elif isinstance(files_path, dict):
            urls = deepcopy(files_path)
            for key, value in urls.items():
                urls[key] = fast_upload_files([value], folder_in_s3)
        else:
            pass

        return urls


class DocumentLoaderService(object):
    __instance = None

    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = super(DocumentLoaderService, cls).__new__(cls)
        return cls.__instance

    @staticmethod
    def loader(file_path = None, web_url = None):
        """
        # https://docs.unstructured.io/open-source/core-functionality/partitioning
        """
        from unstructured.partition import (
            csv, email, msg, epub, xlsx, html, image, md, org, odt, pdf, text, ppt, pptx, rst,
            rtf, tsv, doc, docx, xml
        )
        from unstructured.partition.auto import partition

        partition_map = {
            csv.partition_csv: ['text/csv'],
            email.partition_email: ['message/rfc822'],
            msg.partition_msg: ['application/vnd.ms-outlook'],
            epub.partition_epub: ['application/epub+zip'],
            xlsx.partition_xlsx: [
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                'application/vnd.ms-excel'
            ],
            html.partition_html: ['text/html'],
            image.partition_image: [
                'image/png', 'image/jpeg', 'image/jpg',
                'image/tiff', 'image/bmp', 'image/heic'
            ],
            md.partition_md: ['text/markdown'],
            org.partition_org: ['text/org'],
            odt.partition_odt: ['application/vnd.oasis.opendocument.text'],
            pdf.partition_pdf: ['application/pdf'],
            text.partition_text: [
                'text/plain', 'text/x-python', 'text/javascript',
                'text/x-java-source', 'text/x-c', 'text/x-c++src',
                'application/x-sh', 'application/x-ruby',
                'application/x-php', 'text/x-go'
            ],
            ppt.partition_ppt: ['application/vnd.ms-powerpoint'],
            pptx.partition_pptx: ['application/vnd.openxmlformats-officedocument.presentationml.presentation'],
            rst.partition_rst: ['text/x-rst'],
            rtf.partition_rtf: ['application/rtf'],
            tsv.partition_tsv: ['text/tab-separated-values'],
            doc.partition_doc: ['application/msword'],
            docx.partition_docx: ['application/vnd.openxmlformats-officedocument.wordprocessingml.document'],
            xml.partition_xml: ['application/xml'],
        }

        if file_path:
            content_type = CommonService().detect_content_type(file_path)

            partition_func = next(
                (func for func, types in partition_map.items() if content_type in types),
                None
            )

            if not partition_func:
                raise ValueError(f"Can't load '{file_path}', unsupported content type: {content_type}.")

            try:
                return partition_func(file_path, include_page_breaks=True)
            except Exception as e:
                raise Exception(e)
        else:
            return partition(url=web_url)

    @staticmethod
    def loaders(files_path: list, web_urls: list):
        docs = []
        for web_url in web_urls:
            docs.append(DocumentLoaderService().loader(web_url=web_url))
        for file_path in files_path:
            docs.append(DocumentLoaderService().loader(file_path=file_path))

        return docs

    @staticmethod
    def cleaner(elements):
        """
        https://docs.unstructured.io/open-source/core-functionality/cleaning
        https://github.com/Unstructured-IO/unstructured/blob/main/unstructured/cleaners/core.py
        Custom:

            import re
            remove_citations = lambda text: re.sub("\[\d{1,3}\]", "", text)
            element.apply(remove_citations)

        """
        from unstructured.cleaners.core import (
            clean_non_ascii_chars,
            clean_ligatures,
            group_bullet_paragraph,
            group_broken_paragraphs,
            replace_unicode_quotes,
            replace_mime_encodings,
            bytes_string_to_string,
            clean_extra_whitespace,
        )
        elements_cleaned = []
        for e in elements:
            e_cleaned = (e.apply(clean_non_ascii_chars)
                         .apply(clean_ligatures)
                         .apply(group_bullet_paragraph)
                         .apply(group_broken_paragraphs)
                         .apply(replace_unicode_quotes)
                         .apply(replace_mime_encodings)
                         .apply(bytes_string_to_string)
                         .apply(clean_extra_whitespace)
            )
            elements_cleaned.append(e_cleaned)
        return elements_cleaned


    @staticmethod
    def cleaners(docs):
        docs_cleaned = []
        for doc in docs:
            docs_cleaned.append(DocumentLoaderService().cleaner(doc))
        return docs_cleaned

    @staticmethod
    def iter_markdown_lines(elements) -> Iterator[str]:
        for e in elements:
            if e.category == "Title":
                yield f"# {e.text}"
            elif e.category == "ListItem":
                yield f"- {e.text}"
            else:
                yield e.text

    @staticmethod
    def docs_to_markdowns(docs):
        markdowns = []
        for doc in docs:
            markdown = f"""**Metadata**
- Filename/URL: {doc[0].url or doc[0].filename}
- Date created: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Context**
"""
            markdown += DocumentLoaderService().iter_markdown_lines(doc)
            markdown += "\n---\n\n"
            markdowns.append(markdown)
        return markdowns


class S3UploadFileObject(object):
    filename = None
    file = None

    def __init__(self, filename, file, mimetype) -> None:
        self.filename = filename
        self.file = file
        self.mimetype = mimetype
