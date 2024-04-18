import logging

from collect.collect.core.parse import (
    AbstractFormatParser,
    common,
)
from collect.collect.middlewares import ParseError
from collect.collect.utils import debug_stats as stats
from constant import constants

logger = logging.getLogger(__name__)


@stats.function_stats(logger, log_params=True)
def parse_win_bid(parts: dict[int, list[str]]) -> dict:
    """
    解析 中标结果
    :param parts:
    :return: 返回包含 `KEY_PROJECT_BID_ITEMS`、 `KEY_PROJECT_REVIEW_EXPERT` 和 `KEY_PROJECT_PURCHASE_REPRESENTOR` 的数据
    """

    data = dict()
    bid_items = []
    data[constants.KEY_PROJECT_BID_ITEMS] = bid_items

    # 解析 标项信息
    if constants.KEY_PART_WIN_BID in parts:
        bid_items.extend(
            WinBidStandardFormatParser.parse_bids_information(
                part=parts[constants.KEY_PART_WIN_BID]
            )
        )
    # 解析 评审专家信息
    if constants.KEY_PART_REVIEW_EXPERT in parts:
        data.update(
            WinBidStandardFormatParser.parse_review_expert(
                part=parts[constants.KEY_PART_REVIEW_EXPERT]
            )
        )
    # 解析 联系方式信息
    if constants.KEY_PART_CONTACT in parts:
        data.update(common.parse_contact_info(part=parts[constants.KEY_PART_CONTACT]))

    return data


class WinBidStandardFormatParser(AbstractFormatParser):
    """
    解析中标结果
    """

    @staticmethod
    def __is_bid_item_index(s: str) -> bool:
        # 存在部分情况的需要
        return s.isdigit() or (  # 纯数字： 1、2、3...
            s[0].isalpha() and s[1:].isdigit()
        )  # 第一个是字母，后面是数字： A060205

    @staticmethod
    @stats.function_stats(logger)
    def _parse_win_bids(part: list[str]) -> list:
        """
        解析 中标结果
        :param part:
        :return:
        """

        idx, n, data = 0, len(part), []
        while idx < n:
            text = part[idx]
            # 当前是序号
            if WinBidStandardFormatParser.__is_bid_item_index(text):
                # 中标金额
                price_text = part[idx + 1]
                # 中标供应商
                supplier_text = part[idx + 2]
                # 中标供应商地址
                pre = idx + 3
                idx += 3
                while idx < n and not WinBidStandardFormatParser.__is_bid_item_index(
                    part[idx]
                ):
                    idx += 1
                address_text = "".join(part[pre:idx])

                # 标项信息
                if text.isdigit():
                    bid_item = common.get_template_bid_item(
                        is_win=True, index=int(text)
                    )
                else:
                    bid_item = common.get_template_bid_item(
                        is_win=True, index=len(data) + 1
                    )

                amount, is_percent = AbstractFormatParser.parse_win_bid_item_amount(
                    amount_str=price_text
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
        idx, n, data = 0, len(part), []
        while idx < n:
            if WinBidStandardFormatParser.__is_bid_item_index(part[idx]):
                bid_item = common.get_template_bid_item(
                    index=int(part[idx]), is_win=False
                )
                bid_item[constants.KEY_BID_ITEM_NAME] = part[idx + 1]
                bid_item[constants.KEY_BID_ITEM_REASON] = common.parse_bid_item_reason(
                    part[idx + 2]
                )
                idx += 4
                data.append(bid_item)
            else:
                idx += 1
        return data

    @staticmethod
    @stats.function_stats(logger)
    def parse_win_bid_special_1(part: list[str]) -> list:
        """
        解析 中标结果 特殊格式1：
        格式如下：
        1.供应商名称：xxx
        2.供应商地址：xxx
        3.中标（成交）金额： xxx
        4.交货期/工期：xxx
        :param part:
        :return:
        """
        idx, n, data = 0, len(part), []
        # 默认只有一个
        item = common.get_template_bid_item(index=1, is_win=True)
        cnt = 0
        while idx < n:
            if "供应商名称" in part[idx]:
                idx += 1
                tmp_idx = idx
                while idx < n and common.startswith_number_index(part[idx]) == -1:
                    idx += 1
                item[constants.KEY_BID_ITEM_SUPPLIER] = "".join(part[tmp_idx:idx])
                cnt += 1
            elif "供应商地址" in part[idx]:
                idx += 1
                tmp_idx = idx
                while idx < n and common.startswith_number_index(part[idx]) == -1:
                    idx += 1
                item[constants.KEY_BID_ITEM_SUPPLIER_ADDRESS] = "".join(
                    part[tmp_idx:idx]
                )
                cnt += 1
            elif "中标（成交）金额" in part[idx]:
                idx += 1
                tmp_idx = idx
                while idx < n and common.startswith_number_index(part[idx]) == -1:
                    idx += 1
                amount_text = "".join(part[tmp_idx:idx])
                amount, is_percent = AbstractFormatParser.parse_win_bid_item_amount(
                    amount_str=amount_text
                )
                item[constants.KEY_BID_ITEM_AMOUNT] = amount
                item[constants.KEY_BID_ITEM_IS_PERCENT] = is_percent

        data.append(item)
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

        data, idx, n = [], 0, len(part)
        # 用于统计 “1.中标结果” 和 “2.废标结果” 的数量
        # 如果为0则证明是另一种形式
        part_cnt = 0
        while idx < n:
            text = part[idx]
            # 判断标题为 “1.中标结果”
            if is_win_bid_result(text):
                part_cnt += 1
                pre = idx + 1
                while idx < n and not is_not_win_bid_result(part[idx]):
                    idx += 1
                data.extend(
                    WinBidStandardFormatParser._parse_win_bids(part=part[pre:idx])
                )
            # 判断标题为 “2.废标结果”
            elif is_not_win_bid_result(text):
                part_cnt += 1
                data.extend(
                    WinBidStandardFormatParser._parse_not_win_bids(part=part[idx + 1 :])
                )
                idx += 1
            else:
                idx += 1

        # 不适用
        if part_cnt == 0:
            data.extend(WinBidStandardFormatParser.parse_win_bid_special_1(part=part))
        elif part_cnt == 1:
            raise ParseError(msg="win.py解析中标标项信息出现的格式", content=part)

        return data

    @staticmethod
    @stats.function_stats(logger)
    def parse_review_expert(part: list[str]) -> dict:
        return common.parse_review_experts(part)
