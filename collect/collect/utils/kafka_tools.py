import json
import logging
import threading
import atexit
from typing import Union
from kafka import (
    KafkaProducer,
    KafkaAdminClient,
    errors,
    admin
)
from config.config import settings

from collect.collect.utils import time

__all__ = ["send_item_to_kafka"]

logger = logging.getLogger(__name__)

_producer: Union[KafkaProducer, None] = None
_admin: Union[KafkaAdminClient, None] = None
_lock = threading.Lock()
_config = dict()

DEBUG = True
if DEBUG:
    logging.basicConfig(level=logging.INFO)


def _init_config():
    """
    从 dynaconf settings 中读取配置信息
    :return:
    """
    if DEBUG:
        _config['hostname'] = '172.27.237.77'
        _config['port'] = 9092
        _config['topic'] = 'test1'
        _config['key'] = None
    else:
        _config['hostname'] = getattr(settings, "kafka.hostname", None)
        _config['port'] = getattr(settings, "kafka.port", None)
        _config['topic'] = getattr(settings, "kafka.scrapy.topic", None)
        _config['key'] = getattr(settings, "kafka.scrapy.key", None)

    if _config.get('hostname', None) is None:
        raise ValueError("kafka.hostname is not set in settings.toml")

    if _config.get('port', None) is None:
        raise ValueError("kafka.port is not set in settings.toml")

    if _config.get('topic', None) is None:
        raise ValueError("kafka.scrapy.topic is not set in settings.toml")

    logger.info(f"bootstrap-server={_config['hostname']}:{_config['port']}, topic={_config['topic']}")


def _init_producer():
    """
    初始化 Kafka Producer
    :return:
    """
    server = f"{_config['hostname']}:{_config['port']}"
    return KafkaProducer(
        bootstrap_servers=[server],
        value_serializer=lambda x: x.encode("utf-8"),
    )


def _init_admin():
    """
    初始化 KafkaAdminClient 用于创建主题
    :return:
    """
    server = f"{_config['hostname']}:{_config['port']}"
    logging.info(f"init kafka admin client with server: {server}")
    return KafkaAdminClient(bootstrap_servers=server)


def __clean_up():
    """
    模块退出时释放资源
    :return:
    """
    global _producer
    if _producer:
        _producer.close()
        _producer = None

    global _admin
    if _admin:
        _admin.close()
        _admin = None


# 双重检查锁，保证线程安全
if _producer is None:
    with _lock:
        if _producer is None:
            # 读取配置
            _init_config()
            _admin = _init_admin()
            _producer = _init_producer()
            atexit.register(__clean_up)
            # 没有链接到服务器
            if not _producer.bootstrap_connected():
                raise ConnectionError(
                    "kafka bootstrap server is not connected! please make sure your hostname and post!")


def create_topic(topic: str):
    """
    创建主题
    :param topic:
    :return:
    """
    if not _admin:
        raise RuntimeError("kafka admin is not initialized!")
    if not topic or not isinstance(topic, str):
        raise TypeError(f"topic must be str type!")
    try:
        response = _admin.create_topics([admin.NewTopic(
            topic,
            num_partitions=1,
            replication_factor=1,
        )])
    except errors.TopicAlreadyExistsError:
        return True
    return response.topic_errors[0][1] == 0  # verify error code


def send_item_to_kafka(item: Union[dict, str]):
    """
    发送 item 数据到 kafka 队列中
    :param item:
    :return:
    """
    if isinstance(item, dict):
        value = json.dumps(item, ensure_ascii=False)
    elif isinstance(item, str):
        value = item
    else:
        raise TypeError("item must be dict or str")
    # response 为 future 类型，需要 get 后才能知道是否成功响应
    response = _producer.send(_config['topic'], value=value, key=_config['key'], timestamp_ms=time.now_timestamp())
    response.get()
    return response.succeeded()


if __name__ == '__main__':
    send_item_to_kafka('hahahahhaha')