from datetime import datetime


def now_timestamp() -> int:
    """
    返回当前时间对应的毫秒级的时间戳
    :return:
    """
    return int(datetime.now().timestamp() * 1000)


def from_timestamp(timestamp: int) -> datetime:
    """
    根据时间戳返回对应的时间
    :param timestamp:
    :return:
    """
    return datetime.fromtimestamp(timestamp / 1000)


def dateformat(timestamp: int, _format: str = "%Y-%m-%d-%a %H:%M:%S:%f") -> str:
    """
    根据时间戳返回对应的时间字符串
    :param timestamp:
    :param _format:
    :return:
    """
    return from_timestamp(timestamp).strftime(_format)


if __name__ == "__main__":
    t = now_timestamp()
    print(dateformat(t))
