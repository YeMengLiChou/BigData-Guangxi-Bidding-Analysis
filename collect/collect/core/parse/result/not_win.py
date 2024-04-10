import logging
import re

from collect.collect.core.parse import AbstractFormatParser
from collect.collect.middlewares import ParseError
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
        if "，" in dist:
            split_symbol = "，"
        elif "、" in dist:
            split_symbol = "、"
        else:
            split_symbol = ","
        persons = dist.split(split_symbol)
        review_experts = []
        for person in persons:
            if "采购人代表" in persons:
                left_bracket_symbol = "(" if "(" in person else "（"
                right_bracket_symbol = ")" if left_bracket_symbol == "(" else "）"
                idx = person.index(left_bracket_symbol)
                if idx == 0:
                    idx = person.rindex(right_bracket_symbol)
                    representor = person[idx + 1:]
                else:
                    representor = person[:idx]
                data[constants.KEY_PROJECT_PURCHASE_REPRESENTOR] = representor
                review_experts.append(representor)
            else:
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
            match = re.match(".*分标([0-9]):(.*)", p)
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
