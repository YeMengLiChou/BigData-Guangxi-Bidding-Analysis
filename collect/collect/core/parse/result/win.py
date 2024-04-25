import logging
import re

from collect.collect.core.parse import (
    AbstractFormatParser,
    common,
)
from collect.collect.middlewares import ParseError
from utils import symbol_tools
from utils import debug_stats as stats
from constant import constants

logger = logging.getLogger(__name__)


@stats.function_stats(logger, log_params=True)
def parse_win_bid(parts: dict[int, list[str]]) -> dict:
    """
    解析 中标结果
    :param parts:
    :return: 返回包含 `KEY_PROJECT_BID_ITEMS`、 `KEY_PROJECT_REVIEW_EXPERT` 和 `KEY_PROJECT_PURCHASE_REPRESENTATIVE` 的数据
    """

    data = dict()
    bid_items = []
    data[constants.KEY_PROJECT_BID_ITEMS] = bid_items

    # 解析 标项信息
    if constants.PartKey.WIN_BID in parts:
        bid_items.extend(
            WinBidStandardFormatParser.parse_bids_information(
                part=parts[constants.PartKey.WIN_BID]
            )
        )
    # 解析 评审专家信息
    if constants.PartKey.REVIEW_EXPERT in parts:
        data.update(
            WinBidStandardFormatParser.parse_review_expert(
                part=parts[constants.PartKey.REVIEW_EXPERT]
            )
        )
    # 解析 联系方式信息
    if constants.PartKey.CONTACT in parts:
        data.update(
            common.parse_contact_info(part="".join(parts[constants.PartKey.CONTACT]))
        )

    return data


class WinBidStandardFormatParser(AbstractFormatParser):
    """
    解析中标结果
    """

    PATTERN_BID_ITEM_INDEX_NUMBER = re.compile(r"(\d{1,2})")

    PATTERN_BID_ITEM_INDEX_ALPHA_AND_TEXT = re.compile(
        r"(?:标项|)([A-Z]+)(?:分标|标段)"
    )

    PATTERN_BID_ITEM_INDEX_ALPHA_AND_NUMBER = re.compile(r"([A-Z]+)(\d*)")

    @staticmethod
    def __is_bid_item_index(s: str, def_index: int) -> int:
        """
        判断是否为标项的序号
        :param s:
        :return:
        """
        for p in [
            WinBidStandardFormatParser.PATTERN_BID_ITEM_INDEX_NUMBER,
            WinBidStandardFormatParser.PATTERN_BID_ITEM_INDEX_ALPHA_AND_TEXT,
            WinBidStandardFormatParser.PATTERN_BID_ITEM_INDEX_ALPHA_AND_NUMBER,
        ]:
            if match := p.fullmatch(s):
                # 后面带有数字的使用默认序号
                if len(match.groups()) == 2:
                    if len(match.groups(2)) == 0:
                        return ord(match.group(1)) - ord("A") + 1
                    else:
                        return def_index
                # 数字和字母
                index = match.group(1)
                if index.isdigit():
                    return int(index)
                else:
                    return ord(index) - ord("A") + 1
        return -1

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
            if (
                index := WinBidStandardFormatParser.__is_bid_item_index(
                    text, def_index=len(data) + 1
                )
            ) != -1:
                # 中标金额
                price_text = part[idx + 1]
                # 中标供应商
                supplier_text = part[idx + 2]
                # 中标供应商地址
                pre = idx + 3
                idx += 3
                while (
                    idx < n
                    and WinBidStandardFormatParser.__is_bid_item_index(
                        part[idx], def_index=len(data) + 1
                    )
                    == -1
                ):
                    idx += 1
                address_text = "".join(part[pre:idx])

                bid_item = common.get_template_bid_item(is_win=True, index=index)
                amount, is_percent = AbstractFormatParser.parse_amount(
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
            if (
                index := WinBidStandardFormatParser.__is_bid_item_index(
                    part[idx], def_index=len(data) + 1
                )
            ) > -1:
                # 当前 idx 为序号
                bid_item = common.get_template_bid_item(index=index, is_win=False)
                # 标项名称
                bid_item[constants.KEY_BID_ITEM_NAME] = part[idx + 1]
                # 废标理由
                bid_item[constants.KEY_BID_ITEM_REASON] = part[idx + 2]

                # 某些情况下:  其他事项这一列为空，导致在预处理的时候就已经被过滤掉，这里需要判断一下
                if idx + 3 < n:
                    if (
                        WinBidStandardFormatParser.__is_bid_item_index(
                            part[idx + 3], def_index=len(data) + 1
                        )
                        > -1
                    ):
                        idx += 3
                    else:
                        idx += 4
                else:
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
        # 默认只有一个item
        item = common.get_template_bid_item(index=1, is_win=True)
        cnt = 0

        def check_title():
            """
            检查标题是否是标题
            :return:
            """
            if "供应商名称" in part[idx]:
                return True
            if "供应商地址" in part[idx]:
                return True
            if (
                "中标（成交）金额" in part[idx]
                or "中标金额" in part[idx]
                or "成交金额" in part[idx]
            ):
                return True
            return False

        def split_title():
            """
            将连在一起的内容分离
            :return:
            """
            if not symbol_tools.endswith_colon_symbol(part[idx]):
                colon_idx = part[idx].find("：")
                if colon_idx == -1:
                    colon_idx = part[idx].find(":")
                part.insert(idx + 1, part[idx][colon_idx + 1 :])
                nonlocal n
                n += 1

        def get_content(item_key: str):
            """
            将该片段截取出来，存到 ``item`` 对应的 ``item_key`` 中
            :param item_key:
            :return:
            """
            split_title()
            nonlocal idx, cnt, item
            idx += 1
            t_idx = idx
            while (
                idx < n
                and common.startswith_number_index(part[idx]) == -1
                and not check_title()
            ):
                idx += 1
            item[item_key] = "".join(part[t_idx:idx])
            cnt += 1

        while idx < n:
            if "供应商名称" in part[idx]:
                get_content(constants.KEY_BID_ITEM_SUPPLIER)
            elif "供应商地址" in part[idx]:
                get_content(constants.KEY_BID_ITEM_SUPPLIER_ADDRESS)
            elif (
                "中标（成交）金额" in part[idx]
                or "中标金额" in part[idx]
                or "成交金额" in part[idx]
            ):
                split_title()
                idx += 1
                tmp_idx = idx
                # 某些情况下存在金额 “xxxx.xxx” 会被解析，显示解析后的数目少于 5

                while idx < n and (
                    common.startswith_number_index(part[idx]) == -1  # 不以 '数字.' 开头
                    or (
                        (index := part[idx].find("."))
                        != -1  # 某些情况存在为小数开头，先找到小数点位置 index
                        and index < len(part[idx]) - 1  # 确保小数点后面有字符
                        and part[idx][index + 1].isdigit()  # 小数点后面是数字
                    )
                    and not check_title()
                ):
                    idx += 1

                amount_text = "".join(part[tmp_idx:idx])
                amount, is_percent = AbstractFormatParser.parse_amount(
                    amount_str=amount_text
                )
                item[constants.KEY_BID_ITEM_AMOUNT] = amount
                item[constants.KEY_BID_ITEM_IS_PERCENT] = is_percent
                cnt += 1
            else:
                idx += 1

        if cnt != 3:
            raise ParseError(msg="出现特殊的中标信息格式", content=part)
        data.append(item)
        return data

    @staticmethod
    @stats.function_stats(logger)
    def parse_win_bid_special_2(part: list[str]) -> list:
        """
        解析中标结果特殊格式2
        格式：(没有序号和废标结果)
        中标结果
        序号	中标（成交）金额(元)	中标供应商名称	中标供应商地址
        1	      795000	广西壮族自治区地质环境监 测站	广西壮族自治区玉林市玉州区石棠路与东秀路 交叉路口
        :param part:
        :return:
        """
        if part[0].startswith("中标结果"):
            return WinBidStandardFormatParser._parse_win_bids(part)
        else:
            return []

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
            success = False
            errors = []
            # 尝试每种解析
            for call in [
                WinBidStandardFormatParser.parse_win_bid_special_1,
                WinBidStandardFormatParser.parse_win_bid_special_2,
            ]:
                try:
                    res = call(part)
                    if len(res) > 0:
                        success = True
                        data.extend(res)
                        break
                except ParseError as e:
                    errors.append(e.message)

            # 如果还是没办法解析，就直接抛出异常
            if not success:
                raise ParseError(
                    msg="win.py解析中标标项信息出现新格式", content=part + errors
                )

        elif part_cnt == 1:
            raise ParseError(msg="win.py解析中标标项信息出现新格式", content=part)

        return data

    @staticmethod
    @stats.function_stats(logger)
    def parse_review_expert(part: list[str]) -> dict:
        return common.parse_review_experts(part)
