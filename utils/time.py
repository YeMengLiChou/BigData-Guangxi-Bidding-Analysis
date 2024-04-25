from datetime import datetime

__months = [0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]


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


def get_days_by_year_and_month(year: int, month: int) -> int:
    """
    根据月份获取月份的天数
    :param year:
    :param month:
    :return:
    """
    if year % 4 == 0 and year % 100 != 0 or year % 400 == 0:
        if month == 2:
            return 29
    return __months[month]


if __name__ == "__main__":
    t = now_timestamp()
    print(dateformat(t))
