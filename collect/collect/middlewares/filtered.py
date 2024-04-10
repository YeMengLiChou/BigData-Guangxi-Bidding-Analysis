import urllib.parse

import scrapy.core.downloader.middleware
import urllib3.util
from scrapy import Request, Spider
from urllib.parse import urlparse, parse_qs

from scrapy.exceptions import IgnoreRequest

from collect.collect.utils import redis_tools as redis


def _extract_url_param(url: str) -> dict[str, list[str]]:
    """
    从 url 中解析出所需要的部分
    :param url:
    :return:
    """
    parsed_url = urlparse(url)
    params = parse_qs(parsed_url.query)
    return params


def _parse_article_id(url: str) -> str | None:
    """
    拿到 articleId
    :param url:
    :return:
    """
    articleId = _extract_url_param(url).get("articleId", None)
    if articleId:
        return urllib.parse.unquote(articleId[0])
    return None


class ArticleIdFilterDownloadMiddleware:
    def process_request(self, request: Request, spider: Spider):
        """
        检查 Request 是否已经请求过
        :param request:
        :param spider:
        :return:
        """
        if request.method == "GET":
            url = request.url
            article_id = _parse_article_id(url)
            if article_id and redis.check_article_id_exist(article_id):
                raise IgnoreRequest(
                    f"article_id: {article_id} is duplicated, filter it!"
                )
        return None


if __name__ == "__main__":
    pass
