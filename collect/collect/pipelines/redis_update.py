# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import logging

from scrapy import Spider, signals
from scrapy.crawler import Crawler
from scrapy.statscollectors import StatsCollector

import collect.collect.utils.redis_tools as redis
from constant import constants

logger = logging.getLogger(__name__)


def update_redis_scraped_article_id(*article_ids):
    """
    更新 redis 中已爬取的公告 id
    :param article_ids:
    :return:
    """
    for ids in article_ids:
        redis.add_unique_article_id(ids)


def update_redis_latest_timestamp(timestamp: int):
    """
    更新 redis 中最新数据的时间戳
    :param timestamp:
    :return:
    """
    redis.set_latest_announcement_timestamp(timestamp)


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
            "redis-update/latest_announcement_timestamp",
            redis.get_latest_announcement_timestamp(parse_to_str=True),
        )
        # 已经爬取的公告总数
        self.stats.set_value(
            "redis-update/scraped_announcement_count", redis.count_article_ids()
        )

    def process_item(self, item, spider: Spider):
        self.stats.inc_value("redis-update/process_items_count")

        # 更新两个公告的id，仅有结果公告能够存在表示item数据正常
        purchase_id = item.get(constants.KEY_PROJECT_PURCHASE_ARTICLE_ID, None)
        result_id = item.get(constants.KEY_PROJECT_RESULT_ARTICLE_ID, None)
        if result_id:
            if purchase_id:
                redis.add_unique_article_id(purchase_id)
            redis.add_unique_article_id(result_id)

        # 结果公告的发布日期作为标准
        result_publish_date = item.get(constants.KEY_PROJECT_RESULT_PUBLISH_DATE, None)
        if result_publish_date:
            redis.set_latest_announcement_timestamp(timestamp=result_publish_date)

        return item
