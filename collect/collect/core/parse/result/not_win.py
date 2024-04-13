import logging
import re

from collect.collect.core.parse import AbstractFormatParser, common
from collect.collect.middlewares import ParseError
from collect.collect.utils import debug_stats as stats
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
    @staticmethod
    @stats.function_stats(logger)
    def parse_review_expert(part: list[str]) -> dict:
        return common.parse_review_experts(part)

    @staticmethod
    @stats.function_stats(logger)
    def parse_cancel_reason(part: list[str]):
        data = dict()
        bid_items = []
        data[constants.KEY_PROJECT_BID_ITEMS] = bid_items
        for p in part:
            # 解析出是第几个标项
            match = re.match(r"(?:分标|标项)(\d+):(.*)", p)
            if match:
                index, reason = match.group(1), match.group(2)
                bid_item = common.get_template_bid_item(index=int(index), is_win=False)
                bid_item[constants.KEY_BID_ITEM_REASON] = common.parse_bid_item_reason(
                    reason
                )
                bid_items.append(bid_item)
            else:
                raise ParseError(f"废标结果存在新的格式: {p}", content=part)
        return data

    @staticmethod
    @stats.function_stats(logger)
    def parse_termination_reason(part: list[str]) -> dict:
        if len(part) > 2:
            raise ParseError(f"终止理由存在额外内容:", content=part)
        return {constants.KEY_PROJECT_TERMINATION_REASON: part[-1]}
