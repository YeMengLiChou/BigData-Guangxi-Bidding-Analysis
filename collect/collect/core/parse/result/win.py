import logging
from typing import Type

from collect.collect.core.parse import (
    AbstractFormatParser,
    common,
)
from collect.collect.utils import debug_stats as stats
from contant import constants

logger = logging.getLogger(__name__)


@stats.function_stats(logger)
def parse_win_bid(parts: list[list[str]]) -> dict:
    """
    解析 中标结果
    :param parts:
    :return: 如果结果公告匹配，那么返回对应的数据；否则返回 None
    """

    def is_bids_information(title: str) -> bool:
        return "中标（成交）信息" == title

    def is_review_expert(title: str) -> bool:
        return "评审" in title

    def parse_bids_information(
        _part: list[str], parser: Type[AbstractFormatParser]
    ) -> list:
        """
        解析中标信息
        :param parser:
        :param _part:
        :return:
        """
        return parser.parse_bids_information(part=_part)

    def parse_review_expert(
        _part: list[str], parser: Type[AbstractFormatParser]
    ) -> dict:
        """
        解析评审专家信息
        :param parser:
        :param _part:
        :return:
        """
        return parser.parse_review_expert(part=_part)

    data = dict()

    for part in parts:
        if is_bids_information(title=part[0]):
            # 解析 标项信息
            bid_items = parse_bids_information(
                _part=part, parser=WinBidStandardFormatParser
            )
            data[constants.KEY_PROJECT_BID_ITEMS] = bid_items
        elif is_review_expert(title=part[0]):
            data.update(
                parse_review_expert(_part=part, parser=WinBidStandardFormatParser)
            )
    return data


class WinBidStandardFormatParser(AbstractFormatParser):
    """
    解析中标结果
    """

    @staticmethod
    @stats.function_stats(logger)
    def _parse_win_bids(part: list[str]) -> list:
        """
        解析 中标结果
        :param part:
        :return:
        """

        def is_bid_item_index(s: str) -> bool:
            return s.isdigit()

        idx, n, data = 0, len(part), []
        while idx < n:
            text = part[idx]
            # 当前是序号
            if is_bid_item_index(text):
                bid_item = dict()
                # 中标金额
                price_text = part[idx + 1]
                # 中标供应商
                supplier_text = part[idx + 2]
                # 中标供应商地址
                pre = idx + 3
                idx += 3
                while idx < n and not is_bid_item_index(part[idx]):
                    idx += 1
                address_text = "".join(part[pre:idx])
                bid_item[constants.KEY_BID_ITEM_INDEX] = int(text)
                bid_item[constants.KEY_BID_ITEM_NAME] = None
                amount, is_percent = AbstractFormatParser.parse_win_bid_item_amount(
                    string=price_text
                )
                bid_item[constants.KEY_BID_ITEM_AMOUNT] = amount
                bid_item[constants.KEY_BID_ITEM_IS_PERCENT] = is_percent
                bid_item[constants.KEY_BID_ITEM_SUPPLIER] = supplier_text
                bid_item[constants.KEY_BID_ITEM_SUPPLIER_ADDRESS] = address_text
                data.append(bid_item)
            else:
                idx += 1

        return data

    @staticmethod
    @stats.function_stats(logger)
    def _parse_not_win_bids(part: list[str]) -> list:
        """
        解析其中的废标项
        :param part:
        :return:
        """

        def is_bid_item_index(s: str) -> bool:
            return s.isdigit()

        def make_bid_item(index: int, name: str, reason: str) -> dict:
            item = dict()
            item[constants.KEY_BID_ITEM_INDEX] = index
            item[constants.KEY_BID_ITEM_IS_PERCENT] = False
            item[constants.KEY_BID_ITEM_IS_WIN] = False
            item[constants.KEY_BID_ITEM_REASON] = reason
            item[constants.KEY_BID_ITEM_NAME] = name
            item[constants.KEY_BID_ITEM_SUPPLIER] = None
            item[constants.KEY_BID_ITEM_SUPPLIER_ADDRESS] = None
            return item

        idx, n, data = 0, len(part), []
        while idx < n:
            if is_bid_item_index(part[idx]):
                bid_item = make_bid_item(
                    index=int(part[idx]), name=part[idx + 1], reason=part[idx + 2]
                )
                idx += 4
                data.append(bid_item)
            else:
                idx += 1
        return data

    @staticmethod
    @stats.function_stats(logger)
    def parse_bids_information(part: list[str]) -> list:
        """
        解析中标信息
        :param part:
        :return:
        """

        def is_win_bid_result(s: str) -> bool:
            """
            判断是否为 “1.中标结果”
            :param s:
            :return:
            """
            return (
                common.startswith_number_index(s) == 1
                and "中标结果" in s
                and (s.endswith("：") or s.endswith(":"))
            )

        def is_not_win_bid_result(s: str) -> bool:
            """
            判断是否为 “2.废标结果”
            :param s:
            :return:
            """
            return (
                common.startswith_number_index(s) == 2
                and "废标结果" in s
                and (s.endswith("：") or s.endswith(":"))
            )

        data, idx, n = [], 1, len(part)
        while idx < n:
            text = part[idx]
            # 判断标题为 “1.中标结果”
            if is_win_bid_result(text):
                pre = idx + 1
                while idx < n and not is_not_win_bid_result(part[idx]):
                    idx += 1
                data.extend(
                    WinBidStandardFormatParser._parse_win_bids(part=part[pre:idx])
                )
            # 判断标题为 “2.废标结果”
            elif is_not_win_bid_result(text):
                res = WinBidStandardFormatParser._parse_not_win_bids(
                    part=part[idx + 1 :]
                )
                if len(res) > 0:
                    data.extend(res)
                idx += 1
            else:
                idx += 1
        return data

    @staticmethod
    @stats.function_stats(logger)
    def parse_review_expert(part: list[str]) -> dict:
        return common.parse_review_experts(part)
