import logging

from scrapy import Request
from scrapy.crawler import Crawler


class AnnouncementFilterMiddleware:
    """
    过滤已经爬取过的公告
    根据存储在redis中的articleId进行判断
    """

    logger = logging.getLogger("collect.middleware.AnnouncementFilterMiddleware")

    @classmethod
    def from_crawler(cls, crawler: Crawler):
        return cls()

    def process_request(self, request: Request, spider):
        # TODO: redis 中判断是否存在已经爬取过的id
        return None
