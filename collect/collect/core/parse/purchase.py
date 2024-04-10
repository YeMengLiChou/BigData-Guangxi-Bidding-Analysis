import json
import logging
import time
from typing import Type

from lxml import etree

from collect.collect.core.parse import common, AbstractFormatParser
from collect.collect.utils import log, symbol_tools as sym
from collect.collect.core.parse.errorhandle import raise_error
from collect.collect.middlewares import ParseError
from contant import constants

logger = logging.getLogger(__name__)

try:
    from config.config import settings

    _DEBUG = getattr(settings, "debug.enable", False)
except ImportError:
    _DEBUG = True

if _DEBUG:
    if len(logging.root.handlers) == 0:
        logging.basicConfig(level=logging.DEBUG)


class StandardFormatParser(AbstractFormatParser):
    """
    标准格式文件的解析
    """

    @staticmethod
    def parse_project_base_situation(part: list[str]) -> dict:
        """
        解析 项目基本情况
        :param part:
        :return:
        """
        start_time = 0
        if _DEBUG:
            start_time = time.time()
            logger.debug(f"{log.get_function_name()} started")

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

        try:
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
                    bid_item = dict()
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
                            bid_item[constants.KEY_BID_ITEM_BUDGET] = float(
                                part[idx + 1]
                            )
                            idx += 2
                        else:
                            idx += 1
                    bid_item[constants.KEY_BID_ITEM_INDEX] = bid_item_index
                    bid_item_index += 1
                    bid_items.append(complete_purchase_bid_item(bid_item))
                else:
                    idx += 1
            data[constants.KEY_PROJECT_BID_ITEMS] = bid_items

            return data
        finally:
            if _DEBUG:
                logger.debug(
                    f"{log.get_function_name()} cost: {time.time() - start_time}"
                )

    @staticmethod
    def parse_project_contact(part: list[str]) -> dict:
        """
        解析 以下方式联系 部分
        :param part:
        :return:
        """

        start_time = 0
        if _DEBUG:
            start_time = time.time()
            logger.debug(f"{log.get_function_name()} started")

        def check_information_begin(s: str) -> bool:
            return common.startswith_number_index(s) >= 1

        def check_name(s: str) -> bool:
            startswith_name = s.startswith("名") or (s.find("名") < s.find("称"))
            endswith_colon = s.endswith(":") or s.endswith("：")
            return startswith_name and endswith_colon

        def check_address(s: str) -> bool:
            startswith_address = s.startswith("地") or (s.find("地") < s.find("址"))
            endswith_colon = s.endswith(":") or s.endswith("：")
            return startswith_address and endswith_colon

        def check_person(s: str) -> bool:
            startswith_person = s.startswith("项目联系人") or s.startswith("联系人")
            endswith_colon = s.endswith(":") or s.endswith("：")
            return startswith_person and endswith_colon

        def check_contact_method(s: str) -> bool:
            startswith_contact_method = s.startswith("项目联系方式") or s.startswith(
                "联系方式"
            )
            endswith_colon = s.endswith(":") or s.endswith("：")
            return startswith_contact_method and endswith_colon

        data, n, idx = dict(), len(part), 0
        try:
            while idx < n:
                text = part[idx]
                if check_information_begin(text):
                    # 采购人 / 采购代理机构信息
                    key_word = text[2:]
                    idx += 1
                    info = dict()
                    # 开始解析内容
                    while idx < n and not check_information_begin(part[idx]):
                        # 名称
                        if check_name(part[idx]):
                            info["name"] = part[idx + 1]
                            idx += 2
                        # 地址
                        elif check_address(part[idx]):
                            info["address"] = part[idx + 1]
                            idx += 2
                        # 联系人
                        elif check_person(part[idx]):
                            info["person"] = part[idx + 1].split("、")
                            idx += 2
                        # 联系方式
                        elif check_contact_method(part[idx]):
                            info["contact_method"] = part[idx + 1]
                            idx += 2
                        else:
                            idx += 1

                    # 加入到 data 中
                    if key_word.startswith("采购人"):
                        data[constants.KEY_PURCHASER_INFORMATION] = info
                    elif key_word.startswith("采购代理机构"):
                        data[constants.KEY_PURCHASER_AGENCY_INFORMATION] = info
                else:
                    idx += 1
            return data
        finally:
            if _DEBUG:
                logger.debug(
                    f"{log.get_function_name()} cost: {time.time() - start_time}"
                )


def parse_html(html_content: str):
    """
    解析 采购公告 的详情信息
    :param html_content:
    :return:
    """
    start_time = 0
    if _DEBUG:
        start_time = time.time()
        logger.debug(f"{log.get_function_name()} started")

    result = common.parse_html(html_content=html_content)

    def check_useful_part(title: str) -> bool:
        """
        检查是否包含有用信息的标题
        :param title:
        :return:
        """
        return ("项目基本情况" == title) or ("以下方式联系" in title)

    n, idx, parts = len(result), 0, []
    # 将 result 划分为 若干个部分，每部分的第一个字符串是标题
    try:
        while idx < n:
            # 找以 “一、” 这种格式开头的字符串
            index = common.startswith_chinese_number(result[idx])
            if index != -1:
                result[idx] = result[idx][
                    result[idx].index("、") + 1 :
                ]  # 去掉前面的序号
                if not check_useful_part(title=result[idx]):
                    continue
                pre = idx  # 开始部分
                idx += 1
                # 以 "<中文数字>、“ 形式划分区域
                # 部分可能带有上面的格式，但是最后面带有冒号：
                while idx < n and (
                    common.startswith_chinese_number(result[idx]) == -1
                    or sym.endswith_colon_symbol(result[idx])
                ):
                    idx += 1
                # 将该部分加入
                parts.append(result[pre:idx])
            else:
                idx += 1
    except BaseException as e:
        raise_error(error=e, msg="解析 parts 出现未完善情况", content=result)
        if _DEBUG:
            logger.debug(
                f"{log.get_function_name()} (raise) cost: {time.time() - start_time}"
            )

    parts_length = len(parts)
    try:
        if parts_length >= 2:
            return _parse(parts, parser=StandardFormatParser)
        else:
            raise ParseError(
                msg="解析 parts 出现未完善情况",
                content=["\n".join(part) for part in parts],
            )
    except BaseException as e:
        raise_error(error=e, msg="解析 __parse_standard_format 失败", content=parts)
    finally:
        if _DEBUG:
            logger.debug(f"{log.get_function_name()} cost: {time.time() - start_time}")


def _parse(parts: list[list[str]], parser: Type[AbstractFormatParser]):
    """
    解析 parts 部分
    :param parts:
    :param parser:
    :return:
    """

    # 通过标题来判断是哪个部分
    def is_project_base_situation(s):
        return s == "项目基本情况"

    def is_project_contact(s):
        return "以下方式联系" in s

    data = dict()
    for part in parts:
        title = part[0]
        if is_project_base_situation(title):
            data.update(parser.parse_project_base_situation(part))
        elif is_project_contact(title):
            data.update(parser.parse_project_contact(part))
    return data


if __name__ == "__main__":
    content = \
        ""

    print(json.dumps(parse_html(content), indent=4, ensure_ascii=False))
