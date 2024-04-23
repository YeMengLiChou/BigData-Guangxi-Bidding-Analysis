from urllib.parse import quote
from collect.collect.core.api import GETBaseApi
from utils import time


class DetailApi(GETBaseApi):

    base_url = "http://www.ccgp-guangxi.gov.cn/portal/detail"

    @staticmethod
    def get_complete_url(
        article_id: str, parent_id: int = 66485, timestamp: int = time.now_timestamp()
    ) -> str:
        """
        生成完整的请求 url
        :param article_id:
        :param parent_id:
        :param timestamp:
        :return:
        """
        return (
            f"{DetailApi.base_url}"
            f"?articleId={quote(article_id)}"
            f"&parentId={parent_id}"
            f"&timestamp={timestamp}"
        )
