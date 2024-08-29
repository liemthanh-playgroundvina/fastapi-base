from app.schemas.base import DataResponse


class ChatDocService(object):
    __instance = None

    @staticmethod
    def embed_doc(files_path: list, web_urls: list):
        response = {"files_path": files_path, "web_urls": web_urls}
        return DataResponse().success_response(data=response)
