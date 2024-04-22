from typing import IO, Union

from scrapy import Spider, signals
from scrapy.crawler import Crawler

import constant.constants


class DebugWritePipeline:

    @classmethod
    def from_crawler(cls, crawler: Crawler):
        obj = cls()
        crawler.signals.connect(obj.spider_open, signal=signals.spider_opened)
        crawler.signals.connect(obj.spider_closed, signal=signals.spider_closed)
        return obj

    def __init__(self):
        self.fp: Union[IO, None] = None

    def spider_closed(self):
        if self.fp:
            self.fp.flush()
            self.fp.close()

    def spider_open(self):
        self.fp = open('logs/base_info_test_cases.txt', mode="a", encoding='utf-8')

    def process_item(self, item, spider: Spider):
        if constant.constants.KEY_DEV_DEBUG_WRITE in item:
            self.fp.write(f"{item[constant.constants.KEY_TEMP_BASE_INFO]}\n")
            self.fp.flush()
            return None
        return item
