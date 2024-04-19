import json
from typing import Union, TextIO

from scrapy import signals
from scrapy.crawler import Crawler

import constant.constants


class DebugPipeline:
    """
    将爬虫返回的item写入文件，用于调试
    """

    @classmethod
    def from_crawler(cls, crawler: Crawler):
        obj = cls()
        crawler.signals.connect(obj.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(obj.spider_closed, signal=signals.spider_closed)
        return obj

    def __init__(self):
        self.fp: Union[TextIO, None] = None

    def spider_opened(self):
        self.fp = open("logs/item_debug.json", "w", encoding="utf-8")
        self.fp.write("[")

    def spider_closed(self):
        if self.fp:
            self.fp.write("]")
            self.fp.close()

    def process_item(self, item, spider):
        self.fp.write(json.dumps(item, ensure_ascii=False, indent=4))
        self.fp.write(",\n")
        self.fp.flush()
        return item
