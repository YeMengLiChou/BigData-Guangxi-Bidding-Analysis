import datetime
import logging

from scrapy import signals
from scrapy.exceptions import NotConfigured
from scrapy.statscollectors import StatsCollector
from twisted.internet import task

from constants import StatsKey
from utils import redis_tools

logger = logging.getLogger(__name__)


class LogStats:
    """定时输出当前最新的时间戳"""

    def __init__(self, stats, interval=60.0):
        self.stats: StatsCollector = stats
        self.interval = interval
        self.task = None
        self.latest_timestamp = 0

    @classmethod
    def from_crawler(cls, crawler):
        interval = 300
        if not interval:
            raise NotConfigured
        o = cls(crawler.stats, interval)
        crawler.signals.connect(o.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(o.spider_closed, signal=signals.spider_closed)
        return o

    def spider_opened(self, spider):
        self.task = task.LoopingCall(self.log, spider)
        self.task.start(self.interval)

    def log(self, spider):
        # 最新时间戳
        latest_timestamp = datetime.datetime.fromtimestamp(
            (redis_tools.get_latest_announcement_timestamp(parse_to_str=False) or 0.0)
            / 1000
        ).strftime("%Y-%m-%d %H:%M:%S:%f")
        # 已经成功处理的公告数量
        process_announcement_count = redis_tools.count_article_ids()
        process_item_count = self.stats.get_value(
            StatsKey.REDIS_UPDATE_PROCESS_ITEM_COUNT, 0
        )

        # 异常数量
        parse_error_count = self.stats.get_value(
            StatsKey.PARSE_ERROR_TOTAL, 0
        )
        # kafka发送数量：
        send_item_count = self.stats.get_value(
            StatsKey.COLLECT_KAFKA_SEND_COUNT, 0
        )
        failed_item_count = self.stats.get_value(
            StatsKey.COLLECT_KAFKA_SEND_FAILED_COUNT, 0
        )
        # 公告过滤数量
        filtered_count = self.stats.get_value(StatsKey.FILTERED_COUNT, 0)
        # 计划爬取数量
        planned_crawl_count = self.stats.get_value(
            StatsKey.SPIDER_PLANNED_CRAWL_COUNT, 0
        )
        actual_crawl_count = self.stats.get_value(
            StatsKey.SPIDER_ACTUAL_CRAWL_COUNT, 0
        )
        residual_crawl_count = planned_crawl_count - actual_crawl_count

        redis_items_count = redis_tools.count_all_items()

        cnt = 0
        item_count_string = ""
        for k, v in redis_items_count.items():
            item_count_string += f"{k}: {int(v):4d}, "
            cnt += 1
            if cnt % 4 == 0:
                item_count_string += "\n"

        msg = (
            "Crawled info:\n"
            "redis(%(latest_timestamp)s): { ids: %(process_announcement_count)d, items: %("
            "process_item_count)d }\n"
            "kafka: { sent: %(send_item_count)d, failed: %(failed_item_count)d }\n"
            "error: { parse_error: %(parse_error_count)d }\n"
            "current: { filter: %(filtered_count)d, actual: %(actual_crawl_count)d, remain: %("
            "residual_crawl_count)d }\n"
            "items: \n %(item_count_string)s"
        )
        log_args = {
            "latest_timestamp": latest_timestamp,
            "process_announcement_count": process_announcement_count,
            "process_item_count": process_item_count,
            "send_item_count": send_item_count,
            "failed_item_count": failed_item_count,
            "parse_error_count": parse_error_count,
            "filtered_count": filtered_count,
            "actual_crawl_count": actual_crawl_count,
            "residual_crawl_count": residual_crawl_count,
            "item_count_string": item_count_string
        }
        logger.info(msg, log_args, extra={"spider": spider})

    def spider_closed(self, spider, reason):
        if self.task and self.task.running:
            self.task.stop()
