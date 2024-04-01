import datetime
import json
import logging
import os
import random
import re

from scrapy import signals, Request, Spider
from scrapy.crawler import Crawler
from scrapy.http import Response


class AnnouncementFilterMiddleware:
    """
    过滤已经爬取过的公告
    根据存储在redis中的articleId进行判断
    """
    logger = logging.getLogger("AnnouncementFilterMiddleware")

    @classmethod
    def from_crawler(cls, crawler: Crawler):
        return cls()

    def process_request(self, request: Request, spider):
        # TODO: redis 中判断是否存在已经爬取过的id
        return None


class UserAgentMiddleware(object):
    """
    Middleware 用于加入随机的 UA 请求头
    """

    user_agents = [
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 "
        "Safari/605.1.1",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.3",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.3",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/117.",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.3",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 "
        "Safari/537.36 Config/91.2.2025.1",
        "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 "
        "Safari/537.36 Edg/121.0.0.",
        "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Mobile Safari/537.3",
        "Mozilla/5.0 (Linux; Android 13; SAMSUNG SM-A326B) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/23.0 "
        "Chrome/115.0.0.0 Mobile Safari/537.3",
        "Mozilla/5.0 (Linux; Android 11; moto e20 Build/RONS31.267-94-14) AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/121.0.6167.178 Mobile Safari/537.3",
        "Mozilla/5.0 (Linux; Android 14; SAMSUNG SM-A236B) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/23.0 "
        "Chrome/115.0.0.0 Mobile Safari/537.3",
        "Mozilla/5.0 (Linux; Android 13; 22101320G Build/TKQ1.221114.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) "
        "Version/4.0 Chrome/108.0.5359.128 Mobile Safari/537.3",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 "
        "Safari/537.36 OPR/108.0.0.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:115.0) Gecko/20100101 Firefox/115.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 "
        "Safari/537.36 Edg/121.0.2277.128"
    ]

    @classmethod
    def from_crawler(cls, crawler: Crawler):
        instance = cls()
        extra_user_agent = crawler.settings.get("extra_user_agents", [])
        instance.user_agents += extra_user_agent
        return instance

    def process_request(self, request: Request, spider):
        if not request.headers.get("User-Agent", None):
            request.headers['User-Agent'] = random.choice(self.user_agents)
        return None


class SpiderExceptionHandlerMiddleware(object):

    def process_exception(self, exception: Exception, spider: Spider):
        pass


def prettify_json(json_data: str | dict) -> str:
    if json_data:
        if isinstance(json_data, str):
            return json.dumps(
                json.loads(json_data),
                ensure_ascii=False,
                indent=4,
                sort_keys=True
            )
        elif isinstance(json_data, dict):
            return json.dumps(
                json_data,
                ensure_ascii=False,
                indent=4,
                sort_keys=True
            )
    return ""


class ResponseDebugMiddleware(object):
    """
    用于调试 response 的中间件
    """
    DEBUG = False
    PRE_CLEAR = False

    GENERATE_LOG_FILE_COUNT = 0

    logger = logging.getLogger("ResponseDebugMiddleware")

    @classmethod
    def from_crawler(cls, crawler: Crawler):
        instance = cls()
        is_debug = crawler.settings.get("RESPONSE_DEBUG", False)
        instance.DEBUG = is_debug
        pre_clear = crawler.settings.get("RESPONSE_PRE_CLEAR", False)
        instance.PRE_CLEAR = pre_clear
        crawler.signals.connect(instance.stop, signal=signals.engine_stopped)
        instance.init()
        return instance

    def init(self):
        """
        初始化，
        :return:
        """
        self.logger.info(f"===> ResponseDebugMiddleware started(is_debug={self.DEBUG}, pre_clear={self.PRE_CLEAR})")
        if self.DEBUG and self.PRE_CLEAR:
            dirs = os.listdir('.')
            cnt = 0
            for d in dirs:
                if re.match(r'[0-9]*\.txt', d):
                    os.remove(os.path.join(os.curdir, d))
                    cnt += 1
            self.logger.info(f'===> clear existed {cnt} log files.')

    def process_response(self, request: Request, response: Response, spider: Spider):
        if self.DEBUG:
            now_timestamp = int(datetime.datetime.now().timestamp())
            with open(f"{now_timestamp}.txt", "w", encoding='utf-8') as f:
                f.write(f'Request:\n{request.method} {request.url}\n')
                f.write(f'body: {prettify_json(request.body.decode())}\n')
                f.write(f"headers: {prettify_json(request.headers.to_string())}\n")
                f.write(f"meta: {prettify_json(request.meta)}\n")
                f.write('-----\n\n')
                f.write(f'Response:\n{response.status}\n')
                f.write(prettify_json(response.text))
            self.GENERATE_LOG_FILE_COUNT += 1
        return response

    def stop(self):
        if self.DEBUG:
            self.logger.info(f"===> ResponseDebugMiddleware stopped. Total log count: {self.GENERATE_LOG_FILE_COUNT}")


class ParseError(BaseException):
    """自定义解析错误"""

    def __init__(
            self,
            msg: str,
            content: str = '',
            url: str = '',
            error: BaseException | None = None,
            timestamp: int = int(datetime.datetime.now().timestamp()),
            request: Request | None = None,
            response: Response | None = None
    ):
        """
        :param msg: 出错原因
        :param url: 出错 url
        :param content: 解析内容
        :param error: 上一层异常
        :param timestamp: 出现时间戳
        :param request: 所属请求
        :param response: 所属响应
        """
        self.message = msg
        self.content = content
        self.url = url
        self.timestamp = timestamp
        self.error = error
        self.request = request
        self.response = response

    def __str__(self):
        return f"""
        ParseError: 
        \tmsg: {self.message}, 
        \tcontent: {self.content},
        \turl: {self.url}, 
        \ttimestamp: {self.timestamp}
        \terror: {self.error.__repr__()}
        \trequest: {self.request}, 
        \tresponse: {self.response}
        """.strip()


class ParseErrorHandlerMiddleware(object):
    """
    解析错误中间件
    """

    def process_spider_exception(self, response: Response, exception: BaseException, spider: Spider):
        if isinstance(exception, ParseError):
            # TODO: 输出日志，保存到本地
            error = spider.logger.error
            error(f'===> ParseError: {exception}')
        return None
