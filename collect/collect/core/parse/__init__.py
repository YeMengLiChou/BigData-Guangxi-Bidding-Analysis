import logging
import re
from typing import Iterable, Union

from collect.collect.middlewares import ParseError
from utils import calculate, symbol_tools
from utils import debug_stats as stats

__all__ = [
    "purchase",
    "common",
    "result",
    "AbstractFormatParser",
]

logger = logging.getLogger(__name__)

# 正则表达式预处理，重复使用
PATTERN_NUMBER_UNIT = re.compile(r"(\d+(\.\d*)?)[(（](\S+)[)）]")

# 格式：  (非数字部分)(:)(金额数字)(可能存在的左括号)(非数字部分)(可能存在的右括号)
PATTERN_DESC_NUMBER_UNIT = re.compile(
    r"(\S*)[:：](\d*(?:\.\d*)?)[(（]?([^（(0-9)）]+)[)）]?"
)

# 无冒号
PATTERN_DESC_NUMBER_UNIT_NO_COMMA = re.compile(
    r"([^0-9]*)(\d*(?:\.\d*)?)[(（]?([^（(0-9)）]+)[)）]?"
)

# 中文大写金额（小写金额）
PATTERN_CHINESE_NUMBER = re.compile(
    r"([^0-9]*)[(（]?[¥￥]?(\d*(\.\d*)?)元?[)）]?"
)

# 同PATTERN_DESC_NUMBER_UNIT， 但是单位为元
PATTERN_DESC_NUMBER_YUAN_UNIT = re.compile(r"(\S*)[:：](\d*(?:\.\d*)?)[(（](元)[)）]")


def check_substrings_in_string(string: str, substrings: Iterable[str]) -> bool:
    """
    检查字符串是否包含子字符串
    :param string:
    :param substrings:
    :return:
    """
    for substring in substrings:
        if substring in string:
            return True
    return False


def parse_amount_and_percent(
    string: str, raise_error: bool = True
) -> tuple[Union[float, None], Union[bool, None], bool]:
    """
    解析金额和百分比
    :param raise_error:
    :param string:
    :return:
    """
    string = symbol_tools.remove_all_spaces(string)
    # 格式：数字+单位
    if match := PATTERN_NUMBER_UNIT.fullmatch(string):
        amount_text, unit = match.groups()
        amount = float(amount_text)
        if unit == "元":
            return amount, False, True
        elif unit == "%":
            return amount, True, True
        else:
            if not raise_error:
                return None, None, True

    # 匹配类型： [文字说明] :/： [金额] (/（[单位])/）
    elif (match := PATTERN_DESC_NUMBER_UNIT.fullmatch(string)) or (
        match := PATTERN_DESC_NUMBER_UNIT_NO_COMMA.fullmatch(string)
    ):
        # 前缀描述，金额数字，小数位，单位
        desc, amount_text, unit = match.groups()
        parsed = True

        # 服务总报价、竞标总报价、响应总报价、总价、最终评审价、最后报价、最终报价、投标总价、磋商总报价、投标总报价、单价报价合计、总价大写、金额
        if check_substrings_in_string(
            desc, substrings=("总价", "总报价", "最终", "最后", "合计", "金额", "合价")
        ):
            amount, is_percent = float(amount_text), False
            if check_substrings_in_string(desc, substrings=("系数", "率")):
                # 仅有单位为 % 才能设置（ex 单项合价（元） ③＝①×②/费率:650000(元)）
                if unit == "%":
                    is_percent = True
            if unit == "%":
                is_percent = True

        # 报价、报价大写、投标报价、响应报价、竞标报价、磋商报价、
        elif check_substrings_in_string(desc, substrings=("报价", "单价", "价格")):
            amount, is_percent = float(amount_text), False
            if check_substrings_in_string(desc, substrings=("系数", "率")):
                # 仅有单位为 % 才能设置（ex 单项合价（元） ③＝①×②/费率:650000(元)）
                if unit == "%":
                    is_percent = True
            if unit == "%":
                is_percent = True

        # 检查是否为折扣系数关键词
        elif check_substrings_in_string(desc, substrings=("折扣",)):
            amount, is_percent = float(amount_text), True

        # 收益率、利润率计算
        # 1. 利润率=利润/成本
        elif check_substrings_in_string(desc, substrings=("利润率", "收益率")):
            amount, is_percent = float(amount_text), True
            amount = calculate.decimal_div("100", str(amount))

        # 检查是否为下浮系数关键词
        # 1. 让利系数: （控制价-中标价) / 控制价
        # 2. 优惠率：（基准价-中标价）/基准价
        elif check_substrings_in_string(desc, substrings=("下浮", "优惠率", "让利")):
            amount, is_percent = float(amount_text), True
            amount = float(calculate.decimal_subtract("100", str(amount)))

        # 其他情况
        else:
            # 带有百分比的，一致认为是折扣计算
            if unit == "%":
                amount, is_percent = float(amount_text), True
            elif unit == "元":
                amount, is_percent = float(amount_text), False
                # 不确定该项是否有用
                return amount, is_percent, False
            else:
                parsed = False
                amount, is_percent = -1, False

        if parsed:
            if unit == "%":
                if not is_percent:
                    raise ParseError(
                        f"`{string}` 的单位：`{unit}` 不匹配预期的 %", content=[string]
                    )
                else:
                    return amount, is_percent, True
            elif unit == "元":
                if is_percent:
                    raise ParseError(
                        f"`{string}` 的单位：`{unit}` 不匹配预期的 元", content=[string]
                    )
                else:
                    return amount, is_percent, True
            else:
                raise ParseError(
                    f"无法解析 `{string}` 的 单位：{unit}", content=[string]
                )

    # 匹配类型： [大写金额](¥/￥[小写金额])
    elif match := PATTERN_CHINESE_NUMBER.search(string):
        amount_chinese, amount_text, _ = match.groups()
        return float(amount_text), False, True

    if raise_error:
        raise ParseError(msg=f"无法解析金额：`{string}`", content=[string])
    else:
        return None, None, True


class AbstractFormatParser:
    """
    通用基类，解析所需要的内容
    """

    def __init__(self):
        raise NotImplementedError("AbstractFormatParser is not instantiable")

    @staticmethod
    @stats.function_stats(logger)
    def parse_amount(amount_str: str) -> tuple[float, bool]:
        """
        解析中标结果中的项目金额
        :param amount_str:
        :return: 返回 (数值， 是否为百分比)
        """
        split_sym = symbol_tools.get_symbol(amount_str, (",", "，"), raise_error=False)
        if split_sym:
            strs = amount_str.split(split_sym)
        else:
            strs = [amount_str]

        if len(strs) == 0:
            raise ParseError(f"无法解析金额：{amount_str}", content=[amount_str])

        # 仅有一行
        if len(strs) == 1:
            amount, is_percent, _ = parse_amount_and_percent(strs[0])
            if amount is None:
                raise ParseError(f"无法解析金额：`{amount_str}`", content=[amount_str])
            else:
                return amount, is_percent

        # 不确定数据时，统计所有的金额
        counter = 0
        # 多个数据
        for s in strs:
            amount, is_percent, sure = parse_amount_and_percent(s, raise_error=False)
            if sure:
                if amount is None:
                    continue
                else:
                    return amount, is_percent
            else:
                if not is_percent:
                    counter += amount
        if counter != 0:
            return counter, False

        raise ParseError(f"无法解析金额：`{amount_str}`", content=strs)

    @staticmethod
    def parse_bids_information(part: list[str]) -> list:
        """
        解析中标信息
        :param part:
        :return:
        """
        raise NotImplementedError()

    @staticmethod
    def parse_review_expert(part: list[str]) -> dict:
        """
        解析评审专家信息
        :param part:
        :return:
        """
        raise NotImplementedError()

    @staticmethod
    def parse_project_base_situation(part: list[str]) -> dict:
        """
        解析 项目基本情况 部分
        :param part:
        :return:
        """
        raise NotImplementedError()

    @staticmethod
    def parse_project_contact(part: list[str]) -> dict:
        """
        解析 联系方式 部分
        :param part:
        :return:
        """
        raise NotImplementedError()

    @staticmethod
    def parse_cancel_reason(string: str):
        """
        解析 废标理由 部分
        :param string:
        :return:
        """
        raise NotImplementedError()

    @staticmethod
    def parse_termination_reason(part: list[str]) -> dict:
        """
        解析 终止理由 部分
        :param part:
        :return:
        """
        raise NotImplementedError()


if __name__ == "__main__":
    pass
