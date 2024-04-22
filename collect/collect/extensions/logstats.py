import datetime
import logging

from twisted.internet import task

from scrapy import signals
from scrapy.exceptions import NotConfigured

logger = logging.getLogger(__name__)


class LogStats:
    """定时输出当前最新的时间戳"""

    def __init__(self, stats, interval=60.0):
        self.stats = stats
        self.interval = interval
        self.task = None
        self.latest_timestamp = 0

    @classmethod
    def from_crawler(cls, crawler):
        interval = crawler.settings.getfloat("LOGSTATS_INTERVAL")
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
        latest_timestamp = self.stats.get_value("last_timestamp", 0)

        msg = "Crawled latest announcement timestamp: %(latest_timestamp)s "
        log_args = {
            "latest_timestamp": datetime.datetime.fromtimestamp(
                latest_timestamp
            ).strftime("%Y-%m-%d %H:%M:%S:%f"),
        }
        logger.info(msg, log_args, extra={"spider": spider})

    def spider_closed(self, spider, reason):
        if self.task and self.task.running:
            self.task.stop()
