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
from constant import constants
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


def complete_error(error: ParseError, response: Response):
    """
    补充部分信息
    :param error:
    :param response:
    :return:
    """
    if not error.is_win:
        error.is_win = response.meta.get(constants.KEY_PROJECT_IS_WIN_BID, None)
    # 出现错误的url
    if not error.article_id:
        param = urllib.parse.urlparse(url=response.url).query
        param = urllib.parse.parse_qs(param)
        error.article_id = param.get("articleId", None)[0]
    # 所有公告id
    if not error.article_ids:
        error.article_ids = response.meta.get(
            constants.KEY_PROJECT_RESULT_ARTICLE_ID, None
        )
        if not error.article_ids:
            error.article_ids = response.meta.get(
                constants.KEY_PROJECT_PURCHASE_ARTICLE_ID, None
            )
        else:
            error.article_ids.append("|")
            error.article_ids.extend(
                response.meta.get(constants.KEY_PROJECT_PURCHASE_ARTICLE_ID, None)
            )
    # 最开始的id
    if not error.start_article_id:
        error.start_article_id = response.meta.get(
            constants.KEY_DEV_START_RESULT_ARTICLE_ID, None
        )
    # 解析过后的id标记
    if error.parsed_article_id == 0:
        error.parsed_article_id = response.meta.get(
            constants.KEY_DEV_PARRED_RESULT_ARTICLE_ID, 0
        )

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

        crawler.stats.set_value(constants.StatsKey.PARSE_ERROR_TOTAL, 0)
        crawler.stats.set_value(constants.StatsKey.PARSE_ERROR_DUPLICATED, 0)
        crawler.stats.set_value(constants.StatsKey.PARSE_ERROR_NON_DUPLICATED, 0)
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
            exception: ParseError
            complete_error(exception, response)
            url = response.url
            # 总数+1
            spider.crawler.stats.inc_value(constants.StatsKey.PARSE_ERROR_TOTAL)
            article_id = self._check_url_duplicated(url)
            if not article_id:
                logger.warning(
                    f"catch a duplicated parse error:\n"
                    f"id: {exception.article_id}\n"
                    f"msg: {exception.message}"
                )
                # 重复+1
                spider.crawler.stats.inc_value(
                    constants.StatsKey.PARSE_ERROR_DUPLICATED
                )
            else:
                logger.warning(
                    f"catch a parse error:\n"
                    f"id: {exception.article_id}\n"
                    f"msg: {exception.message}"
                )
                # 非重复+1
                spider.crawler.stats.inc_value(constants.StatsKey.PARSE_ERROR_NON_DUPLICATED)
                self.exceptions["error"].append(exception)
                self.articleIds.add(article_id)
            logger.exception(exception)
            return []

    def __del__(self):
        # 防止突然停止没有写入日志
        self.spider_closed()
