import logging
import time
from typing import Type
from contant import constants

from collect.collect.core.parse import (
    AbstractFormatParser,
    common,
)
from collect.collect.utils import (
    log,
    symbol_tools as sym,
)
from collect.collect.middlewares import ParseError

logger = logging.getLogger(__name__)

try:
    from config.config import settings

    _DEBUG = getattr(settings, "debug.enable", False)
except ImportError:
    _DEBUG = True

if _DEBUG:
    if len(logging.root.handlers) == 0:
        logging.basicConfig(level=logging.DEBUG)


def parse_win_bid(parts: list[list[str]]) -> dict | None:
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
            bid_items = parse_bids_information(
                _part=part, parser=WinBidStandardFormatParser
            )
            if len(bid_items) == 0:
                logger.warning(
                    "该结果公告没有爬取到任何标项信息！尝试切换 other_announcements 进行查找！"
                )
                return None
            else:
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
    def _parse_win_bids(part: list[str]) -> list:
        """
        解析 中标结果
        :param part:
        :return:
        """

        start_time = time.time()
        if _DEBUG:
            logger.debug(f"DEBUG INFO: {log.get_function_name()} started")

        def is_bid_item_index(s: str) -> bool:
            return s.isdigit()

        try:
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
                    while idx < n and not is_bid_item_index(price_text):
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
        finally:
            if _DEBUG:
                logger.debug(
                    f"{log.get_function_name()} finished, running: {time.time() - start_time}"
                )

    @staticmethod
    def _parse_not_win_bids(part: list[str]) -> list:
        """
        解析其中的废标项
        :param part:
        :return:
        """
        start_time = 0
        if _DEBUG:
            start_time = time.time()
            logger.debug(f"{log.get_function_name()} started")

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

        try:
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
        finally:
            if _DEBUG:
                logger.debug(
                    f"{log.get_function_name()} finished, running: {time.time() - start_time}"
                )

    @staticmethod
    def parse_bids_information(part: list[str]) -> list:
        """
        解析中标信息
        :param part:
        :return:
        """
        start_time = 0
        if _DEBUG:
            start_time = time.time()
            logger.debug(f"{log.get_function_name()} started")

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

        try:
            data, idx, n = [], 1, len(part)
            while idx < n:
                text = part[idx]
                if is_win_bid_result(text):
                    pre = idx + 1
                    while idx < n and not is_not_win_bid_result(part[idx]):
                        idx += 1
                    data.append(
                        *WinBidStandardFormatParser._parse_win_bids(part=part[pre:idx])
                    )

                elif is_not_win_bid_result(text):
                    res = WinBidStandardFormatParser._parse_not_win_bids(
                        part=part[idx + 1 :]
                    )
                    if len(res) > 0:
                        data.append(*res)
                    idx += 1
                else:
                    idx += 1
            return data
        finally:
            if _DEBUG:
                logger.debug(
                    f"{log.get_function_name()} finished, running: {time.time() - start_time}"
                )

    @staticmethod
    def parse_review_expert(part: list[str]) -> dict:
        start_time = 0
        if _DEBUG:
            start_time = time.time()
            logger.debug(f"{log.get_function_name()} started")

        try:
            data = dict()
            dist = part[-1]
            # 获取分隔符
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
                            representor = persons[r + 1 :]
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

                    data[constants.KEY_PROJECT_PURCHASE_REPRESENTOR] = representor
                    review_experts.append(representor)
                # 非采购人代表
                else:
                    review_experts.append(persons)
            return data
        finally:
            if _DEBUG:
                logger.debug(
                    f"{log.get_function_name()} finished, running: {time.time() - start_time}"
                )
