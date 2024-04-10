import logging
import re

from collect.collect.core.parse import AbstractFormatParser
from collect.collect.middlewares import ParseError
from collect.collect.utils import (
    symbol_tools as sym
)
from contant import constants

logger = logging.getLogger(__name__)


def parse_not_win_bid(parts: list[list[str]]):
    def is_reason(_title):
        return "废标理由" in _title

    def is_preview(_title):
        return "评审" in _title

    def is_termination_reason(_title):
        return "终止" in _title

    data = dict()
    for part in parts:
        title = part[0]
        if is_preview(title):
            data.update(NotWinBidStandardFormatParser.parse_review_expert(part))
        elif is_reason(title):
            data.update(NotWinBidStandardFormatParser.parse_cancel_reason(part))
        elif is_termination_reason(title):
            data.update(NotWinBidStandardFormatParser.parse_termination_reason(part))
        else:
            raise ParseError(f"{title} 不存在解析部分", content=part)
    return data


class NotWinBidStandardFormatParser(AbstractFormatParser):
    @staticmethod
    def parse_review_expert(part: list[str]) -> dict:
        data = dict()
        dist = part[-1]

        split_symbol = sym.get_symbol(dist, [",", "，", "、"])
        persons = dist.split(split_symbol)
        review_experts = []
        for person in persons:
            # 采购人代表
            if "采购人代表" in persons:
                l, r = sym.get_parentheses_position(person)
                if l != -1 and r != -1:
                    if l == 0:
                        # 名字在括号的右边
                        representor = persons[r + 1:]
                    elif r == len(persons) - 1:
                        # 名字在括号的左边
                        representor = persons[:l]
                    else:
                        raise ParseError(
                            msg="评审专家解析部分-采购人部分出现特殊情况", content=part
                        )
                else:
                    raise ParseError(
                        msg="评审专家解析部分-采购人部分出现特殊情况", content=part
                    )
            else:
                if person == '/':
                    continue
                review_experts.append(persons)
        data[constants.KEY_PROJECT_REVIEW_EXPERT] = review_experts
        return data

    @staticmethod
    def parse_cancel_reason(part: list[str]):
        # 删除标题
        part.pop(0)

        data = dict()
        bid_items = []
        data[constants.KEY_PROJECT_BID_ITEMS] = bid_items
        for p in part:
            match = re.match(".*(分标|标项)([0-9]):(.*)", p)
            if match:
                index, reason = match.group(1), match.group(2)
                bid_items.append({
                    constants.KEY_BID_ITEM_INDEX: index,
                    constants.KEY_BID_ITEM_IS_WIN: False,
                    constants.KEY_BID_ITEM_REASON: reason,
                    constants.KEY_BID_ITEM_IS_PERCENT: False,
                    constants.KEY_BID_ITEM_SUPPLIER_ADDRESS: None,
                    constants.KEY_BID_ITEM_SUPPLIER: None,
                    constants.KEY_BID_ITEM_AMOUNT: constants.BID_ITEM_AMOUNT_NOT_DEAL
                })
            else:
                raise ParseError(f"存在新的格式: {p}", content=part)
        return data

    @staticmethod
    def parse_termination_reason(part: list[str]) -> dict:
        if len(part) > 2:
            raise ParseError(f"终止理由存在额外内容:", content=part)
        return {
            constants.KEY_PROJECT_TERMINATION_REASON: part[-1]
        }
