import logging

BOT_NAME = "collect"

SPIDER_MODULES = ["collect.spiders"]
NEWSPIDER_MODULE = "collect.spiders"

# Crawl responsibly by identifying yourself (and your website) on the user-agent
# USER_AGENT = "data_scrapy (+http://www.yourdomain.com)"

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# Configure maximum concurrent requests performed by Scrapy (default: 16)
CONCURRENT_REQUESTS = 24

# Configure a delay for requests for the same website (default: 0)
# See https://docs.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
DOWNLOAD_DELAY = 0

# 下载超时30
DOWNLOAD_TIMEOUT = 30

# 对用一个响应的最大处理item数
CONCURRENT_ITEMS = 64

# 对同一个域名的最大并发请求数
CONCURRENT_REQUESTS_PER_DOMAIN = 16

# 重试次数
RETRY_TIMES = 5

# 最大线程池大小
REACTOR_THREADPOOL_MAXSIZE = 16

# url长度限制
URLLENGTH_LIMIT = 3000

# The download delay setting will honor only one of:
# CONCURRENT_REQUESTS_PER_DOMAIN = 16
# CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
# COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
# TELNETCONSOLE_ENABLED = False

# Override the default request headers:
# DEFAULT_REQUEST_HEADERS = {
#    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
#    "Accept-Language": "en",
# }

# Enable or disable spider middlewares
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
SPIDER_MIDDLEWARES = {
    "collect.middlewares.ParseErrorHandlerMiddleware": 1,
}

# Enable or disable downloader middlewares
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
DOWNLOADER_MIDDLEWARES = {
    "collect.middlewares.ArticleIdFilterDownloadMiddleware": 12,
    "collect.middlewares.UserAgentMiddleware": 100,
    "collect.middlewares.ResponseDebugMiddleware": 100,
    "collect.middlewares.TimeoutProxyDownloadMiddleware": 600,
    "scrapy.downloadermiddlewares.downloadtimeout.DownloadTimeoutMiddleware": 500,
}

# Enable or disable extensions
# See https://docs.scrapy.org/en/latest/topics/extensions.html
EXTENSIONS = {"collect.extensions.LogStats": 300}

# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
    "collect.pipelines.UpdateRedisInfoPipeline": 200,  # redis 更新 item 的数据
    "collect.pipelines.DebugPipeline": 200,  # debug，写入本地
    "collect.pipelines.CollectKafkaPipeline": 300,  # 发送到 kafka
    # "collect.pipelines.DebugWritePipeline": 100,
}

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/autothrottle.html
# AUTOTHROTTLE_ENABLED = True
# The initial download delay
# AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
# AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
# AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
# AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
# HTTPCACHE_ENABLED = True
# HTTPCACHE_EXPIRATION_SECS = 0
# HTTPCACHE_DIR = "httpcache"
# HTTPCACHE_IGNORE_HTTP_CODES = []
# HTTPCACHE_STORAGE = "scrapy.extensions.httpcache.FilesystemCacheStorage"

# Set settings whose default value is deprecated to a future-proof value
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"

LOG_LEVEL = logging.INFO

# LOG_FILE =  "logs/collect/out.log"

# size / time
LOG_FILE_TYPE = "time"

# 最大保留个数
LOG_FILE_BACKUP_COUNT = 50

# 最大文件大小，当 ``LOG_FILE_TYPE`` 设置为 size 生效
# LOG_FILE_MAX_BYTES = 5 * 1024 * 1024

# 生成文件间隔，单位为 ``LOG_FILE_ROTATION``，当 ``LOG_FILE_TYPE`` 设置为 time 生效
LOG_FILE_INTERVAL = 4

# 日志文件生成间隔单位：second / minute / hour / day /
LOG_FILE_ROTATION_UNIT = "hour"

# 自动调节
AUTOTHROTTLE_ENABLED=True

# 下载延迟
AUTOTHROTTLE_START_DELAY=2

# 最大延迟
AUTOTHROTTLE_MAX_DELAY=10

# ======== ResponseDebugMiddleware =================
# 是否设置 ResponseDebugMiddleware 的调试
RESPONSE_DEBUG = False

RESPONSE_DEBUG_LOG_DIR = "logs"

RESPONSE_PRE_CLEAR = True

# ======== ParseErrorHandlerMiddleware =============
PARSE_ERROR_LOG_DIR = "logs"

PARSE_ERROR_CONTAINS_RESPONSE_BODY = False
