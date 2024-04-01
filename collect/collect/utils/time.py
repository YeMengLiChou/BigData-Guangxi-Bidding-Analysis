from datetime import datetime


def now_timestamp() -> int:
    """
    返回当前时间对应的毫秒级的时间戳
    :return:
    """
    return int(datetime.now().timestamp())