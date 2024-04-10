import re

from collect.collect.core.parse.errorhandle import raise_error
from collect.collect.middlewares import ParseError
from collect.collect.utils import calculate

__all__ = [
    "purchase",
    "common",
    "result",
    "AbstractFormatParser",
]


class AbstractFormatParser:
    """
    通用基类，解析所需要的内容
    """

    def __init__(self):
        raise NotImplementedError("AbstractFormatParser is not instantiable")

    @staticmethod
    def parse_win_bid_item_amount(string: str) -> tuple[float, bool]:
        """
        解析中标结果中的项目金额
        :param string:
        :return: 返回 (数值， 是否为百分比)
        """

        def get_unit_with_bracket_symbol(s: str, unit: str) -> str:
            bracket_symbol = ("(", ")") if "(" in s else ("（", "）")
            return f"{bracket_symbol[0]}{unit}{bracket_symbol[1]}"

        # TODO 负责解析项目金额，适应各种格式
        try:
            res = calculate.try_float(string)
            # 格式：全是数字，没有单位
            if res:
                return res, False

            # 格式：数字+单位
            if calculate.startswith_digital(string):
                amount = calculate.parse_string_with_unit(string)
                unit = calculate.parse_unit(string)
                if unit == 0:
                    percent = True
                else:
                    percent = False
                    amount *= unit
                return amount, percent

            #  格式：单项合价（元） ③＝①×②：1278820（元）
            if string.startswith("单项合价"):
                endswith_yuan_unit = string.endswith(
                    get_unit_with_bracket_symbol(string, "元")
                )
                endswith_percent_unit = string.endswith(
                    get_unit_with_bracket_symbol(string, "%")
                )
                if endswith_yuan_unit or endswith_percent_unit:
                    result = re.match(r"[^0-9]*(\d*(\.\d+)?)[^0-9]*", string)
                    if result:
                        amount = float(result.group(1))
                        is_percent = endswith_percent_unit
                        return amount, is_percent
                else:
                    raise_error(
                        ParseError(f"无法解析金额：{string}"), msg="", content=[string]
                    )

            # 最终报价/报价:[金额]（元/%）
            if string.startswith("报价") or string.startswith("最终报价"):
                endswith_yuan_unit = string.endswith(
                    get_unit_with_bracket_symbol(string, "元")
                )
                endswith_percent_unit = string.endswith(
                    get_unit_with_bracket_symbol(string, "%")
                )
                if endswith_yuan_unit or endswith_percent_unit:
                    result = re.match(r"[^0-9]*(\d*(\.\d+)?)[^0-9]*", string)
                    if result:
                        amount = float(result.group(1))
                        is_percent = endswith_percent_unit
                        return amount, is_percent
                else:
                    raise_error(
                        ParseError(f"无法解析金额：{string}"), msg="", content=[string]
                    )

            # 投标总报价（单价×127400×12）:1116024.00(元)
            if string.startswith("投标总报价"):
                colon_symbol = "：" if "：" in string else ":"
                suffix = string.split(colon_symbol)[-1]
                endswith_yuan_unit = suffix.endswith(
                    get_unit_with_bracket_symbol(suffix, "元")
                )
                endswith_percent_unit = suffix.endswith(
                    get_unit_with_bracket_symbol(suffix, "%")
                )
                if endswith_percent_unit or endswith_yuan_unit:
                    result = re.match(r"[^0-9]*(\d*(\.\d+)?)[^0-9]*", suffix)
                    if result:
                        amount = float(result.group(1))
                        is_percent = endswith_percent_unit
                        return amount, is_percent
                else:
                    raise_error(
                        ParseError(f"无法解析金额：{string}"), msg="", content=[string]
                    )

            # 下浮系数：(原始价格-现在价格)/原始价格*100%=下浮百分比
            # 将其改为 100 - 下浮百分比
            if string.startswith("下浮系数"):
                result = re.match(r"[^0-9]*(\d*(\.\d+)?)[^0-9]*", string)
                if result:
                    amount = float(calculate.decimal_subtract("100", result.group(1)))
                    is_percent = True
                    return amount, is_percent

            # 折扣率：就是打几折
            # 将其改为 100 - 折扣百分比
            if "折扣率" in string:
                result = re.match(r"[^0-9]*(\d*(\.\d+)?)[^0-9]*", string)
                if result:
                    amount = float(calculate.decimal_subtract("100", result.group(1)))
                    is_percent = True
                    return amount, is_percent

            raise ParseError(msg=f"标项金额存在未发现的格式: {string}")
        except BaseException as e:
            raise_error(
                msg=f"标项金额存在未发现的格式: {string}", content=[string], error=e
            )

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
    def parse_cancel_reason(part: list[str]):
        """
        解析 废标理由 部分
        :param part:
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
    text = "投标总报价（单价×127400×12）:1116024.00(元)"
    print(AbstractFormatParser.parse_win_bid_item_amount(text))
