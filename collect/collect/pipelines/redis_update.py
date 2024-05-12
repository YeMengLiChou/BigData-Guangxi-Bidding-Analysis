import datetime
import logging
from typing import Union

from scrapy import Spider, signals
from scrapy.crawler import Crawler
from scrapy.statscollectors import StatsCollector

import utils.redis_tools as redis
from constants import StatsKey, ProjectKey, CollectDevKey

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
            StatsKey.REDIS_LATEST_TIMESTAMP,
            redis.get_latest_announcement_timestamp(parse_to_str=True),
        )
        # 已经爬取的公告总数
        self.stats.set_value(
            StatsKey.REDIS_SCRAPED_ANNOUNCEMENT_COUNT,
            redis.count_article_ids(),
        )

    def process_item(self, item, spider: Spider):
        if getattr(spider, "debug", False):
            return item

        self.stats.inc_value(StatsKey.REDIS_UPDATE_PROCESS_ITEM_COUNT)

        # 更新公告的id
        result_id = item.get(ProjectKey.RESULT_ARTICLE_ID, [])

        # 对已经解析过的进行跳过
        result_parsed = item.pop(CollectDevKey.PARRED_RESULT_ARTICLE_ID, 0)

        add_ids = []
        for i in range(len(result_id)):
            if (result_parsed >> i) & 1 == 0:
                add_ids.append(result_id[i])

        # 更新已经爬取的公告
        redis.add_unique_article_ids(add_ids)

        # 更新最新的公告时间戳
        scrape_timestamp: Union[int, None] = item.get(ProjectKey.SCRAPE_TIMESTAMP, None)
        if scrape_timestamp:
            redis.set_latest_announcement_timestamp(timestamp=scrape_timestamp)

        # 增加item的数量
        d = datetime.datetime.fromtimestamp(scrape_timestamp / 1000)
        time_desc = f"{d.year}-{d.month}"
        redis.increment_items_amount(time_desc)

        return item
