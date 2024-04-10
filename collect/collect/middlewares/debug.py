import json
import logging
import os
import re

from scrapy import Request, Spider
from scrapy.crawler import Crawler
from scrapy.http import Response

logger = logging.getLogger(__name__)


def prettify_json(json_data: str | dict) -> str:
    if json_data:
        if isinstance(json_data, str):
            return json.dumps(
                json.loads(json_data), ensure_ascii=False, indent=4, sort_keys=True
            )
        elif isinstance(json_data, dict):
            return json.dumps(json_data, ensure_ascii=False, indent=4, sort_keys=True)
    return ""


def number_to_str(num: int) -> str:
    """
    将数字转换为字符串
    :param num:
    :return:
    """
    s = str(num)
    length = len(s)
    zero_length = 6 - length
    return f'{"0" * zero_length}{s}'


def ensure_dir_exist(directory: str):
    """
    确保目录存在
    :param directory:
    :return:
    """
    if not os.path.exists(directory):
        os.makedirs(directory)


class ResponseDebugMiddleware(object):
    """
    用于调试 response 的中间件
    """

    @classmethod
    def from_crawler(cls, crawler: Crawler):
        obj = cls(crawler)
        return obj

    def __init__(self, crawler: Crawler):
        self.debug = crawler.settings.get("RESPONSE_DEBUG", False)
        self.pre_clear_log = crawler.settings.get("RESPONSE_PRE_CLEAR", False)
        self.log_dir = crawler.settings.get("RESPONSE_DEBUG_LOG_DIR", "logs")
        logger.debug(
            f"Using config("
            f"RESPONSE_DEBUG={self.debug}, "
            f"RESPONSE_PRE_CLEAR={self.pre_clear_log}, "
            f"RESPONSE_DEBUG_LOG_DIR={self.log_dir}"
            f")"
        )

        self.index = 0
        ensure_dir_exist(self.log_dir)
        self.clear_exist_logs()

    def clear_exist_logs(self):
        """
        初始化，
        :return:
        """
        if self.pre_clear_log:
            dirs = os.listdir(self.log_dir)
            cnt = 0
            for d in dirs:
                if re.match(r"debug-[0-9]*\.log", d):
                    os.remove(os.path.join(self.log_dir, d))
                    cnt += 1
            logger.info(f"Cleared existed {cnt} log files.")

    def process_response(self, request: Request, response: Response, spider: Spider):
        if self.debug:
            path = os.path.join(self.log_dir, f"debug-{number_to_str(self.index)}.log")
            with open(path, "w", encoding="utf-8") as f:
                f.write(f"Request:\n{request.method} {request.url}\n")
                f.write(f"body: {prettify_json(request.body.decode())}\n")
                f.write(f"headers: {prettify_json(request.headers.to_string())}\n")
                f.write(f"meta: {prettify_json(request.meta)}\n")
                f.write("-----\n\n")
                f.write(f"Response:\n{response.status}\n")
                f.write(prettify_json(response.text))
            spider.crawler.stats.inc_value("debug/response_log_count")
            self.index += 1
        return response


if __name__ == '__main__':
    log_dir = ".\\..\\..\\..\\logs"
    dirs = os.listdir(log_dir)
    cnt = 0
    for d in dirs:
        if re.match(r"debug-[0-9]*\.log", d):
            os.remove(os.path.join(log_dir, d))
            cnt += 1
    logger.info(f"Cleared existed {cnt} log files.")