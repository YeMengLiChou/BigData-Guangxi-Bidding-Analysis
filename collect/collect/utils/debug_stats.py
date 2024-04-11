import functools
import inspect
import logging
import threading
import time
from typing import Union

# ============ DEBUG 统计数据 ==========

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

__all__ = [
    "debug_status",
    "function_stats",
    ""
]


# ================ STATS ==============


class StatsCollector:

    def __init__(self):
        self.func_running_time = dict[str, list]()

    def inc_function(self, func_name: str, running_time: float):
        """
        统计 函数
        :param running_time:
        :param func_name:
        :return:
        """
        if func_name not in self.func_running_time:
            value = [running_time, 1]
            self.func_running_time[func_name] = value
        else:
            value = self.func_running_time[func_name]
            value[0] += running_time
            value[1] += 1

    def log_stats(self):
        log_info = "\n".join(
            [
                f"{func_name} total:{running_time:}  count: {count}  avg: {running_time / count}"
                for func_name, (running_time, count) in self.func_running_time.items()
            ]
        )
        logger.info(log_info)


stat_collector: Union[StatsCollector, None] = None

# ================ DEBUG ===============

KEY_DEBUG_STATUS = "debug.enable"


def debug_status():
    """
    获取 debug 信息，如果获取不到，默认为 True
    :return:
    """
    try:
        from config.config import settings

        status = getattr(settings, KEY_DEBUG_STATUS, False)
    except ImportError:
        status = True
    return status


DEBUG_STATUS = debug_status()
"""
当前的 debug 状态
"""

LOCK = threading.RLock()

if DEBUG_STATUS:
    with LOCK:
        # 初始化时保证 logger 已经初始化
        if len(logging.root.handlers) == 0:
            logging.basicConfig(level=logging.DEBUG)

        stat_collector = StatsCollector()


def function_stats(_logger: logging.Logger = logger, log_params: bool = False):
    """
    装饰器：用于输出函数的调用状态，在调用前和调用结束后输出调试信息
    :param _logger:
    :param log_params:
    :return:
    """
    def decorator(func):
        start_time = 0
        try:
            def start_stats(*args, **kwargs):
                if DEBUG_STATUS:
                    # 记录 函数开始时间
                    log_info = f"DEBUG INFO: {func.__qualname__} started."
                    nonlocal start_time
                    start_time = time.time()
                    if log_params:
                        if len(args) != 0:
                            log_info += f"\nargs: {args}"
                        if len(kwargs) != 0:
                            kwargs_str = "\n\t".join(
                                [f"{k}: {v}" for k, v in kwargs.items()]
                            )
                            log_info += f"\nkwargs:\n\t{kwargs_str}"
                    _logger.debug(log_info)

            # 生成器函数
            if inspect.isgeneratorfunction(func):
                @functools.wraps(func)
                def wrapper(*args, **kwargs):
                    start_stats(*args, **kwargs)
                    # 运行被修饰函数
                    for item in func(*args, **kwargs):
                        yield item

            else:
                @functools.wraps(func)
                def wrapper(*args, **kwargs):
                    start_stats(*args, **kwargs)
                    return func(*args, **kwargs)
        finally:
            if DEBUG_STATUS:
                running_time = time.time() - start_time
                _logger.debug(
                    f"DEBUG INFO: {func.__qualname__} running {running_time} s."
                )
                # 统计函数运行时间
                stat_collector.inc_function(
                    func_name=func.__qualname__, running_time=running_time
                )
        return wrapper

    return decorator


def log_stats_collector():
    """
    输出统计信息
    :return:
    """
    if DEBUG_STATUS:
        stat_collector.log_stats()
