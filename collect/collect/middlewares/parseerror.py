import json
import logging
import os
import traceback
import urllib.parse
from logging.handlers import RotatingFileHandler
from typing import Union, TextIO

from scrapy import Spider, signals
from scrapy.crawler import Crawler
from scrapy.http import Response

from constants import ProjectKey, CollectDevKey, StatsKey
from utils import time

logger = logging.getLogger(__name__)


class ParseError(Exception):
    """自定义解析错误"""

    def __init__(
            self,
            msg: str,
            article_id: Union[list, None] = None,
            start_article_id: Union[str, None] = None,
            parsed_article_id: int = 0,
            article_ids: Union[list[str], None] = None,
            is_win: Union[bool, None] = None,
            content: Union[list, None] = None,
            error: Union[BaseException, None] = None,
            timestamp: int = time.now_timestamp(),
    ):
        """
        :param msg: 出错原因
        :param article_id: 出错所在 id
        :param parsed_article_id： 解析过的 id
        :param start_article_id 开始的公告
        :param content: 解析内容
        :param error: 上一层异常
        :param timestamp: 出现时间戳
        """
        self.message = msg
        self.content = content
        self.timestamp = timestamp
        self.error = error
        self.article_id = article_id
        self.article_ids = article_ids
        self.start_article_id = start_article_id
        self.parsed_article_id = parsed_article_id
        self.is_win = is_win
        self.exc_info = traceback.format_tb(
            self.error.__traceback__ if self.error else self.__traceback__
        )

    def __str__(self):
        if self.is_win is None:
            result = "unknown"
        elif self.is_win:
            result = "win"
        else:
            result = "not win"
        content = json.dumps(self.content, ensure_ascii=False)
        return (
            f"ParseError(\n"
            f"\tmsg: {self.message}\n"
            f"\tarticle_id: {self.article_id}\n"
            f"\tstart_article_id({result}): {self.start_article_id}\n"
            f"\tparsed: {bin(self.parsed_article_id)[2:]}\n"
            f"\tall_article_ids: {self.article_ids}\n"
            f"\ttimestamp: {time.dateformat(self.timestamp)}\n"
            f"\terror: {'None' if not self.error else self.error.__repr__()}\n"
            f"\tcontent: {content}"
        )

    __repr__ = __str__

    def to_dict(self):
        if self.is_win is None:
            result = "unknown"
        elif self.is_win:
            result = "win"
        else:
            result = "not win"
        return {
            "msg": self.message,
            "article_info": {
                f"error_article": self.article_id,
                f"start_article({result})": self.start_article_id,
                "parsed_article": bin(self.parsed_article_id)[2:],
                "all_article_ids": self.article_ids,
            },
            "timestamp": time.dateformat(self.timestamp),
            "error": self.error.__repr__(),
            "content": self.content,
            "exc_info": self.exc_info,
        }


def complete_error(error: ParseError, response: Response):
    """
    补充部分信息
    :param error:
    :param response:
    :return:
    """
    if not error.is_win:
        error.is_win = response.meta.get(ProjectKey.IS_WIN_BID, None)
    # 出现错误的url
    if not error.article_id:
        param = urllib.parse.urlparse(url=response.url).query
        param = urllib.parse.parse_qs(param)
        error.article_id = param.get("articleId", None)[0]
    # 所有公告id
    if not error.article_ids:
        error.article_ids = response.meta.get(ProjectKey.RESULT_ARTICLE_ID, None)
        if not error.article_ids:
            error.article_ids = response.meta.get(ProjectKey.PURCHASE_ARTICLE_ID, None)
        else:
            if isinstance(error.article_ids, str):
                error.article_ids = [error.article_ids]

            error.article_ids.append("|")
            error.article_ids.extend(
                response.meta.get(ProjectKey.PURCHASE_ARTICLE_ID, None)
            )
    # 最开始的id
    if not error.start_article_id:
        error.start_article_id = response.meta.get(
            CollectDevKey.START_RESULT_ARTICLE_ID, None
        )
    # 解析过后的id标记
    if error.parsed_article_id == 0:
        error.parsed_article_id = response.meta.get(
            CollectDevKey.PARRED_RESULT_ARTICLE_ID, 0
        )

    if len(error.exc_info) == 0:
        error.exc_info = traceback.format_tb(error.__traceback__)


class ParseErrorHandlerMiddleware:
    """
    解析错误统一处理中间件
    """

    LOG_FILE_NAME = "parse_errors.log"

    JSON_FILE_NAME = "parse_errors.json"

    def __init__(self, crawler: Crawler):
        settings = crawler.settings
        self.contains_response_body = settings.get(
            "PARSE_ERROR_CONTAINS_RESPONSE_BODY", True
        )

        self.log_format = settings.get("LOG_FORMAT")
        self.log_dateformat = settings.get("LOG_DATEFORMAT")
        self.log_dir = settings.get("PARSE_ERROR_LOG_DIR", "logs")
        self.log_path = os.path.join(self.log_dir, self.LOG_FILE_NAME)
        self.json_path = os.path.join(self.log_dir, self.JSON_FILE_NAME)

        self.json_fp: Union[TextIO, None] = None
        self.json_first_write = True
        if os.path.exists(self.json_path):
            if os.path.isdir(self.json_path):
                raise ValueError(f"JSON_FILE_NAME`{self.JSON_FILE_NAME}` is a directory!")

            if os.path.getsize(self.json_path) > 0:
                self.json_first_write = False

        crawler.stats.set_value(StatsKey.PARSE_ERROR_TOTAL, 0)
        crawler.stats.set_value(StatsKey.PARSE_ERROR_AMOUNT, 0)
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
        handler = RotatingFileHandler(
            filename=self.log_path,
            backupCount=5,
            maxBytes=1024 * 1024 * 10,  # 10M
            encoding="utf-8",
            mode="a",
        )
        handler.addFilter(lambda record: record.levelno >= logging.DEBUG)
        fmt = logging.Formatter(fmt=self.log_format, datefmt=self.log_dateformat)
        handler.setFormatter(fmt)
        logger.addHandler(handler)

    def spider_opened(self):
        self.closed = False
        self.json_fp = open(self.json_path, "a", encoding="utf-8")
        self._init_logger()

    def spider_closed(self):
        """
        在 Spider 关闭的时候将数据写入日志文件中
        :return:
        """
        if self.closed:
            return
        self.closed = True

    def process_spider_exception(
            self, response: Response, exception: BaseException, spider: Spider
    ):
        # 处理 ParseError
        if isinstance(exception, ParseError):
            exception: ParseError
            complete_error(exception, response)

            # 总数+1
            spider.crawler.stats.inc_value(StatsKey.PARSE_ERROR_TOTAL)

            # 如果包含了候选人公示，则选择不处理
            if response.meta.get(CollectDevKey.RESULT_CONTAINS_CANDIDATE, False):
                return []

            logger.warning(
                f"catch a parse error:\n"
                f"id: {exception.article_id}\n"
                f"msg: {exception.message}"
            )

            logger.exception(exception)

            if self.json_fp:
                if self.json_first_write:
                    self.json_fp.write("[")
                    self.json_first_write = False
                else:
                    self.json_fp.write(",")
                self.json_fp.write(json.dumps(exception.to_dict(), ensure_ascii=False, indent=4))

            return []

    def __del__(self):
        # 防止突然停止没有写入日志
        self.spider_closed()
