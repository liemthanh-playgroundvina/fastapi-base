import itertools
import os
import uuid
import mimetypes

import uuid
import requests
from datetime import datetime
from typing import List, Dict, Tuple, Iterator
import re
from fastapi import UploadFile
from urllib.parse import urlparse
from requests.exceptions import HTTPError

from app.core.config import settings
from app.schemas.queue import QueueTimeHandle, QueueStatusHandle, QueueResult

from googleapiclient.discovery import build
from bs4 import BeautifulSoup


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


    @staticmethod
    def save_upload_file(file: UploadFile, save_directory: str = f"{settings.STATIC_URL}/uploads") -> str:
        if not os.path.exists(save_directory):
            os.makedirs(save_directory)

        unique_filename = f"{uuid.uuid4().hex}_{os.path.basename(file.filename)}"
        file_path = os.path.join(save_directory, unique_filename)

        with open(file_path, "wb") as f:
            f.write(file.file.read())

        return file_path

    @staticmethod
    def detect_content_type(file_path):
        """Detect MIME type based on file extension."""

        content_type, _ = mimetypes.guess_type(file_path)
        return content_type

    @staticmethod
    def save_url_file(file_url: str, save_directory: str = f"{settings.STATIC_URL}/uploads") -> str:
        if not os.path.exists(save_directory):
            os.makedirs(save_directory)

        parsed_url = urlparse(file_url)
        unique_filename = f"{uuid.uuid4().hex}_{os.path.basename(parsed_url.path)}"
        file_path = os.path.join(save_directory, unique_filename)

        try:
            response = requests.get(file_url)
            response.raise_for_status()
            with open(file_path, "wb") as f:
                f.write(response.content)

            return file_path
        except HTTPError as http_err:
            raise ValueError(f"Failed to download file: {http_err}")

    @staticmethod
    def classify_urls(urls: List[str]) -> Tuple[List[str], List[str]]:
        file_urls = []
        web_urls = []

        storage_domain_pattern = re.compile(
            r'https?://(.+\.)?(s3\.amazonaws\.com|storage\.googleapis\.com|blob\.core\.windows\.net|dropbox\.com|'
            r'onedrive\.live\.com|box\.com|github\.com|digitaloceanspaces\.com|wasabisys\.com|backblazeb2\.com)'
        )

        file_extension_pattern = re.compile(
            r'.+\.(pdf|doc|docx|txt|xls|xlsx|csv|ppt|pptx|md|html|xml)$'
        )

        for url in urls:
            if storage_domain_pattern.match(url):
                if file_extension_pattern.search(url):
                    file_urls.append(url)
            else:
                if url.startswith("http://") or url.startswith("https://"):
                    web_urls.append(url)

        return file_urls, web_urls


class GoogleSearchService(object):
    __instance = None

    @staticmethod
    def google_search(search_term, api_key = settings.GOOGLE_API_KEY, cse_id = settings.GOOGLE_CSE_ID, **kwargs):
        service = build("customsearch", "v1", developerKey=api_key)
        res = service.cse().list(q=search_term, cx=cse_id, excludeTerms="youtube.com", **kwargs).execute()
        urls = [result["link"] for result in res['items']]
        # urls = list(search(search_term, num_results=3))

        return urls

    @staticmethod
    def web_scraping(urls):
        texts = []
        for url in urls:
            try:
                response = requests.get(url)
            except:
                continue
            if response.ok:
                soup = BeautifulSoup(response.content)
                text = soup.text.replace("\n", " ")
                text = " ".join(text.split())
                if len(text.split()) < 50:
                    continue
                texts.append(text)

        return texts


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

        for i, element in enumerate(elements):
            elements[i] = element.apply(clean_extra_whitespace)
        return elements

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
            markdowns.append(DocumentLoaderService().iter_markdown_lines(doc))
