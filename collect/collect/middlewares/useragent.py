import random

from scrapy import Request
from scrapy.crawler import Crawler


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
        "Safari/537.36 Edg/121.0.2277.128",
    ]

    @classmethod
    def from_crawler(cls, crawler: Crawler):
        instance = cls()
        extra_user_agent = crawler.settings.get("extra_user_agents", [])
        instance.user_agents += extra_user_agent
        return instance

    def process_request(self, request: Request, spider):
        if not request.headers.get("User-Agent", None):
            request.headers["User-Agent"] = random.choice(self.user_agents)
        return None
