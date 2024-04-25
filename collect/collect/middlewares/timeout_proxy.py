import logging

import requests
from requests.exceptions import ProxyError
from scrapy import Request
from twisted.internet.error import TCPTimedOutError, TimeoutError

logger = logging.getLogger(__name__)


class TimeoutProxyDownloadMiddleware:
    """
    超时后使用代理进行获取

    """

    @classmethod
    def from_crawler(cls, crawler):
        return cls()

    def __init__(self):
        self.username = "202404252020545401"
        self.password = "91916481"
        self.api = f"http://www.zdopen.com/ShortProxy/GetIP/?api={self.username}&akey=6d3251d0421790b6&count=1&fitter=2&timespan=2&type=3"

    def fetch_proxy(self) -> dict[str, str] | None:
        res = requests.get(self.api)
        proxy_data = res.json()["data"]["proxy_list"][0]
        proxy_url = f"http://{self.username}:{self.password}@{proxy_data['ip']}:{proxy_data['port']}"
        proxy = {"http": proxy_url, "https": proxy_url}
        res = requests.get(url="https://www.baidu.com/", proxies=proxy, timeout=10)
        if res.status_code == 200:
            return proxy
        else:
            return None

    def process_exceptions(self, request: Request, exception, spider):
        if isinstance(exception, (TimeoutError, TCPTimedOutError, ProxyError)):
            if (times := request.meta.get("proxy_retry_times", 0)) < 2:
                cnt = 0
                while (proxy := self.fetch_proxy()) is None and cnt < 2:
                    cnt += 1
                else:
                    if proxy:
                        new_request = request.copy()
                        new_request.meta["proxy"] = proxy
                        new_request.meta["proxy_retry_times"] = times + 1
                        new_request.priority = 3000000000010
                        logger.info(
                            f"Retry {request.url} {times + 1} times, use proxy.http: {proxy['http']}"
                        )
                        return new_request
            else:
                logger.warning(f"Gave up retrying {request.url}.")
        return None
