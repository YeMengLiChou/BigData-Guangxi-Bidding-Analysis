import logging

from scrapy.crawler import Crawler
from scrapy.statscollectors import StatsCollector

import constant.constants
from utils import kafka_tools

logger = logging.getLogger(__name__)


class CollectKafkaPipeline:

    @classmethod
    def from_crawler(cls, crawler: Crawler):
        obj = cls(crawler.stats)

        # 返回实例
        return obj

    def __init__(self, stats: StatsCollector):
        self.stats = stats
        self.stats.set_value(constant.constants.StatsKey.COLLECT_KAFKA_SEND_COUNT, 0)
        self.stats.set_value(
            constant.constants.StatsKey.COLLECT_KAFKA_SEND_FAILED_COUNT, 0
        )

    def process_item(self, item, spider):
        # 将 item 发送给 kafka
        status = kafka_tools.send_item_to_kafka(item)
        if status:
            self.stats.inc_value(constant.constants.StatsKey.COLLECT_KAFKA_SEND_COUNT)
        else:
            self.stats.inc_value(
                constant.constants.StatsKey.COLLECT_KAFKA_SEND_FAILED_COUNT
            )
        return {"status": "Success"}
