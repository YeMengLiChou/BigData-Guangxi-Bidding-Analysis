import json
import logging
import os
import pathlib
import pickle
import traceback
import urllib.parse
from typing import Union, Any

from scrapy import Spider, signals
from scrapy.crawler import Crawler
from scrapy.http import Response

from collect.collect.utils import time

logger = logging.getLogger(__name__)


class ParseError(Exception):
    """自定义解析错误"""

    def __init__(
        self,
        msg: str,
        content: Union[list[str], None] = None,
        url: Union[str, None] = None,
        error: Union[BaseException, None] = None,
        timestamp: int = time.now_timestamp(),
        response_status: int = -1,
        response_body: Union[str, None] = None,
    ):
        """
        :param msg: 出错原因
        :param url: 出错 url
        :param content: 解析内容
        :param error: 上一层异常
        :param timestamp: 出现时间戳
        :param response_status: 所属响应状态码
        :param response_body: 所属响应
        """
        self.message = msg
        self.content = content
        self.url = url
        self.timestamp = timestamp
        self.error = error
        self.response_status = response_status
        self.response_body = response_body
        self.exc_info = traceback.format_tb(
            self.error.__traceback__ if self.error else self.__traceback__
        )

    def __str__(self):
        return (
            f"ParseError(\n"
            f"\tmsg: {self.message}\n"
            f"\turl: {self.url}\n"
            f"\ttimestamp: {time.dateformat(self.timestamp)}\n"
            f"\terror: {self.error.__repr__()}\n"
            f"\tresponse_stats: {self.response_status}\n"
        )

    __repr__ = __str__

    def to_dict(self):
        return {
            "msg": self.message,
            "url": self.url,
            "timestamp": time.dateformat(self.timestamp),
            "error": self.error.__repr__(),
            "response": {"status": self.response_status, "data": self.response_body},
            "content": self.content,
            "exc_info": self.exc_info,
        }


def ensure_file_exist(file: str):
    """
    确保日志文件存在
    :return:
    """
    # 文件不存在则创建
    path = pathlib.Path(file)
    if not path.exists():
        # 先创建目录
        path_directory = path.parent
        path_directory.mkdir(parents=True, exist_ok=True)
        # 再创建文件
        path.touch(exist_ok=True)


def complete_error(
    error: ParseError, response: Response, contains_response_body: bool = True
):
    """
    补充部分信息
    :param contains_response_body: 是否赋值 body
    :param error:
    :param response:
    :return:
    """
    error.response_status = response.status
    error.response_body = response.text if contains_response_body else ""
    error.url = response.url
    if len(error.exc_info) == 0:
        error.exc_info = traceback.format_tb(error.__traceback__)


class ParseErrorHandlerMiddleware:
    """解析错误统一处理中间件"""

    LOG_FILE_NAME = "parse_errors.log"

    JSON_FILE_NAME = "parse_errors.json"

    PICKLE_FILE_NAME = "parse_errors.pickle"

    def __init__(self, crawler: Crawler):
        self.exceptions: Union[dict[str, Any], None] = None
        self.articleIds: Union[set[str], None] = None

        settings = crawler.settings
        self.contains_response_body = settings.get(
            "PARSE_ERROR_CONTAINS_RESPONSE_BODY", True
        )
        self.log_format = settings.get("LOG_FORMAT")
        self.log_dateformat = settings.get("LOG_DATEFORMAT")
        self.log_dir = settings.get("PARSE_ERROR_LOG_DIR", "logs")
        self.log_path = os.path.join(self.log_dir, self.LOG_FILE_NAME)
        self.pickle_path = os.path.join(self.log_dir, self.PICKLE_FILE_NAME)
        self.json_path = os.path.join(self.log_dir, self.JSON_FILE_NAME)

        crawler.stats.set_value("parse_error/total", 0)
        crawler.stats.set_value("parse_error/duplicated", 0)
        crawler.stats.set_value("parse_error/non_repeat", 0)
        logger.debug(
            f"Using config(PARSE_ERROR_LOG_DIR={self.log_dir})",
        )
        self.closed = True

    @classmethod
    def from_crawler(cls, crawler: Crawler):
        obj = cls(crawler)
        crawler.signals.connect(obj.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(obj.spider_closed, signal=signals.spider_closed)
        return obj

    def _init_logger(self):
        ensure_file_exist(self.log_path)
        handler = logging.FileHandler(
            filename=self.log_path,
            encoding="utf-8",
            mode="a",
        )
        handler.addFilter(lambda record: record.levelno >= logging.DEBUG)
        fmt = logging.Formatter(fmt=self.log_format, datefmt=self.log_dateformat)
        handler.setFormatter(fmt)
        logger.addHandler(handler)

    def _load_pickle(self):
        try:
            with open(self.pickle_path, "rb") as f:
                self.exceptions = pickle.load(f)
            self.articleIds = self.exceptions["ids"]
        except Exception as e:
            logger.error(e)
            self.exceptions = {
                "error": list[ParseError](),
                "ids": set[str](),
            }
            self.articleIds = self.exceptions["ids"]

    def spider_opened(self):
        self.closed = False
        self._init_logger()
        try:
            self._load_pickle()
            logger.debug(
                f"pickle load from `{self.pickle_path}` successfully, total {len(self.exceptions['error'])} records"
            )
        except Exception as e:
            logger.warning(e)

    def _dumps_pickle(self):
        with open(self.pickle_path, "wb") as f:
            pickle.dump(self.exceptions, f)

    def _write_json(self):
        ensure_file_exist(self.json_path)
        json_data = [d.to_dict() for d in self.exceptions.get("error", [])]
        with open(self.json_path, "w", encoding="utf-8") as f:
            json.dump(json_data, f, indent=4, ensure_ascii=False)

    def spider_closed(self):
        """
        在 Spider 关闭的时候将数据写入日志文件中
        :return:
        """
        if self.closed:
            return
        self.closed = True

        logger.debug(self.exceptions)

        try:
            self._dumps_pickle()
            logger.debug("pickle dumps successfully!")
        except Exception as e:
            logger.warning("dumps to file failed!")
            logger.exception(e)

        try:
            self._write_json()
            logger.debug("write json successfully!")
        except Exception as e:
            logger.warning("write json failed!")
            logger.exception(e)

    def _check_url_duplicated(self, url: str) -> str | None:
        """
        检查url是否重复，通过判断articleId
        :param url:
        :return: 如果不重复，则返回对应的articleId，否则返回one
        """
        parsed_url = urllib.parse.urlparse(url)
        param = urllib.parse.parse_qs(parsed_url.query)
        if "articleId" not in param:
            return None
        article_id = param["articleId"][0]
        return None if (article_id in self.articleIds) else article_id

    def process_spider_exception(
        self, response: Response, exception: BaseException, spider: Spider
    ):
        # 处理 ParseError
        if isinstance(exception, ParseError):
            complete_error(exception, response, self.contains_response_body)
            url = exception.url
            spider.crawler.stats.inc_value("parse_error/total")
            articleId = self._check_url_duplicated(url)
            if not articleId:
                logger.warning(
                    f"catch a duplicated parse error:\n"
                    f"url: {exception.url}\n"
                    f"msg: {exception.message}"
                )
                spider.crawler.stats.inc_value("parse_error/duplicated")
            else:
                logger.warning(
                    f"catch a parse error:\n"
                    f"url: {exception.url}\n"
                    f"id: {urllib.parse.unquote(articleId)}\n"
                    f"msg: {exception.message}"
                )
                spider.crawler.stats.inc_value("parse_error/non_repeat")
                self.exceptions["error"].append(exception)
                self.articleIds.add(articleId)
            logger.exception(exception)
            return []

    def __del__(self):
        # 防止突然停止没有写入日志
        self.spider_closed()
