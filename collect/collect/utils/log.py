import json as origin_json
from typing import Union, Any

import scrapy


def _pretty_json(data: Union[dict, scrapy.Item]) -> str:
    if isinstance(data, scrapy.Item):
        data = dict(data)
    return origin_json.dumps(data, ensure_ascii=False, indent=2)


def json(
    logger: callable,
    data: Any,
):
    """
    输出 json 格式数据
    :param data:
    :param logger:
    :return:
    """
    logger(_pretty_json(data=data))


def get_function_name():
    """
    获取所在函数的调用名称
    :return:
    """
    from inspect import currentframe, getframeinfo

    frame_info = getframeinfo(currentframe().f_back)
    function_name = frame_info.function
    return function_name


# def debug(start_msg: str = None, end_msg: str = None):
