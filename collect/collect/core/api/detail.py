import urllib

from collect.collect.core.api import GETBaseApi
from collect.collect.utils import time


class DetailApi(GETBaseApi):

    base_url = "https://www.ccgp-guangxi.gov.cn/portal/detail"

    @staticmethod
    def get_complete_url(
            articleId: str,
            parentId: int = 66485,
            timestamp: int = time.now_timestamp()
    ) -> str:
        """
        生成完整的请求 url
        :param articleId:
        :param parentId:
        :param timestamp:
        :return:
        """
        return (f"{DetailApi.base_url}"
                f"?articleId={urllib.parse.quote(articleId)}"
                f"&parentId={parentId}"
                f"&timestamp={timestamp}")
