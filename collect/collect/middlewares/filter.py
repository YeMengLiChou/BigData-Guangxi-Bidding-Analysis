import logging
from urllib.parse import urlparse, parse_qs, unquote

import scrapy
from scrapy import Request, Spider
from scrapy.crawler import Crawler
from scrapy.exceptions import IgnoreRequest

from constants import StatsKey
from utils import redis_tools as redis

logger = logging.getLogger(__name__)


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
    article_id = _extract_url_param(url).get("articleId", None)
    if article_id:
        return unquote(article_id[0])
    return None


class ArticleIdFilterDownloadMiddleware:
    """
    将 articleId 进行去重：
    1. 该中间件从 redis 中的set检查是否已经存在
    2. articleId 的更新仅在 pipelines/redis_update.py 中的 RedisUpdatePipeline 处理 Item 时
    3. 仅 Item 能够处理成功（数据正常）时进行统计
    """

    @classmethod
    def from_crawler(cls, crawler: Crawler):
        obj = cls(crawler.stats)
        return obj

    def __init__(self, stats: scrapy.crawler.StatsCollector):
        self.stats = stats
        self.stats.set_value(StatsKey.FILTERED_COUNT, 0)

    def process_request(self, request: Request, spider: Spider):
        """
        检查 Request 是否已经请求过
        :param request:
        :param spider:
        :return:
        """
        # 如果是在 debug 则跳过
        if getattr(spider, "debug", False):
            return None

        if request.method == "GET":
            url = request.url
            article_id = _parse_article_id(url)
            if article_id and redis.check_article_id_exist(article_id):
                self.stats.inc_value(StatsKey.FILTERED_COUNT)
                raise IgnoreRequest(
                    f"article_id: `{article_id}` is duplicated, filter it!"
                )

        return None


if __name__ == "__main__":
    pass
