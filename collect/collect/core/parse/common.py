import logging
import re
from typing import Union, Callable

from lxml import etree

from collect.collect.middlewares import ParseError
from utils import symbol_tools as sym
from utils import debug_stats as stats
from constants import (
    ProjectKey,
    AnnouncementType,
    BidItemKey,
    CollectConstants,
    CollectDevKey,
)

logger = logging.getLogger(__name__)

__all__ = [
    "filter_texts",
    "translate_zh_to_number",
    "startswith_chinese_number",
    "startswith_number_index",
    "parse_review_experts",
    "parse_html",
    "split_content_by_titles",
]

filter_rules = [
    lambda text: isinstance(text, str),
    lambda text: len(text.strip()) > 0,  # 过滤空字符串
    lambda text: text not in ['"', "“", "”", "\\n"],  # 过滤双引号、转义回车符
]

chinese_number_mapper = {
    "零": 0,
    "一": 1,
    "二": 2,
    "三": 3,
    "四": 4,
    "五": 5,
    "六": 6,
    "七": 7,
    "八": 8,
    "九": 9,
    "十": 10,
    "十一": 11,
    "十二": 12,
    "十三": 13,
    "十四": 14,
    "十五": 15,
    "十六": 16,
    "十七": 17,
    "十八": 18,
    "十九": 19,
    "二十": 20,
    "二十一": 21,
    "二十二": 22,
    "二十三": 23,
    "二十四": 24,
    "二十五": 25,
    "二十六": 26,
    "二十七": 27,
    "二十八": 28,
    "二十九": 29,
    "三十": 30,
    "三十一": 31,
    "三十二": 32,
    "三十三": 33,
    "三十四": 34,
    "三十五": 35,
    "三十六": 36,
    "三十七": 37,
    "三十八": 38,
    "三十九": 39,
    "四十": 40,
    "四十一": 41,
    "四十二": 42,
    "四十三": 43,
    "四十四": 44,
    "四十五": 45,
    "四十六": 46,
    "四十七": 47,
    "四十八": 48,
    "四十九": 49,
    "五十": 50,
    "五十一": 51,
    "五十二": 52,
    "五十三": 53,
    "五十四": 54,
    "五十五": 55,
    "五十六": 56,
    "五十七": 57,
    "五十八": 58,
    "五十九": 59,
    "六十": 60,
    "六十一": 61,
    "六十二": 62,
    "六十三": 63,
    "六十四": 64,
    "六十五": 65,
    "六十六": 66,
    "六十七": 67,
    "六十八": 68,
    "六十九": 69,
    "七十": 70,
    "七十一": 71,
    "七十二": 72,
    "七十三": 73,
    "七十四": 74,
    "七十五": 75,
    "七十六": 76,
    "七十七": 77,
    "七十八": 78,
    "七十九": 79,
    "八十": 80,
    "八十一": 81,
    "八十二": 82,
    "八十三": 83,
    "八十四": 84,
    "八十五": 85,
    "八十六": 86,
    "八十七": 87,
    "八十八": 88,
    "八十九": 89,
    "九十": 90,
    "九十一": 91,
    "九十二": 92,
    "九十三": 93,
    "九十四": 94,
    "九十五": 95,
    "九十六": 96,
    "九十七": 97,
    "九十八": 98,
    "九十九": 99,
    "一百": 100,
}

chinese_numbers: list = list(chinese_number_mapper.keys())


def translate_zh_to_number(text: str) -> int:
    """
    返回中文数字对应的阿拉伯数字
    :param text:
    :return:
    """
    return chinese_number_mapper.get(text, -1)


def filter_texts(texts: list, rules=None):
    """
    根据已有规则进行过滤（按照rules中的顺序进行过滤）
    :param texts:
    :param rules:
    :return:
    """
    if rules is None:
        rules = filter_rules
    for rule in rules:
        result = list(filter(rule, texts))
        del texts
        texts = result
    return texts


def parse_html(html_content: str) -> list[str]:
    """
    解析html，返回文本列表
    :param html_content:
    :return:
    """
    html = etree.HTML(html_content)
    # 找出所有的文本，并且进行过滤
    text_list = [text.strip() for text in html.xpath("//text()")]
    return filter_texts(text_list)


def startswith_chinese_number(text: str) -> int:
    """
    判断text是否为 “中文数字、” 开头，最多匹配到 20
    :param text:
    :return:
    """
    idx = text.find("、")
    if idx == -1:
        return -1
    return chinese_number_mapper.get(text[:idx], -1)


def startswith_number_index(text: str) -> int:
    """
    判断text是否为 “数字.” 或 “数字、”开头
    :param text:
    :return:
    """
    if len(text) == 0:
        return -1
    if not text[0].isdigit():
        return -1

    idx = text.find(".")
    if idx == -1:
        idx = text.find("、")
    if idx == -1:
        return idx
    try:
        value = int(text[:idx])
    except ValueError:
        value = -1
    return value


def check_win_bid_announcement(announcement_type: int) -> bool:
    """
    判断是否为中标公告
    :param announcement_type:
    :return:
    """
    return announcement_type in [
        AnnouncementType.WIN,
        AnnouncementType.DEAL,
        AnnouncementType.WIN_AND_DEAL,
    ]


def check_termination_announcement(announcement_type: int) -> bool:
    """
    判断是否为终止公告
    :param announcement_type:
    :return:
    """
    return announcement_type == AnnouncementType.TERMINATION


def check_not_win_bid_announcement(announcement_type: int) -> bool:
    """
    判断是否为未中标公告
    :param announcement_type:
    :return:
    """
    return announcement_type == AnnouncementType.NOT_WIN


def check_unuseful_announcement(announcement_type: int) -> bool:
    """
    判断是否为不需要的公告
    :param announcement_type:
    :return:
    """
    return announcement_type not in [
        AnnouncementType.NOT_WIN,  # 废标
        AnnouncementType.WIN,  # 中标
        AnnouncementType.DEAL,  # 成交
        AnnouncementType.WIN_AND_DEAL,  # 中标（成交）
        AnnouncementType.TERMINATION,  # 终止公告
    ]


PATTERN_COMPACT_NUMBER = re.compile(r"(\d{1,2}、)+\d{1,2}分标")
"""
用于匹配评审专家字符串中的  “第1、2、3、4分标采购人代表”
"""


@stats.function_stats(logger)
def parse_review_experts(part: list[str]) -> dict:
    """
    通用的 “评审小组” 部分解析
    :param part:
    :return: 返回包含 ``ProjectKey.PURCHASE_REPRESENTATIVE``
                和 ``ProjectKey.REVIEW_EXPERT`` 的dict（不为空）
    """
    data = dict()
    counter = {}
    # 统计可能分割符的频率
    sym_candidates = ("、", "，", ",", " ", "\u3000")
    for i in range(len(part)):
        part[i] = PATTERN_COMPACT_NUMBER.sub("", part[i])
        for _sym in sym_candidates:
            counter[_sym] = counter.get(_sym, 0) + part[i].count(_sym)

    # 评审小组
    review_experts = []
    data[ProjectKey.REVIEW_EXPERT] = review_experts
    # 采购代表人
    representatives = []
    data[ProjectKey.PURCHASE_REPRESENTATIVE] = representatives

    # 存在分隔符
    if len(counter) != 0:
        # 拿出现次数的分隔符
        max_symbol = max(counter.keys(), key=lambda x: counter[x])
        # 拿到后面部分的内容
        dist = "".join(part).replace("评审专家名单：", "")  # 部分带有该前缀
        if dist == "/":
            return data
        # 分隔
        persons = dist.split(max_symbol)
    # 没有分隔符，表示已经是分隔好的形式
    else:
        persons = part

    for p in persons:
        # 部分去掉句号
        p = p.replace("。", "").replace("：", "").replace(":", "")
        # 判断是否有括号
        l, r = sym.get_parentheses_position(p)

        if r < l:
            raise ParseError(
                msg="评审专家解析部分出现特殊情况: l > r", content=part + [p]
            )

        # 存在括号
        if l != -1 and r != -1:
            # 名字在括号的右边：（xxx）名字
            if l == 0:
                result = p[r + 1 :]
            # 名字在括号的左边： 名字（xxx）
            elif r == len(p) - 1:
                result = p[:l]
            else:
                raise ParseError(
                    msg="评审专家解析部分出现特殊情况",
                    content=persons + [f"{p} l:{l}, r:{r}"],
                )

            # 去掉括号加入到评审小组
            review_experts.append(result)
            # 加入到采购代表人
            if "采购" in p[l:r]:
                representatives.append(result)
        elif l == -1 and r == -1:
            if p == "/":
                continue
            review_experts.append(p)
        else:
            raise ParseError(msg="评审专家解析部分出现特殊情况", content=part + [p])
    return data


@stats.function_stats(logger)
def get_template_bid_item(is_win: bool, index: int, name: str = None) -> dict:
    """
    获取一个模板的投标信息，只需要关注已经拿到的值并赋值即可，而无需其他的初始化操作，保证到最后合并的时候都是完整的
    :return:
    """
    return {
        # 名称
        BidItemKey.NAME: name,
        # 序号
        BidItemKey.INDEX: index,
        # 是否中标
        BidItemKey.IS_WIN: is_win,
        # 预算
        BidItemKey.BUDGET: CollectConstants.BID_ITEM_BUDGET_UNASSIGNED,
        # 中标金额
        BidItemKey.AMOUNT: (
            CollectConstants.BID_ITEM_AMOUNT_UNASSIGNED
            if is_win
            else CollectConstants.BID_ITEM_AMOUNT_NOT_DEAL
        ),
        # 中标金额是否为百分比
        BidItemKey.IS_PERCENT: False,
        # 供应商
        BidItemKey.SUPPLIER: None,
        # 供应商地址
        BidItemKey.SUPPLIER_ADDRESS: None,
        # 废标原因
        BidItemKey.REASON: None,
    }


PATTERN_PURCHASER = re.compile(
    r"(?:采购|征集|招标)人(?:信息|)(?:\S*?名称\S*?)?[:：](\S+?)(?:地址|联系人|联系方式)[:：]"
)

PATTERN_PURCHASER_AGENCY = re.compile(
    r"(?:采购|招标)代理机构(?:信息|)(?:\S*?名称)?[：:](\S+?)(?:地址|联系人|联系方式|\d)[:：]?"
)


@stats.function_stats(logger)
def parse_contact_info(part: str) -> dict:
    """
    解析 以下方式联系 部分
    :param part:
    :return:
    """
    # 替换掉无用字符，避免干扰正则表达式
    part = sym.remove_all_spaces(part)

    data = dict()
    if match := PATTERN_PURCHASER.search(part):
        data[ProjectKey.PURCHASER] = match.group(1)
    else:
        data[ProjectKey.PURCHASER] = None

    if match := PATTERN_PURCHASER_AGENCY.search(part):
        data[ProjectKey.PURCHASER_AGENCY] = match.group(1)
    else:
        data[ProjectKey.PURCHASER_AGENCY] = None

    if data[ProjectKey.PURCHASER] is None or data[ProjectKey.PURCHASER_AGENCY] is None:
        # 某些只有一个名称
        if part.count("名称") == 1:
            return data
        raise ParseError(
            msg="出现新的联系方式内容",
            content=[
                f"purchaser 解析结果:{data[ProjectKey.PURCHASER]}",
                f"agency 解析结果:{data[ProjectKey.PURCHASER_AGENCY]}",
                part,
            ],
        )

    return data


@stats.function_stats(logger)
def _merge_bid_items(
    _purchase: list, _result: list, cancel_reason_only_one: bool, data: dict
) -> list:
    """
    将两部分的标项信息合并
    :param _purchase:
    :param _result:
    :return:
    """
    _purchase.sort(key=lambda x: x[BidItemKey.INDEX])
    _result.sort(key=lambda x: x[BidItemKey.INDEX])
    # 仅有一个废标理由，所有标项共用
    if cancel_reason_only_one:
        for i in range(len(_purchase)):
            _purchase[i][BidItemKey.REASON] = _result[0][BidItemKey.REASON]
        return _purchase

    n = len(_purchase)
    if len(_result) == 0:
        m = 0
    else:
        # 存在多个供应商分一个标项
        m = max(_result, key=lambda x: x[BidItemKey.INDEX])[BidItemKey.INDEX]
    if n != m:
        # 候选人公告导致的标项不一致，TODO：到时候特判处理一下
        if CollectDevKey.RESULT_CONTAINS_CANDIDATE in data:
            raise ParseError(
                msg="标项数量不一致，存在候选人公告！",
                content=[
                    f"purchase length: {n}, result length: {m}",
                    _purchase,
                    _result,
                ],
            )
        raise ParseError(
            msg="标项数量不一致",
            content=[f"purchase length: {n}, result length: {m}", _purchase, _result],
        )

    result_len = len(_result)
    r_idx = 0
    for p_idx in range(n):
        purchase_item = _purchase[p_idx]
        purchase_index = purchase_item[BidItemKey.INDEX]

        # 同一个标项 purchase_item 可能有多个 result_item 对应
        while r_idx < result_len and _result[r_idx][BidItemKey.INDEX] == purchase_index:
            result_item = _result[r_idx]
            # 标项名称
            result_item[BidItemKey.NAME] = purchase_item[BidItemKey.NAME]
            # 标项预算
            result_item[BidItemKey.BUDGET] = purchase_item[BidItemKey.BUDGET]
            r_idx += 1

    return _result


@stats.function_stats(logger)
def calculate_total_amount(bid_items: list, budget: float):
    """
    计算项目的总金额
    :param budget: 项目的总预算
    :param bid_items:
    :return:
    """
    total_amount = 0
    for item in bid_items:
        if item[BidItemKey.IS_WIN]:
            amount = item[BidItemKey.AMOUNT]
            # 百分比计算，需要和项目的总预算计算
            if item[BidItemKey.IS_PERCENT]:
                amount = amount * 0.01
                total_amount += budget * amount
            else:
                total_amount += amount

    return total_amount


@stats.function_stats(logger)
def calculate_total_budget(bid_items: list):
    """
    计算总预算
    :param bid_items:
    :return:
    """
    total_budget = 0
    bid_item_index = 0
    for item in bid_items:
        if item[BidItemKey.INDEX] != bid_item_index:
            bid_item_index = item[BidItemKey.INDEX]
            total_budget += item[BidItemKey.BUDGET]
    return total_budget


# ProjectKey
keys = []
# 排除的key，需要单独设置
exclude_keys = [ProjectKey.TOTAL_BUDGET, ProjectKey.TOTAL_AMOUNT]
for _k, v in vars(ProjectKey).items():
    if _k.isupper() and v not in exclude_keys:
        keys.append(v)


@stats.function_stats(logger)
def make_item(result_data: dict, purchase_data: Union[dict, None]):
    """
    将 data 所需要的内容提取出来
    :param purchase_data:
    :param result_data:
    :return:
    """
    # 存在 采购数据, 也就是存在标项，
    if purchase_data:
        # 终止公告
        if result_data.get(ProjectKey.IS_TERMINATION, False):
            # 直接用 purchase 的 标项
            result_data[ProjectKey.BID_ITEMS] = purchase_data.pop(
                ProjectKey.BID_ITEMS, []
            )
        else:
            # 合并标项
            purchase_bid_items = purchase_data.pop(ProjectKey.BID_ITEMS, [])
            result_bid_items = result_data.get(ProjectKey.BID_ITEMS, [])
            result_data[ProjectKey.BID_ITEMS] = _merge_bid_items(
                _purchase=purchase_bid_items,
                _result=result_bid_items,
                cancel_reason_only_one=result_data.get(
                    CollectDevKey.BIDDING_CANCEL_REASON_ONLY_ONE, False
                ),
                data=result_data,
            )
        result_data.update(purchase_data)

    # 从 data 中取出所需要的信息
    item = {k: result_data[k] for k in keys}

    # TODO： 设置广西值，如果没有设置默认为广西，或者尝试从标题中解析出来
    if not item[ProjectKey.DISTRICT_CODE]:
        raise ParseError(msg="项目地区编号不能为空", content=list(item.items()))

    # 项目总预算
    total_budget = result_data.get(ProjectKey.TOTAL_BUDGET, None)
    calculated_budget = calculate_total_budget(
        bid_items=result_data[ProjectKey.BID_ITEMS]
    )
    # 如果项目总预算存在，则需要和计算后的预算进行对比
    if total_budget:
        if abs(calculated_budget - total_budget) > 1e-5:
            raise ParseError(
                msg=f"项目总预算: {total_budget} 与计算后的预算: {calculated_budget} 不一致（误差大于1e-5）",
                content=result_data[ProjectKey.BID_ITEMS],
            )
        else:
            item[ProjectKey.TOTAL_BUDGET] = calculated_budget
    else:
        item[ProjectKey.TOTAL_BUDGET] = calculated_budget

    # 计算总金额
    if item[ProjectKey.IS_WIN_BID]:
        item[ProjectKey.TOTAL_AMOUNT] = calculate_total_amount(
            bid_items=item[ProjectKey.BID_ITEMS],
            budget=item[ProjectKey.TOTAL_BUDGET],
        )
    else:
        item[ProjectKey.TOTAL_AMOUNT] = 0

    return item


@stats.function_stats(logger, log_params=True)
def split_content_by_titles(
    result: list[str],
    is_win_bid: bool,
    check_title: Callable[[bool, str], int],
    rfind: bool = False,
) -> dict[int, list[str]]:
    """
    根据标题来分片段
    :param rfind:  是否反向定位查找
    :param result:
    :param is_win_bid:
    :param check_title:
    :return:
    """
    # chinese_number_index 用于规定顺序，避免某些特殊情况
    n, idx, chinese_number_index = len(result), 0, 0
    # 分解的片段
    parts = dict[int, list[str]]()

    while idx < n:
        title = result[idx]

        # 存在情况：“中文数字” 和 后面部分的标题内容 “、xxx” 是分开的
        if translate_zh_to_number(title) > chinese_number_index:
            # 检测第二行
            if idx + 1 < n and result[idx + 1].startswith("、"):
                title += result[idx + 1]
                result.pop(idx + 1)
                n -= 1

        # 找以 “一、” 这种格式开头的字符串
        index = startswith_chinese_number(title)
        # 需要在上次解析的序号后面
        if index > chinese_number_index:
            # 标题是否为已经完善
            completed = False

            # 存在一种废标情况，标题为 “二、项目废标的原因”，但是文本分开，需要特殊处理
            if not is_win_bid:
                length = len(result[idx])
                if length < 9 and index == 2 and result[idx][2:].startswith("项目"):
                    tmp_idx = idx
                    # 往下查找直到长度满足
                    while idx < n and length < 9:
                        idx += 1
                        length += len(result[idx])
                    else:
                        # 拼接
                        result[idx] = "".join(result[tmp_idx : idx + 1])
                        completed = True

            # 存在一种情况，“中文数字、”和后面的标题内容分开，也就是 '、' 是最后一个字符
            if not completed:
                if title[-1].endswith("、"):
                    title += result[idx + 1]
                    result.pop(idx + 1)
                    n -= 1
                    completed = True

            # 标题长度少于4则继续拼接
            while len(title) - 2 < 4 and idx + 1 < n:
                title += result[idx + 1]
                result.pop(idx + 1)
                n -= 1

            # 检查 标题
            key_part = check_title(is_win_bid, title)
            if key_part:
                chinese_number_index = index

                # 某些部分已经解析过，然后可能存在重复的部分，判断
                if key_part in parts:
                    idx += 1
                    continue
                # 某些标题可能和后面的内容连成一块，需要分开
                if symbol := sym.get_symbol(
                    result[idx], (":", "："), raise_error=False
                ):
                    sym_idx = result[idx].index(symbol)
                    # 如果冒号不是最后一个字符
                    if sym_idx < len(result[idx]) - 1:
                        result.insert(idx + 1, result[idx][sym_idx + 1 :])
                        n += 1

                # 开始部分(不记入标题）
                idx += 1
                pre = idx
                # 正向查找
                if not rfind:
                    while idx < n and (
                        # 单个中文
                        translate_zh_to_number(result[idx]) < chinese_number_index + 1
                        and (  # 不以 ‘中文数字、’ 开头
                            (zh_idx := startswith_chinese_number(result[idx])) == -1
                            or
                            # 以 ‘中文数字、’ 开头，但是小于当前的 index + 1
                            zh_idx < chinese_number_index + 1
                        )
                    ):
                        idx += 1
                else:
                    r_idx = n - 1
                    while r_idx > idx and (
                        # 单个中文
                        translate_zh_to_number(result[r_idx]) > chinese_number_index + 1
                        and (  # 不以 ‘中文数字、’ 开头
                            (zh_idx := startswith_chinese_number(result[r_idx])) == -1
                            or
                            # 以 ‘中文数字、’ 开头，但是小于当前的 index + 1
                            zh_idx > chinese_number_index + 1
                        )
                    ):
                        r_idx -= 1
                    idx = r_idx + 1
                # 加入片段
                parts[key_part] = result[pre:idx]
            else:
                idx += 1
        else:
            idx += 1
    return parts
