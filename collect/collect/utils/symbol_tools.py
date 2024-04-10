from typing import Union


def get_comma_symbol(s: str) -> Union[str, None]:
    """
    获取中文/英文的逗号
    :return:
    """
    if "," in s:
        return ","
    elif "，" in s:
        return "，"
    else:
        return None


def get_symbol(s: str, coordinators: list[str]) -> Union[str, None]:
    """
    从 coordinators 中获取 s 中存在的符号
    :param s:
    :param coordinators:
    :return:
    """
    for sym in coordinators:
        if sym in s:
            return sym
    else:
        return None


def get_parentheses_position(s: str) -> tuple[int, int]:
    """
    获取中文/英文的括号位置
    :return:
    """
    if "(" in s:
        return s.find("("), s.find(")")
    elif "（" in s:
        return s.find("（"), s.find("）")
    else:
        return -1, -1


def endswith_colon_symbol(s: str) -> bool:
    """
    判断字符串是否以冒号结尾
    :param s:
    :return:
    """
    s = s.strip()
    return s.endswith("：") or s.endswith(":")
