import logging
import re
import time

from collect.collect.core.parse import AbstractFormatParser, __all__, common
from collect.collect.middlewares import ParseError
from collect.collect.utils import symbol_tools as sym
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


def parse_not_win_bid(parts: list[list[str]]):
    """
    解析 “废标公告” 信息
    :param parts:
    :return:
    """
    def is_reason(_title):
        return "废标理由" in _title

    def is_review(_title):
        return "评审" in _title

    def is_termination_reason(_title):
        return "终止" in _title

    data = dict()
    for part in parts:
        title = part[0]
        # “评审小组” 部分 （废标公告可能有）
        if is_review(title):
            data.update(NotWinBidStandardFormatParser.parse_review_expert(part))
        # “废标理由” 部分 （废标公告特有）
        elif is_reason(title):
            data.update(NotWinBidStandardFormatParser.parse_cancel_reason(part))
        # “终止理由” 部分 （终止公告特有）
        elif is_termination_reason(title):
            data.update(NotWinBidStandardFormatParser.parse_termination_reason(part))
        else:
            raise ParseError(f"{title} 不存在解析部分", content=part)
    return data


class NotWinBidStandardFormatParser(AbstractFormatParser):
    @staticmethod
    def parse_review_expert(part: list[str]) -> dict:
        start_time = 0
        if _DEBUG:
            start_time = time.time()
            logger.debug(f"{log.get_function_name()} started")

        try:
            return common.parse_review_experts(part)
        finally:
            if _DEBUG:
                logger.debug(
                    f"{log.get_function_name()} finished, running: {time.time() - start_time}"
                )

    @staticmethod
    def parse_cancel_reason(part: list[str]):
        # 删除标题
        part.pop(0)

        data = dict()
        bid_items = []
        data[constants.KEY_PROJECT_BID_ITEMS] = bid_items
        for p in part:
            # 解析出是第几个标项
            match = re.match(".*(分标|标项)([0-9]):(.*)", p)
            if match:
                index, reason = match.group(1), match.group(2)
                bid_items.append(
                    {
                        constants.KEY_BID_ITEM_INDEX: index,
                        constants.KEY_BID_ITEM_IS_WIN: False,
                        constants.KEY_BID_ITEM_REASON: reason,
                        constants.KEY_BID_ITEM_IS_PERCENT: False,
                        constants.KEY_BID_ITEM_SUPPLIER_ADDRESS: None,
                        constants.KEY_BID_ITEM_SUPPLIER: None,
                        constants.KEY_BID_ITEM_AMOUNT: constants.BID_ITEM_AMOUNT_NOT_DEAL,
                    }
                )
            else:
                raise ParseError(f"存在新的格式: {p}", content=part)
        return data

    @staticmethod
    def parse_termination_reason(part: list[str]) -> dict:
        if len(part) > 2:
            raise ParseError(f"终止理由存在额外内容:", content=part)
        return {constants.KEY_PROJECT_TERMINATION_REASON: part[-1]}
