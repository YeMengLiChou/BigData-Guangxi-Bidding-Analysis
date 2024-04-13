import json
import logging
from typing import Union

from collect.collect.core.parse import common, AbstractFormatParser
from collect.collect.core.parse.errorhandle import raise_error
from collect.collect.middlewares import ParseError
from collect.collect.utils import symbol_tools as sym, debug_stats as stats
from constant import constants

logger = logging.getLogger(__name__)


class StandardFormatParser(AbstractFormatParser):
    """
    标准格式文件的解析
    """

    @staticmethod
    @stats.function_stats(logger)
    def parse_project_base_situation(part: list[str]) -> dict:
        """
        解析 项目基本情况
        :param part:
        :return:
        """

        def get_colon_symbol(s: str) -> str:
            if s.endswith(":"):
                return ":"
            if s.endswith("："):
                return "："
            raise ParseError(msg="不以：或: 作为标志符", content=[s])

        def check_project_code(s: str) -> bool:
            return s.startswith("项目编号")

        def check_project_name(s: str) -> bool:
            return s.startswith("项目名称")

        def check_bid_item_quantity(s: str) -> bool:
            return s.startswith("数量") and sym.endswith_colon_symbol(s)

        def check_bid_item_budget(s: str) -> bool:
            return s.startswith("预算金额") and sym.endswith_colon_symbol(s)

        def complete_purchase_bid_item(item: dict) -> dict:
            """
            完善标项信息
            :param item:
            :return:
            """
            if not bid_item.get(constants.KEY_BID_ITEM_QUANTITY, None):
                bid_item[constants.KEY_BID_ITEM_QUANTITY] = (
                    constants.BID_ITEM_QUANTITY_UNCLEAR
                )
            return item

        data, bid_items = dict(), []
        n, idx = len(part), 0
        bid_item_index = 1
        while idx < n:
            text = part[idx]
            # 项目编号
            if check_project_code(text):
                if not sym.endswith_colon_symbol(text):
                    colon_symbol = get_colon_symbol(text)
                    project_code = text.split(colon_symbol)[-1]
                    idx += 1
                else:
                    project_code = part[idx + 1]
                    idx += 2
                data[constants.KEY_PROJECT_CODE] = project_code
            # 项目名称
            elif check_project_name(text):
                if not sym.endswith_colon_symbol(text):
                    colon_symbol = get_colon_symbol(text)
                    project_name = text.split(colon_symbol)[-1]
                    idx += 1
                else:
                    project_name = part[idx + 1]
                    idx += 2
                data[constants.KEY_PROJECT_NAME] = project_name
            # 总预算
            elif "预算总金额" in text:
                budget = float(part[idx + 1])
                data[constants.KEY_PROJECT_TOTAL_BUDGET] = budget
                idx += 2
            # 标项解析
            elif text.startswith("标项名称"):
                bid_item = common.get_template_bid_item(
                    is_win=False, index=bid_item_index
                )
                idx += 1
                # 标项名称
                bid_item[constants.KEY_BID_ITEM_NAME] = part[idx]
                idx += 1
                while idx < n and not part[idx].startswith("标项名称"):
                    # 标项采购数量
                    if check_bid_item_quantity(part[idx]):
                        quantity = part[idx + 1]
                        if quantity == "不限":
                            quantity = constants.BID_ITEM_QUANTITY_UNLIMITED
                        bid_item[constants.KEY_BID_ITEM_QUANTITY] = quantity
                        idx += 2
                    # 标项预算金额
                    elif check_bid_item_budget(part[idx]):
                        bid_item[constants.KEY_BID_ITEM_BUDGET] = float(part[idx + 1])
                        idx += 2
                    else:
                        idx += 1
                bid_item_index += 1
                bid_items.append(complete_purchase_bid_item(bid_item))
            else:
                idx += 1
        data[constants.KEY_PROJECT_BID_ITEMS] = bid_items

        return data

    @staticmethod
    @stats.function_stats(logger)
    def parse_project_contact(part: list[str]) -> dict:
        return common.parse_contact_info(part)


def check_useful_part(title: str) -> Union[int, None]:
    """
    检查是否包含有用信息的标题
    :param title:
    :return:
    """
    if "项目基本情况" in title:
        return constants.KEY_PART_PROJECT_SITUATION
    return None


@stats.function_stats(logger)
def parse_html(html_content: str):
    """
    解析 采购公告 的详情信息
    :param html_content:
    :return:
    """
    result = common.parse_html(html_content=html_content)

    parts = dict[int, list[str]]()
    n, idx, chinese_idx = len(result), 0, 0

    # 将 result 划分为 若干个部分
    try:
        while idx < n:
            # 找以 “一、” 这种格式开头的字符串
            index = common.startswith_chinese_number(result[idx])
            if index > chinese_idx:
                key_part = check_useful_part(title=result[idx])
                if key_part:
                    chinese_idx = index
                    # 开始部分（不算入标题）
                    idx += 1
                    pre = idx
                    # 以 "<中文数字>、“ 形式划分区域
                    # 部分可能带有上面的格式，但是最后面带有冒号：
                    while idx < n and (
                        common.startswith_chinese_number(result[idx]) == -1
                        or sym.endswith_colon_symbol(result[idx])
                    ):
                        idx += 1
                    # 将该部分加入
                    parts[key_part] = result[pre:idx]
                else:
                    idx += 1
            else:
                idx += 1
    except BaseException as e:
        raise_error(error=e, msg="解析 parts 出现未完善情况", content=result)

    parts_length = len(parts)
    try:
        if parts_length >= 1:
            return _parse(parts)
        else:
            raise ParseError(
                msg="解析 parts 出现不足情况",
                content=result,
            )
    except BaseException as e:
        raise_error(
            error=e,
            msg="解析 __parse_standard_format 失败",
            content=["\n".join(v) for _, v in parts],
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
    if constants.KEY_PART_PROJECT_SITUATION in parts:
        data.update(
            StandardFormatParser.parse_project_base_situation(
                parts[constants.KEY_PART_PROJECT_SITUATION]
            )
        )

    return data


if __name__ == "__main__":
    content = ""

    print(json.dumps(parse_html(content), indent=4, ensure_ascii=False))
