import logging
import re

from collect.collect.core.parse import AbstractFormatParser, common
from collect.collect.core.error import SwitchError
from collect.collect.middlewares import ParseError
from collect.collect.utils import debug_stats as stats, symbol_tools
from constant import constants

logger = logging.getLogger(__name__)


@stats.function_stats(logger, log_params=True)
def parse_not_win_bid(parts: dict[int, list[str]]):
    """
    解析 “废标公告” 信息
    :param parts:
    :return:
    """
    data = dict()
    # 解析 联系方式
    if constants.KEY_PART_CONTACT in parts:
        data.update(common.parse_contact_info(parts[constants.KEY_PART_CONTACT]))
    # 解析 评审专家
    if constants.KEY_PART_REVIEW_EXPERT in parts:
        data.update(
            NotWinBidStandardFormatParser.parse_review_expert(
                parts[constants.KEY_PART_REVIEW_EXPERT]
            )
        )
    # 解析 废标理由
    if constants.KEY_PART_NOT_WIN_BID in parts:
        data.update(
            NotWinBidStandardFormatParser.parse_cancel_reason(
                parts[constants.KEY_PART_NOT_WIN_BID]
            )
        )
    # 解析 终止理由
    if constants.KEY_PART_TERMINATION_REASON in parts:
        # 存在一种情况：标的类型是废标，但是实际上是终止，在这里加上去
        data[constants.KEY_PROJECT_IS_TERMINATION] = True
        data.update(
            NotWinBidStandardFormatParser.parse_termination_reason(
                parts[constants.KEY_PART_TERMINATION_REASON]
            )
        )

    # 如果没有对应的数据，那么就赋值默认值
    if not data.get(constants.KEY_PROJECT_REVIEW_EXPERT, None):
        data[constants.KEY_PROJECT_REVIEW_EXPERT] = []
        data[constants.KEY_PROJECT_PURCHASE_REPRESENTOR] = []

    # 如果不是结果公告 或者 没有对应的数据，那么赋默认值
    if (not data.get(constants.KEY_PROJECT_IS_TERMINATION, False)) or (
        not data.get(constants.KEY_PROJECT_TERMINATION_REASON, None)
    ):
        data[constants.KEY_PROJECT_TERMINATION_REASON] = None

    return data


class NotWinBidStandardFormatParser(AbstractFormatParser):
    # 数字序号
    __PATTERN_BID_ITEM_NUMBER_INDEX = re.compile(r"(?:分标|标项|包)(\d+)[:：]?(.*)")
    # 字母序号"
    __PATTERN_BID_ITEM_CHARACTER_INDEX = re.compile(r"([A-Z])(?:分标|标项)[:：]?(.*)")

    @staticmethod
    @stats.function_stats(logger)
    def parse_review_expert(part: list[str]) -> dict:
        """
        解析 评审专家 部分
        :param part:
        :return:
        """
        return common.parse_review_experts(part)

    @staticmethod
    @stats.function_stats(logger)
    def parse_cancel_reason(part: list[str]) -> dict:
        """
        解析 废标理由 部分
        :param part:
        :return:
        """
        data = dict()
        bid_items = []
        data[constants.KEY_PROJECT_BID_ITEMS] = bid_items

        # 存在文本分开的情况
        tmp = "".join(part)
        logger.warning(tmp)
        # 每个标项都有单独的理由说明
        if "标项" in tmp or "分标" in tmp:
            part = tmp.split("。")
            del tmp
            # 存在 "分标1:xxxx;分标2:xxxx;" 这种合并在同一个字符串的情况
            if len(part) == 1:
                sym = symbol_tools.get_symbol(part[0], (";", "；"), raise_error=False)
                if sym:
                    part = part[0].split(sym)

            for p in part:
                if not p:
                    continue
                # 解析出是第几个标项
                # 数字分标：分标1:xxxx
                if match := NotWinBidStandardFormatParser.__PATTERN_BID_ITEM_NUMBER_INDEX.match(p):
                    index, reason = match.group(1), match.group(2)

                # 字母分标：A分标:xxxx
                elif match := NotWinBidStandardFormatParser.__PATTERN_BID_ITEM_CHARACTER_INDEX.match(p):
                    index, reason = match.group(1), match.group(2)
                    # 将其转化为 数字
                    index = ord(index) - ord("A") + 1
                else:
                    raise ParseError(f"废标结果存在新的格式: `{p}`", content=part)

                # 生成标项信息
                bid_item = common.get_template_bid_item(index=int(index), is_win=False)
                bid_item[constants.KEY_BID_ITEM_REASON] = common.parse_bid_item_reason(
                    reason
                )
                bid_items.append(bid_item)
        # 共用一个标项
        else:
            logger.warning(f"废标理由共用：`{tmp}`")
            data[constants.KEY_DEV_BIDDING_CANCEL_REASON_ONLY_ONE] = True
            item = common.get_template_bid_item(index=1, is_win=False)
            item[constants.KEY_BID_ITEM_REASON] = common.parse_bid_item_reason(tmp)
            bid_items.append(item)

        if len(bid_items) == 0:
            raise SwitchError("该公告没有对应的标项信息")
        return data

    @staticmethod
    @stats.function_stats(logger)
    def parse_termination_reason(part: list[str]) -> dict:
        """
        解析 终止理由 部分
        :param part:
        :return:
        """
        if len(part) > 2:
            raise ParseError(f"终止理由存在额外内容:", content=part)
        return {constants.KEY_PROJECT_TERMINATION_REASON: part[-1]}
