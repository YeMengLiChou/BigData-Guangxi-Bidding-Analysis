import re
import typing
from typing import Union

PATTERN_REPLACE_SPACE = re.compile(r"[\s\u3000 ]")


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


def get_symbol(
        s: str, candidates: typing.Iterable[str], raise_error: bool = True
) -> Union[str, None]:
    """
    从 coordinators 中获取 s 中存在的符号
    :param s:
    :param candidates: 候选的标点符号
    :param raise_error: 是否抛出异常
    :return:
    """
    for sym in candidates:
        if sym in s:
            return sym
    else:
        if raise_error:
            raise ValueError(f"字符串 `{s}` 中没有 {candidates} 中的符号!")
        else:
            return None


def get_parentheses_position(s: str) -> tuple[int, int]:
    """
    获取 ``s`` 中 中文/英文括号的位置
    :return:
    """
    if "(" in s:
        left_idx = s.find("(")
    elif '（' in s:
        left_idx = s.find('（')
    else:
        left_idx = -1
    if ")" in s:
        right_idx = s.find(")")
    elif "）" in s:
        right_idx = s.find("）")
    else:
        right_idx = -1
    return left_idx, right_idx


def endswith_colon_symbol(s: str) -> bool:
    """
    判断字符串是否以冒号结尾
    :param s:
    :return:
    """
    s = s.strip()
    return s.endswith("：") or s.endswith(":")


def remove_all_spaces(string: str) -> str:
    """
    移除字符串中的所有空格
    :param string:
    :return:
    """
    return PATTERN_REPLACE_SPACE.sub("", string)
