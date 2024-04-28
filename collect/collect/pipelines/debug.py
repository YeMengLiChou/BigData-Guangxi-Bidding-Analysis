import datetime
import json
import os
from typing import Union, TextIO

from scrapy import signals
from scrapy.crawler import Crawler

import constants

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
        self.current_filename: Union[str, None] = None
        self.created_filenames = set()

    def spider_opened(self):
        if not os.path.exists("logs/items/"):
            os.mkdir("logs/items/")
        for filename in os.listdir("logs/items/"):
            os.remove(f"logs/items/{filename}")

    def spider_closed(self):
        if self.fp:
            self.fp.close()
            self.fp = None

        # 对每个文件的尾部补充 ], 使其成为完整的 json 文件
        for fn in self.created_filenames:
            with open(fn, "a", encoding="utf-8") as f:
                f.write(f"]")
                f.flush()

    def process_item(self, item, spider):
        scraped_timestamp = item[constants.ProjectKey.SCRAPE_TIMESTAMP]
        d = datetime.datetime.fromtimestamp(scraped_timestamp / 1000)
        filename = f"logs/items/items-{d.year}-{d.month}.json"

        first_write = False
        # 如果不是当前写入的文件
        if filename != self.current_filename:
            if self.fp:
                self.fp.close()
                self.fp = None
            self.fp = open(filename, "a", encoding="utf-8")
            self.current_filename = filename

            # 第一次写入
            if filename not in self.created_filenames:
                first_write = True
                self.created_filenames.add(filename)

        # 如果是第一次写入，则写入 [，否则写入 `,` 与前面的部分区分
        if not first_write:
            self.fp.write(",\n")
        else:
            self.fp.write("[")

        self.fp.write(json.dumps(item, ensure_ascii=False, indent=4))

        self.fp.flush()
        return item
