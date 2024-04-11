import functools
import inspect
import logging
import threading
import time
from typing import Union

# ============ DEBUG 统计数据 ==========

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

__all__ = ["debug_status", "function_stats", ""]


# ================ STATS ==============
class Table:
    """
    表格，用于输出
    """

    __ALIGNS = {
        "left": "<",
        "center": "^",
        "right": ">",
    }

    def __init__(
        self,
        table_name: str,
        data: list,
        col_names: list[str],
        col_widths: Union[list[int], None],
        align: str = "center",
        auto_width: bool = False,
    ):
        """

        :param table_name: 表明
        :param data: 数据，格式 list[list[x,x,x...]]
        :param col_names: 列名
        :param col_widths: 列宽，当 auto_width 为 True 时该值失效
        :param align: 对齐方向
        :param auto_width: 自动宽度
        """
        self.table_name = table_name
        self.table_data = data
        self.col_names = col_names
        self.col_widths = col_widths
        try:
            self.align = self.__ALIGNS[align]
        except KeyError:
            raise ValueError(f"align must be one of {list(self.__ALIGNS.keys())}")

        self.auto_width = auto_width
        if auto_width:
            self.col_widths = [max(len(str(d)) + 4 for d in col) for col in zip(*data)]
        else:
            if not self.col_widths:
                raise ValueError("col_widths must be set when auto_width is False")

    @staticmethod
    def omit_str(string, max_width: int):
        """
        截断字符串
        :param string:
        :param max_width:
        :return:
        """
        if not isinstance(string, str):
            string = str(string)
        str_len = len(string)
        if str_len > max_width:
            return string[: max_width - 3] + "..."
        else:
            return string

    def __str__(self):
        """
        打印表格
        :return:
        """
        # 表格的宽度（不包括左右边框的宽度）
        table_width = sum(self.col_widths) + len(self.col_widths) - 1
        # 分割线
        split_line = f"+{'—' * table_width}+"
        # 标题
        title_line = f"|{self.table_name:^{table_width}}|"
        # 列名
        col_name_line = ""
        for content, width in zip(self.col_names, self.col_widths):
            col_name_line += f"|{self.omit_str(content, width):{self.align}{width}}"
        else:
            col_name_line += "|"

        content_line = ""
        for d in self.table_data:
            for content, width in zip(d, self.col_widths):
                content_line += f"|{self.omit_str(content, width):{self.align}{width}}"
            else:
                content_line += "|\n"
                content_line += split_line + "\n"

        return (
            f"\n{split_line}\n"
            f"{title_line}\n"
            f"{split_line}\n"
            f"{col_name_line}\n"
            f"{split_line}\n"
            f"{content_line}\n"
        )


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
        t = Table(
            table_name="debug_stats",
            data=[
                [fun, running, cnt, running / cnt]
                for fun, (running, cnt) in list(self.func_running_time.items())
            ],
            col_names=["func_name", "running_time", "count", "avg"],
            col_widths=None,
            align="center",
            auto_width=True,
        )
        logger.info(t)


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

        def start_stats(*args, **kwargs):
            """
            开始统计
            :param args:
            :param kwargs:
            :return:
            """
            if DEBUG_STATUS:
                # 记录 函数开始时间
                log_info = f"DEBUG INFO: {func.__qualname__} started."
                if log_params:
                    if len(args) != 0:
                        log_info += f"\nargs: {args}"
                    if len(kwargs) != 0:
                        kwargs_str = "\n\t".join(
                            [f"{k}: {v}" for k, v in kwargs.items()]
                        )
                        log_info += f"\nkwargs:\n\t{kwargs_str}"
                _logger.debug(log_info)
                nonlocal start_time
                start_time = time.time()

        def finish_stats():
            """
            结束统计
            :return:
            """
            if DEBUG_STATUS:
                running_time = time.time() - start_time
                _logger.debug(
                    f"DEBUG INFO: {func.__qualname__} running {running_time} s."
                )
                # 统计函数运行时间
                stat_collector.inc_function(
                    func_name=func.__qualname__, running_time=running_time
                )

        # 生成器函数
        if inspect.isgeneratorfunction(func):

            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                start_stats(*args, **kwargs)
                # 运行被修饰函数
                try:
                    for item in func(*args, **kwargs):
                        yield item
                finally:
                    finish_stats()

        else:

            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                start_stats(*args, **kwargs)
                try:
                    return func(*args, **kwargs)
                finally:
                    finish_stats()

        return wrapper

    return decorator


def log_stats_collector():
    """
    输出统计信息
    :return:
    """
    if DEBUG_STATUS:
        stat_collector.log_stats()
