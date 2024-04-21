import datetime
import logging
import threading
from typing import Union
from config.config import settings
import redis
from redis import Redis

logger = logging.getLogger(__name__)

_client: Union[Redis, None] = None

_lock = threading.Lock()


if not _client:
    with _lock:
        if not _client:
            _client = redis.Redis(
                host=getattr(settings, "redis.host", "localhost"),
                port=getattr(settings, "redis.port", 6379),
                db=getattr(settings, "redis.db", 0),
                decode_responses=True,
            )


# ========================== KEY CONSTANTS ========================= #

KEY_ANNOUNCEMENT_LATEST_TIMESTAMP = "bidding:announcement:latest"
"""
数据库中最新的公告时间戳
"""

KEY_ANNOUNCEMENT_ARTICLE_IDS = "bidding:announcement:article_ids"
"""
已经爬取过的所有公告结果
"""


# ======================== TOOLS FUNCTIONS ========================= #


def parse_timestamp(timestamp: int) -> str:
    """
    将毫秒级时间戳解析为 YY-MM-DD 格式
    :param timestamp: 毫秒级时间戳
    :return: 格式化的字符串
    """
    time = datetime.datetime.fromtimestamp(timestamp / 1000)
    return time.strftime("%Y-%m-%d")


def get_latest_announcement_timestamp(
    parse_to_str: bool = True,
) -> Union[int, str, None]:
    """
    获取数据库中最新的公告时间戳
    :param parse_to_str 是否解析为 YY-MM-DD 格式
    :return:
    - 如果 ``parse_to_str`` 为 True，返回解析为 YY-MM-DD 的字符串
    - 如果 ``parse_to_str`` 为 False，返回毫秒级字符串
    - 当 redis 中没有对应的时间戳时，返回 None
    """
    # 先从 redis 拿到数据
    latest_timestamp = _client.get(KEY_ANNOUNCEMENT_LATEST_TIMESTAMP)
    # 从 str 转成 int
    if latest_timestamp:
        timestamp = int(str(latest_timestamp))
    else:
        timestamp = None
    # 转成 字符串 格式
    if timestamp and parse_to_str:
        return parse_timestamp(int(timestamp))
    return timestamp


def set_latest_announcement_timestamp(timestamp: Union[int, str]) -> Union[int, None]:
    """
    设置数据库中最新的公告时间戳，并返回旧的时间戳
    :param timestamp: 存储的毫秒级时间戳或者 YY-MM-DD 格式
    :return:
    """
    prev = get_latest_announcement_timestamp(parse_to_str=False) or 0

    if isinstance(timestamp, str):
        timestamp = int(
            datetime.datetime.strptime(timestamp, "%Y-%m-%d").timestamp() * 1000
        )

    if timestamp > prev:
        _client.set(KEY_ANNOUNCEMENT_LATEST_TIMESTAMP, timestamp)
    return None if prev == 0 else prev


def clear_latest_announcement_timestamp():
    """
    清空数据库中最新的公告时间戳
    """
    _client.delete(KEY_ANNOUNCEMENT_LATEST_TIMESTAMP)


# --------------------- ARTICLE IDS --------------------- #


def add_unique_article_id(article_id: str) -> bool:
    """
    添加一个唯一的公告结果 ID
    :param article_id: 公告结果 ID
    :return: 是否添加成功
    """
    return _client.sadd(KEY_ANNOUNCEMENT_ARTICLE_IDS, article_id) == 1


def remove_article_id(article_id: str) -> bool:
    """
    移除一个公告结果 ID
    :param article_id:
    :return:
    """
    return _client.srem(KEY_ANNOUNCEMENT_ARTICLE_IDS, article_id) == 1


def check_article_id_exist(article_id: str) -> bool:
    """
    检查一个公告结果 ID 是否存在
    :param article_id: 公告结果 ID
    :return: 是否存在
    """
    return _client.sismember(KEY_ANNOUNCEMENT_ARTICLE_IDS, article_id) == 1


def count_article_ids() -> int:
    """
    获取已经爬取过的公告结果数量
    :return: 公告结果数量
    """
    return _client.scard(KEY_ANNOUNCEMENT_ARTICLE_IDS)


if __name__ == "__main__":
    print(_client.smembers(KEY_ANNOUNCEMENT_ARTICLE_IDS))
