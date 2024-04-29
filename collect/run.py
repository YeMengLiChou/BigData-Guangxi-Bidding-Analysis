import importlib
import logging
import sys
from logging.handlers import RotatingFileHandler

import coloredlogs
import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings
from scrapy.utils import log

from utils.handlers import HourRotationFileHandler


class LevelFilter(logging.Filter):
    """
    设置最低的日志等级
    """

    def __init__(self, level: int):
        logging.Filter.__init__(self)
        if level not in (
            logging.DEBUG,
            logging.INFO,
            logging.WARNING,
            logging.ERROR,
            logging.CRITICAL,
        ):
            raise ValueError(
                "level must be one of DEBUG, INFO, WARNING, ERROR, CRITICAL"
            )
        self.level = level

    def filter(self, record: logging.LogRecord) -> bool:
        if record.levelno >= self.level:
            return True
        return False


def _get_project_settings(module_path: str) -> Settings:
    """
    读取项目的 settings.py
    :param module_path:
    :return:
    """

    # 将 settings.py 中的路径字符串拼接为新的路径
    split_path = module_path.split(".")
    new_prefix = ".".join(split_path[:-2])
    old_prefix = ".".join(split_path[-2:-1]) + "."

    def modify(value):
        if isinstance(value, str) and value.startswith(old_prefix):
            return ".".join([new_prefix, value])
        elif isinstance(value, list):
            return [modify(item) for item in value]
        elif isinstance(value, dict):
            return {modify(k): v for k, v in value.items()}
        else:
            return value

    # 导入 settings.py 且创建 settings 实例
    settings_module = importlib.import_module(module_path)
    settings = Settings()
    for key in dir(settings_module):
        if key.isupper():
            settings.set(
                key, value=modify(getattr(settings_module, key)), priority="project"
            )

    return settings


def configure_logging(settings: Settings):
    """
    配置日志，控制台输出着色
    :param settings:
    :return:
    """
    enabled = settings.getbool("LOG_ENABLED")  # 是否启用日志
    if not enabled:
        return

    filename = settings.get("LOG_FILE")  # 输出的日志文件名称

    log_format = settings.get("LOG_FORMAT")
    log_dateformat = settings.get("LOG_DATEFORMAT")

    level = settings.get("LOG_LEVEL")
    log_type = settings.get("LOG_FILE_TYPE", None)
    # 输出到文件就不需要着色
    if filename:
        file_mode = "a" if settings.getbool("LOG_FILE_APPEND") else "w"  # 日志文件模式
        encoding = settings.get("LOG_ENCODING")  # 日志文件编码
        backup_count = settings.getint("LOG_FILE_BACKUP_COUNT")
        # 没有指定
        if log_type is None:
            handler = logging.FileHandler(
                filename=filename, mode=file_mode, encoding=encoding
            )

        elif log_type == "time":
            unit = settings.get("LOG_FILE_ROTATION_UNIT", "hour")
            interval = settings.getint("LOG_FILE_INTERVAL", 1)
            handler = HourRotationFileHandler(
                filename=filename,
                encoding=encoding,
                unit=unit,
                interval=interval,
                backupCount=backup_count,
                utc=False,
            )
        elif log_type == "size":
            max_bytes = settings.getint("LOG_FILE_MAX_BYTES")
            handler = RotatingFileHandler(
                filename=filename,
                mode=file_mode,
                encoding=encoding,
                maxBytes=max_bytes,
                backupCount=backup_count,
            )
        else:
            raise ValueError("`LOG_FILE_TYPE` must be time、 size or None")

        formatter = logging.Formatter(  # 设置日志格式
            fmt=log_format, datefmt=log_dateformat
        )
        handler.setFormatter(formatter)
        if settings.getbool("LOG_SHORT_NAMES"):  # 是否缩写
            handler.addFilter(log.TopLevelFormatter(["scrapy"]))

        handler.addFilter(LevelFilter(level=logging.INFO))
        logging.basicConfig(
            level=level,
            handlers=[handler],
        )

    else:
        coloredlogs.install(
            level=level,
            stream=sys.stdout,
            datefmt=log_dateformat,
            fmt=log_format,
            milliseconds=True,
            level_styles={
                "critical": {"color": 9},
                "error": {"color": 1},
                "warn": {"color": 11},
                "info": {"color": 250},
                "debug": {"color": 117},
            },
            field_styles={
                "asctime": {"color": 227},
                "name": {"color": 219},
                "levelname": {
                    "color": 147,
                    "bold": True,
                    "bright": True,
                    "italic": True,
                    "underline": True,
                },
            },
            isatty=True,
        )


def _run_spider(spider_name: str, _settings: Settings):
    """
    启动爬虫
    :param spider_name:
    :param _settings:
    :return:
    """
    configure_logging(_settings)
    crawler_process = CrawlerProcess(_settings, install_root_handler=False)
    crawl_defer = crawler_process.crawl(spider_name)
    if getattr(crawl_defer, "result", None) is not None and issubclass(
        crawl_defer.result.type, Exception
    ):
        exitcode = 1
    else:
        crawler_process.start()

        if (
            crawler_process.bootstrap_failed
            or hasattr(crawler_process, "has_exception")
            and crawler_process.has_exception
        ):
            exitcode = 1
        else:
            exitcode = 0
    sys.exit(exitcode)


def start(spider_name: str, module_path: str):
    settings = _get_project_settings(module_path)
    _run_spider(spider_name, settings)
