import logging
import re

from collect.collect.core.parse import AbstractFormatParser, common
from collect.collect.core.error import SwitchError
from collect.collect.middlewares import ParseError
from utils import symbol_tools
from utils import debug_stats as stats
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
    if constants.PartKey.CONTACT in parts:
        data.update(
            common.parse_contact_info("".join(parts[constants.PartKey.CONTACT]))
        )
    # 解析 评审专家
    if constants.PartKey.REVIEW_EXPERT in parts:
        data.update(
            NotWinBidStandardFormatParser.parse_review_expert(
                parts[constants.PartKey.REVIEW_EXPERT]
            )
        )
    # 解析 废标理由
    if constants.PartKey.NOT_WIN_BID in parts:
        data.update(
            NotWinBidStandardFormatParser.parse_cancel_reason(
                parts[constants.PartKey.NOT_WIN_BID]
            )
        )
    # 解析 终止理由
    if constants.PartKey.TERMINATION_REASON in parts:
        # 存在一种情况：标的类型是废标，但是实际上是终止，在这里加上去
        data[constants.KEY_PROJECT_IS_TERMINATION] = True
        data.update(
            NotWinBidStandardFormatParser.parse_termination_reason(
                parts[constants.PartKey.TERMINATION_REASON]
            )
        )

    # 如果没有对应的数据，那么就赋值默认值
    if not data.get(constants.KEY_PROJECT_REVIEW_EXPERT, None):
        data[constants.KEY_PROJECT_REVIEW_EXPERT] = []
        data[constants.KEY_PROJECT_PURCHASE_REPRESENTATIVE] = []

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

    # 合并在一起的标项
    # 本项目1、2分标投标文件提交截止时间后提交投标文件的供应商不足三家，本项目废标
    __PATTERN_BID_ITEM_COMPACT_INDEX = re.compile(
        r"(?:标项)?((?:\d{1,2}、)+\d{1,2})(?:分标)?(\S+)"
    )

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
    @stats.function_stats(logger, log_params=True)
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
        # 每个标项都有单独的理由说明
        # 拿到关键词
        if keyword := symbol_tools.get_symbol(
            tmp, ("标项", "分标", "包"), raise_error=False
        ):

            # TODO: ex: 标项1:三家提供的软件著作权证书均与其投标产品不符。不通过符合性审查
            part = list(filter(lambda x: x, tmp.split("。")))
            del tmp
            # 存在 "分标1:xxxx;分标2:xxxx;" 这种合并在同一个字符串的情况
            if len(part) == 1:
                sym = symbol_tools.get_symbol(part[0], (";", "；"), raise_error=False)
                if sym:
                    part = part[0].split(sym)
            for p in part:
                if not p:
                    continue

                if keyword not in p:
                    continue
                # 解析出是第几个标项
                # 数字分标：分标1:xxxx
                if match := NotWinBidStandardFormatParser.__PATTERN_BID_ITEM_NUMBER_INDEX.match(
                    p
                ):
                    index, reason = match.group(1), match.group(2)

                # 字母分标：A分标:xxxx
                elif match := NotWinBidStandardFormatParser.__PATTERN_BID_ITEM_CHARACTER_INDEX.match(
                    p
                ):
                    index, reason = match.group(1), match.group(2)
                    # 将其转化为 数字
                    index = ord(index) - ord("A") + 1

                # 连续的 标项：本项目1、2分标投标文件提交截止时间后提交投标文件的供应商不足三家，本项目废标"
                elif match := NotWinBidStandardFormatParser.__PATTERN_BID_ITEM_COMPACT_INDEX.search(
                    p
                ):
                    index_sequence, reason = match.groups()
                    index = index_sequence.split("、")

                else:
                    raise ParseError(f"废标结果存在新的格式: `{p}`", content=part)

                # 生成标项信息
                if isinstance(index, str):
                    bid_item = common.get_template_bid_item(
                        index=int(index), is_win=False
                    )
                    bid_item[constants.KEY_BID_ITEM_REASON] = (
                        common.parse_bid_item_reason(reason)
                    )
                    bid_items.append(bid_item)
                # 第三种情况，出现多个标项
                elif isinstance(index, list):
                    for i in index:
                        bid_item = common.get_template_bid_item(
                            index=int(i), is_win=False
                        )
                        bid_item[constants.KEY_BID_ITEM_REASON] = (
                            common.parse_bid_item_reason(reason)
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
