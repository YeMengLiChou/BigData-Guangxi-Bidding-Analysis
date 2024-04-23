import logging

from scrapy.crawler import Crawler
from scrapy.statscollectors import StatsCollector

from collect.collect.utils import kafka_tools

logger = logging.getLogger(__name__)


class CollectKafkaPipeline:

    @classmethod
    def from_crawler(cls, crawler: Crawler):
        obj = cls(crawler.stats)

        # 返回实例
        return obj

    def __init__(self, stats: StatsCollector):
        self.stats = stats
        self.stats.set_value("collect-kafka/send_count", 0)
        self.stats.set_value("collect-kafka/failed_send", 0)

    def process_item(self, item, spider):
        # 将 item 发送给 kafka
        status = kafka_tools.send_item_to_kafka(item)
        if status:
            self.stats.inc_value("collect-kafka/send_count")
        else:
            self.stats.inc_value("collect-kafka/failed_send")
        return None
