import logging

from scrapy.crawler import Crawler
from scrapy.statscollectors import StatsCollector

from constants import StatsKey
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
        self.stats.set_value(StatsKey.COLLECT_KAFKA_SEND_COUNT, 0)
        self.stats.set_value(StatsKey.COLLECT_KAFKA_SEND_FAILED_COUNT, 0)

    def flush(self):
        count = self.stats.get_value(StatsKey.COLLECT_KAFKA_SEND_COUNT, 0)
        if count % 1000 == 0:
            kafka_tools.flush_to_kafka()

    def process_item(self, item, spider):
        # 将 item 发送给 kafka

        try:
            kafka_tools.send_item_to_kafka(item)
            self.stats.inc_value(StatsKey.COLLECT_KAFKA_SEND_COUNT)
            self.flush()
            return "Success"
        except Exception as e:
            logger.error(e)
            self.stats.inc_value(StatsKey.COLLECT_KAFKA_SEND_FAILED_COUNT)
            return "Error"
