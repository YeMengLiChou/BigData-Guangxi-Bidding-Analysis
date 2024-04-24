import logging
from typing import Union

from scrapy import Spider, signals
from scrapy.crawler import Crawler
from scrapy.statscollectors import StatsCollector

import utils.redis_tools as redis
from constant import constants

logger = logging.getLogger(__name__)


class UpdateRedisInfoPipeline:
    """
    通过读取 item 的信息来更新 redis 中相关数据
    """

    @classmethod
    def from_crawler(cls, crawler: Crawler):
        obj = cls(crawler.stats)
        crawler.signals.connect(obj.spider_close, signal=signals.spider_closed)
        return obj

    def __init__(self, stats: StatsCollector):
        self.stats = stats

    def spider_close(self):
        # 最新公告的时间
        self.stats.set_value(
            constants.StatsKey.REDIS_LATEST_TIMESTAMP,
            redis.get_latest_announcement_timestamp(parse_to_str=True),
        )
        # 已经爬取的公告总数
        self.stats.set_value(
            constants.StatsKey.REDIS_SCRAPED_ANNOUNCEMENT_COUNT,
            redis.count_article_ids(),
        )

    def process_item(self, item, spider: Spider):
        if getattr(spider, "debug", False):
            return item

        self.stats.inc_value(constants.StatsKey.REDIS_UPDATE_PROCESS_ITEM_COUNT)
        # 更新两个公告的id
        purchase_id = item.get(constants.KEY_PROJECT_PURCHASE_ARTICLE_ID, [])
        result_id = item.get(constants.KEY_PROJECT_RESULT_ARTICLE_ID, [])

        # 更新已经爬取的公告
        redis.add_unique_article_ids(purchase_id)
        redis.add_unique_article_ids(result_id)

        # 更新最新的公告时间戳
        scrape_timestamp: Union[int, None] = item.get(
            constants.KEY_PROJECT_SCRAPE_TIMESTAMP, None
        )
        if scrape_timestamp:
            redis.set_latest_announcement_timestamp(timestamp=scrape_timestamp)
        return item
