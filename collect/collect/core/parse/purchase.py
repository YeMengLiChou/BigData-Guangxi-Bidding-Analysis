import json
import logging
import re
from typing import Union

from collect.collect.core.error import SwitchError
from collect.collect.core.parse import common, AbstractFormatParser
from collect.collect.core.parse.errorhandle import raise_error
from collect.collect.middlewares import ParseError
from utils import debug_stats as stats, symbol_tools
from constant import constants

logger = logging.getLogger(__name__)


class StandardFormatParser(AbstractFormatParser):
    """
    标准格式文件的解析
    """

    # 解析基本情况的正则表达式
    PATTERN_PROJECT_INFO = re.compile(
        r"项目编号[:：](\S+)(?:\d\.)?项目名称[:：](\S+?)(?:\d\.)?(?:采购方式[:：]\S+)?(?:采购)?预算总?金额\S*?[:：]\D*?(\d+("
        r"?:\.\d*)?)"
    )
    # 解析标项信息的正则表达式
    PATTERN_BIDDING = re.compile(
        r"(?:标项(\S{1,2}))?标项名称[:：](\S+?)数量:\S+?预算金额\S*?[:：](\d+(?:\.\d*)?)"
    )

    @staticmethod
    @stats.function_stats(logger)
    def parse_project_base_situation(string: str) -> dict:
        """
        解析 项目基本情况
        :param string:
        :return:
        """
        # 去掉空白字符，避免正则匹配失败
        string = symbol_tools.remove_all_spaces(string)

        # 分离为两部分，一部分是前面的基本信息，另一部分是后面的标项信息
        split_idx = string.index("采购需求")
        prefix, suffix = string[:split_idx], string[split_idx:]

        data = dict()
        bidding_items = []
        data[constants.KEY_PROJECT_BID_ITEMS] = bidding_items

        total_budget: Union[float, None] = None
        # 正则表达式匹配基本信息
        if match := StandardFormatParser.PATTERN_PROJECT_INFO.search(prefix):
            # 项目编号
            data[constants.KEY_PROJECT_CODE] = match.group(1)
            # 项目名称
            data[constants.KEY_PROJECT_NAME] = match.group(2)
            # 总预算
            total_budget = float(match.group(3))
            data[constants.KEY_PROJECT_TOTAL_BUDGET] = total_budget
            for d in match.groups():
                if d is None:
                    raise ParseError(
                        msg="基本情况解析失败：其中一项/多项为None", content=[string]
                    )
        else:
            raise ParseError(msg="基本情况解析失败：匹配失败", content=[string])

        if match := StandardFormatParser.PATTERN_BIDDING.findall(suffix):
            if len(match) == 0:
                raise ParseError(msg="基本情况解析失败：无标项信息", content=[string])
            for m in match:
                # 标项编号
                item_index = 1
                index, name, budget = m

                if index is None or name is None or budget is None:
                    raise ParseError(msg="标项解析失败", content=[string])

                # 空串
                if not index:
                    index = item_index
                else:
                    # 阿拉伯数字
                    if index.isdigit():
                        index = int(index)
                    else:
                        # 中文数字
                        index = common.translate_zh_to_number(index)

                item = common.get_template_bid_item(
                    is_win=False, index=index, name=name
                )
                item[constants.KEY_BID_ITEM_BUDGET] = float(budget)
                bidding_items.append(item)

                item_index += 1
                total_budget -= float(budget)
        else:
            raise ParseError(
                msg="基本情况解析失败：标项信息匹配失败", content=[string]
            )

        if total_budget is None or total_budget > 1e-5:
            raise ParseError(msg="标项预算合计与总预算不符", content=[string])

        return data

    @staticmethod
    @stats.function_stats(logger)
    def parse_project_contact(part: list[str]) -> dict:
        return common.parse_contact_info("".join(part))


def check_useful_part(_: bool, title: str) -> Union[int, None]:
    """
    检查是否包含有用信息的标题
    :param _: (无用，为了统一接口）
    :param title:
    :return:
    """
    if "项目基本情况" in title:
        return constants.PartKey.PROJECT_SITUATION
    return None


@stats.function_stats(logger)
def parse_html(html_content: str):
    """
    解析 采购公告 的详情信息
    :param html_content:
    :return:
    """
    result = common.parse_html(html_content=html_content)
    parts: Union[dict[int, list[str]], None] = None
    # 将 result 划分为 若干个部分
    try:
        parts = common.split_content_by_titles(
            result=result,
            is_win_bid=False,
            check_title=check_useful_part,
        )
        # print(json.dumps(parts, ensure_ascii=False, indent=4))
    except BaseException as e:
        raise_error(error=e, msg="解析 parts 出现未完善情况", content=result)

    parts_length = len(parts)
    try:
        if parts_length >= 1:
            res = _parse(parts)

            # 没有标项信息则切换
            if len(res.get(constants.KEY_PROJECT_BID_ITEMS, [])) == 0:
                raise SwitchError("该采购公告没有标项信息")

            return res
        else:
            raise ParseError(
                msg="解析 parts 出现不足情况",
                content=result,
            )
    except SwitchError as e:
        raise e
    except BaseException as e:
        raise_error(
            error=e,
            msg="解析 __parse_standard_format 失败",
            content=["\n".join(v) for _, v in parts.items()],
        )


@stats.function_stats(logger)
def _parse(parts: dict[int, list[str]]):
    """
    解析 parts 部分
    :param parts:
    :return:
    """

    data = dict()
    # 项目基本情况
    if constants.PartKey.PROJECT_SITUATION in parts:
        data.update(
            StandardFormatParser.parse_project_base_situation(
                "".join(parts[constants.PartKey.PROJECT_SITUATION])
            )
        )

    return data


if __name__ == "__main__":
    content = ""
    print(json.dumps(parse_html(content), indent=4, ensure_ascii=False))
