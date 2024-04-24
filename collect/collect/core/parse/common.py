import logging
import re
from typing import Union, Callable

from lxml import etree

from collect.collect.middlewares import ParseError
from utils import symbol_tools as sym
from utils import debug_stats as stats
from constant import constants

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
        constants.ANNOUNCEMENT_TYPE_WIN,
        constants.ANNOUNCEMENT_TYPE_DEAL,
        constants.ANNOUNCEMENT_TYPE_WIN_AND_DEAL,
    ]


def check_termination_announcement(announcement_type: int) -> bool:
    """
    判断是否为终止公告
    :param announcement_type:
    :return:
    """
    return announcement_type == constants.ANNOUNCEMENT_TYPE_TERMINATION


def check_not_win_bid_announcement(announcement_type: int) -> bool:
    """
    判断是否为未中标公告
    :param announcement_type:
    :return:
    """
    return announcement_type == constants.ANNOUNCEMENT_TYPE_NOT_WIN


def check_unuseful_announcement(announcement_type: int) -> bool:
    """
    判断是否为不需要的公告
    :param announcement_type:
    :return:
    """
    return announcement_type not in [
        constants.ANNOUNCEMENT_TYPE_NOT_WIN,  # 废标
        constants.ANNOUNCEMENT_TYPE_WIN,  # 中标
        constants.ANNOUNCEMENT_TYPE_DEAL,  # 成交
        constants.ANNOUNCEMENT_TYPE_WIN_AND_DEAL,  # 中标（成交）
        constants.ANNOUNCEMENT_TYPE_TERMINATION,  # 终止公告
    ]


@stats.function_stats(logger)
def parse_review_experts(part: list[str]) -> dict:
    """
    通用的 “评审小组” 部分解析
    :param part:
    :return: 返回包含 ``constants.KEY_PROJECT_PURCHASE_REPRESENTATIVE``
                和 ``constants.KEY_PROJECT_REVIEW_EXPERT`` 的dict（不为空）
    """
    data = dict()

    counter = {}
    for i in range(len(part)):
        split_symbol = sym.get_symbol(
            part[i], ("、", "，", ",", " ", "\u3000"), raise_error=False
        )
        if split_symbol is not None:
            # 存在分隔符
            counter[split_symbol] = counter.get(split_symbol, 0) + 1

    # 评审小组
    review_experts = []
    data[constants.KEY_PROJECT_REVIEW_EXPERT] = review_experts
    # 采购代表人
    representors = []
    data[constants.KEY_PROJECT_PURCHASE_REPRESENTATIVE] = representors

    # 存在分隔符
    if len(counter) != 0:
        # 拿出现次数的分隔符
        max_symbol = max(counter, key=lambda x: counter[x])
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
            if "采购" in p[l + 1 : r]:
                representors.append(result)
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
        constants.KEY_BID_ITEM_NAME: name,
        # 序号
        constants.KEY_BID_ITEM_INDEX: index,
        # 是否中标
        constants.KEY_BID_ITEM_IS_WIN: is_win,
        # 预算
        constants.KEY_BID_ITEM_BUDGET: constants.BID_ITEM_BUDGET_UNASSIGNED,
        # 中标金额
        constants.KEY_BID_ITEM_AMOUNT: (
            constants.BID_ITEM_AMOUNT_UNASSIGNED
            if is_win
            else constants.BID_ITEM_AMOUNT_NOT_DEAL
        ),
        # 中标金额是否为百分比
        constants.KEY_BID_ITEM_IS_PERCENT: False,
        # 供应商
        constants.KEY_BID_ITEM_SUPPLIER: None,
        # 供应商地址
        constants.KEY_BID_ITEM_SUPPLIER_ADDRESS: None,
        # 废标原因
        constants.KEY_BID_ITEM_REASON: (
            constants.BidItemReason.NOT_EXIST
            if is_win
            else constants.BidItemReason.UNASSIGNED
        ),
    }


@stats.function_stats(logger)
def parse_bid_item_reason(reason: str) -> int:
    # 1.有效供应商(不足三家)
    # 2.提交投标文件的投标供应商数量(不足三家),本项目废标
    # 3.投标供应商(数量不符合)要求,系统自动废标
    # 4.通过符合性审查的投标人(不足3家)，作废标处理。
    # 5.至投标截止时间，提交投标文件的投标人(少于三家)，本项目流标，由采购人依法重新招标
    # 6.经公开唱标，B分标(无投标人参与)投标，该分标采购失败。
    # 7.本项目1、2分标投标文件提交截止时间后提交投标文件的供应商(不足三家)，本项目废标
    if (
        (
            ("三家" in reason or "3家" in reason)
            and ("不足" in reason or "少于" in reason)
        )
        or ("数量不符合" in reason)
        or ("无投标人参与" in reason)
    ):
        return constants.BidItemReason.NOT_ENOUGH_SUPPLIERS

    # 1. "评标委员会发现招标文件存在歧义，故本次采购活动作废标处理。
    if "存在歧义" in reason and "招标文件" in reason:
        return constants.BidItemReason.BIDDING_DOCUMENTS_AMBIGUITY

    # 1. 出现影响采购公正的违法、违规行为
    if "违法、违规行为" in reason:
        return constants.BidItemReason.ILLEGAL

    # 1. 因电子签章原因，资格审查中投标人了出现了几种签章的形式，采购人为了本项目更加公正公开公平，决定废标，重新开展采购;
    if "重新开展采购" in reason:
        return constants.BidItemReason.REOPEN

    # 1. 因操作失误，评委人数不符合要求，且系统无法修改，导致项目无法评审，因此流标。
    # 2. 无法进行评审
    if ("无法评审" in reason) or ("无法进行评审" in reason):
        return constants.BidItemReason.UNABLE_REVIEW

    # 1. 三家提供的软件著作权证书均与其投标产品不符。不通过符合性审查
    if "不通过符合性审查" in reason:
        return constants.BidItemReason.NOT_PASS_COMPLIANCE_REVIEW

    # 1. 因(重大变故)，(采购)任务(取消)
    # 2. 因项目(重大变故)，(取消)本次(采购)
    # 3. 因项目有(重大变更)，故本项目(终止采购)。
    if (
        ("重大变故" in reason or "重大表更")
        and ("采购" in reason)
        and ("取消" in reason or "终止" in reason)
    ):
        return constants.BidItemReason.MAJOR_CHANGES_AND_CANCEL

    # 1. 在项目评审中，排名第一的中标侯选供应商在本项目本分标中取得本分标的第一中标侯选供应商资格的，在接下来的分标中将不能再取得第一中标候选供应商资格，但能参与接下来分标的评审，以此类推
    # 2. 根据中标候选人推荐原则；在项目评审中，排名第一的中标侯选供应商在本项目本分标中取得本分标的第一中标侯选供应商资格的，在接下来的分标中将不能再取得第一中标候选供应商资格，但能参与接下来分标的评审，如排名
    if "不能再取得第一中标候选供应商资格" in reason:
        return constants.BidItemReason.SUPPLIERS_ALLOCATION_COMPLETED

    # 1. 三家提供的(软件著作权)证书均与其投标产品(不符)
    if "软件著作权" in reason and "不符" in reason:
        return constants.BidItemReason.COPYRIGHT_INCONSISTENT

    # 1. 本项目应采购人要求，经政府采购监督管理部门同意，(终止)此次(采购)。
    if "终止" in reason and "采购" in reason:
        return constants.BidItemReason.PROCUREMENT_TERMINATION

    # 1.本项目在系统生成项目时没有分标项生成，导致(报价评审无法进行)，故本项目作废标处理
    if "报价评审" in reason and "无法进行" in reason:
        return constants.BidItemReason.UNABLE_QUOTATION_REVIEW

    # 1. 按照采购文件要求：响应文件承诺不得直接复制采购需求，供货商存在直接复制采购需求现象
    if "直接复制" in reason and "采购需求" in reason:
        return constants.BidItemReason.SUPPLIER_COPY_PROCUREMENT_REQUIREMENTS

    # 1. （桂政办发〔2021〕78号）已废止招标文件引用的桂政办发【2015】78 号文内容，招标文件A分标存在重大缺陷应当停止评标工作。
    if "招标文件" in reason and "存在" in reason and "缺陷" in reason:
        return constants.BidItemReason.TENDER_DOCUMENTS_EXIST_SIGNIFICANT_DEFECTS

    # 1.至响应文件提交截止时间止，(供应商)(未提交响应文件)，项目流标
    # 2. 至响应文件提交截止时间止，(无供应商)(提交响应文件)，根据《中华人民共和国政府采购法》第三十六条规定,本分标废标
    if (
        "供应商" in reason
        and ("无供应商" in reason or "未提交" in reason)
        and "响应文件" in reason
    ):
        return constants.BidItemReason.SUPPLIER_NOT_SUBMIT_RESPONSE_DOCUMENTS

    raise ParseError(msg=f"无法解析废标原因: {reason}", content=[reason])


PATTERN_PURCHASER = re.compile(
    r"采购人(?:信息|)(?:\S*?名称)?[:：](\S+?)(?:地址|联系人|联系方式)[:：]"
)

PATTERN_PURCHASER_AGENCY = re.compile(
    r"采购代理机构(?:信息|)(?:\S*?名称)?[：:](\S+?)(?:地址|联系人|联系方式)[:：]"
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
        data[constants.KEY_PURCHASER] = match.group(1)
    else:
        data[constants.KEY_PURCHASER] = None

    if match := PATTERN_PURCHASER_AGENCY.search(part):
        data[constants.KEY_PURCHASER_AGENCY] = match.group(1)
    else:
        data[constants.KEY_PURCHASER_AGENCY] = None

    if (
        data[constants.KEY_PURCHASER] is None
        or data[constants.KEY_PURCHASER_AGENCY] is None
    ):
        raise ParseError(msg="出现新的联系方式内容", content=[part])
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
    # TODO: 可能部分标项信息的index不一致，需要其他方法来进行实现
    _purchase.sort(key=lambda x: x[constants.KEY_BID_ITEM_INDEX])
    _result.sort(key=lambda x: x[constants.KEY_BID_ITEM_INDEX])

    # 仅有一个废标理由，所有标项共用
    if cancel_reason_only_one:
        for i in range(len(_purchase)):
            _purchase[i][constants.KEY_BID_ITEM_REASON] = _result[0][
                constants.KEY_BID_ITEM_REASON
            ]
        return _purchase

    n = len(_purchase)
    if len(_result) == 0:
        m = 0
    else:
        # 存在多个供应商分一个标项
        m = max(_result, key=lambda x: x[constants.KEY_BID_ITEM_INDEX])[
            constants.KEY_BID_ITEM_INDEX
        ]
    if n != m:
        # 候选人公告导致的标项不一致，TODO：到时候特判处理一下
        if constants.KEY_DEV_RESULT_CONTAINS_CANDIDATE in data:
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
        purchase_index = purchase_item[constants.KEY_BID_ITEM_INDEX]

        # 同一个标项 purchase_item 可能有多个 result_item 对应
        while (
            r_idx < result_len
            and _result[r_idx][constants.KEY_BID_ITEM_INDEX] == purchase_index
        ):
            result_item = _result[r_idx]
            # 标项名称
            result_item[constants.KEY_BID_ITEM_NAME] = purchase_item[
                constants.KEY_BID_ITEM_NAME
            ]
            # 标项预算
            result_item[constants.KEY_BID_ITEM_BUDGET] = purchase_item[
                constants.KEY_BID_ITEM_BUDGET
            ]
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
        if item[constants.KEY_BID_ITEM_IS_WIN]:
            amount = item[constants.KEY_BID_ITEM_AMOUNT]
            # 百分比计算，需要和项目的总预算计算
            if item[constants.KEY_BID_ITEM_IS_PERCENT]:
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
        if item[constants.KEY_BID_ITEM_INDEX] != bid_item_index:
            bid_item_index = item[constants.KEY_BID_ITEM_INDEX]
            total_budget += item[constants.KEY_BID_ITEM_BUDGET]
    return total_budget


@stats.function_stats(logger)
def make_item(data: dict, purchase_data: Union[dict, None]):
    """
    将 data 所需要的内容提取出来
    :param purchase_data:
    :param data:
    :return:
    """
    # 存在 采购数据, 也就是存在标项，
    if purchase_data:
        # 终止公告
        if data.get(constants.KEY_PROJECT_IS_TERMINATION, False):
            # 直接用 purchase 的 标项
            data[constants.KEY_PROJECT_BID_ITEMS] = purchase_data.pop(
                constants.KEY_PROJECT_BID_ITEMS, []
            )
        else:
            # 合并标项
            purchase_bid_items = purchase_data.pop(constants.KEY_PROJECT_BID_ITEMS, [])
            result_bid_items = data.get(constants.KEY_PROJECT_BID_ITEMS, [])
            data[constants.KEY_PROJECT_BID_ITEMS] = _merge_bid_items(
                _purchase=purchase_bid_items,
                _result=result_bid_items,
                cancel_reason_only_one=data.get(
                    constants.KEY_DEV_BIDDING_CANCEL_REASON_ONLY_ONE, False
                ),
                data=data,
            )
        data.update(purchase_data)

    # 从 data 中取出所需要的信息
    item = dict()
    # 爬取的时间
    item[constants.KEY_PROJECT_SCRAPE_TIMESTAMP] = data[
        constants.KEY_PROJECT_SCRAPE_TIMESTAMP
    ]
    # 项目名称
    item[constants.KEY_PROJECT_NAME] = data.get(constants.KEY_PROJECT_NAME, None)
    # 项目编号
    item[constants.KEY_PROJECT_CODE] = data.get(constants.KEY_PROJECT_CODE, None)
    # 地区编号
    item[constants.KEY_PROJECT_DISTRICT_CODE] = data.get(
        constants.KEY_PROJECT_DISTRICT_CODE, None
    )
    # TODO： 设置广西值，如果没有设置默认为广西，或者尝试从标题中解析出来
    if not item[constants.KEY_PROJECT_DISTRICT_CODE]:
        raise ParseError(msg="项目地区编号不能为空", content=list(item.items()))

    item[constants.KEY_PROJECT_AUTHOR] = data.get(constants.KEY_PROJECT_AUTHOR, None)
    # 采购种类
    item[constants.KEY_PROJECT_CATALOG] = data.get(constants.KEY_PROJECT_CATALOG, None)
    # 采购方式
    item[constants.KEY_PROJECT_PROCUREMENT_METHOD] = data.get(
        constants.KEY_PROJECT_PROCUREMENT_METHOD, None
    )
    # 开标时间
    item[constants.KEY_PROJECT_BID_OPENING_TIME] = data.get(
        constants.KEY_PROJECT_BID_OPENING_TIME, None
    )
    # 是否成交：中标/废标
    item[constants.KEY_PROJECT_IS_WIN_BID] = data.get(
        constants.KEY_PROJECT_IS_WIN_BID, None
    )
    # 结果公告 ids
    item[constants.KEY_PROJECT_RESULT_ARTICLE_ID] = data.get(
        constants.KEY_PROJECT_RESULT_ARTICLE_ID, []
    )
    # 结果公告的日期
    item[constants.KEY_PROJECT_RESULT_PUBLISH_DATE] = data.get(
        constants.KEY_PROJECT_RESULT_PUBLISH_DATE, []
    )

    # 采购公告ids
    item[constants.KEY_PROJECT_PURCHASE_ARTICLE_ID] = data.get(
        constants.KEY_PROJECT_PURCHASE_ARTICLE_ID, []
    )
    # 采购公告的日期
    item[constants.KEY_PROJECT_PURCHASE_PUBLISH_DATE] = data.get(
        constants.KEY_PROJECT_PURCHASE_PUBLISH_DATE, []
    )

    # 项目总预算
    total_budget = data.get(constants.KEY_PROJECT_TOTAL_BUDGET, None)
    calculated_budget = calculate_total_budget(
        bid_items=data[constants.KEY_PROJECT_BID_ITEMS]
    )
    # 如果项目总预算存在，则需要和计算后的预算进行对比
    if total_budget:
        if abs(calculated_budget - total_budget) > 1e-5:
            raise ParseError(
                msg=f"项目总预算: {total_budget} 与计算后的预算: {calculated_budget} 不一致（误差大于1e-5）",
                content=data[constants.KEY_PROJECT_BID_ITEMS],
            )
        else:
            item[constants.KEY_PROJECT_TOTAL_BUDGET] = calculated_budget
    else:
        item[constants.KEY_PROJECT_TOTAL_BUDGET] = calculated_budget

    # 项目的标项
    item[constants.KEY_PROJECT_BID_ITEMS] = data.get(
        constants.KEY_PROJECT_BID_ITEMS, None
    )
    # 计算总金额
    if item[constants.KEY_PROJECT_IS_WIN_BID]:
        item[constants.KEY_PROJECT_TOTAL_AMOUNT] = calculate_total_amount(
            bid_items=item[constants.KEY_PROJECT_BID_ITEMS],
            budget=item[constants.KEY_PROJECT_TOTAL_BUDGET],
        )
    else:
        item[constants.KEY_PROJECT_TOTAL_AMOUNT] = 0

    # 总时长
    item[constants.KEY_PROJECT_TENDER_DURATION] = data.get(
        constants.KEY_PROJECT_TENDER_DURATION, 0
    )

    # 采购方信息
    item[constants.KEY_PURCHASER] = data.get(constants.KEY_PURCHASER, None)
    # 采购方机构信息
    item[constants.KEY_PURCHASER_AGENCY] = data.get(
        constants.KEY_PURCHASER_AGENCY, None
    )
    # 审查专家信息
    item[constants.KEY_PROJECT_REVIEW_EXPERT] = data.get(
        constants.KEY_PROJECT_REVIEW_EXPERT, []
    )
    # 采购代表人信息
    item[constants.KEY_PROJECT_PURCHASE_REPRESENTATIVE] = data.get(
        constants.KEY_PROJECT_PURCHASE_REPRESENTATIVE, []
    )
    # 是否终止
    item[constants.KEY_PROJECT_IS_TERMINATION] = data.get(
        constants.KEY_PROJECT_IS_TERMINATION, None
    )
    # 终止理由
    item[constants.KEY_PROJECT_TERMINATION_REASON] = data.get(
        constants.KEY_PROJECT_TERMINATION_REASON, None
    )
    return item


@stats.function_stats(logger, log_params=True)
def split_content_by_titles(
    result: list[str],
    is_win_bid: bool,
    check_title: Callable[[bool, str], int],
) -> dict[int, list[str]]:
    """
    根据标题来分片段
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

                # 某些标题可能和后面的内容连成一块，需要分开
                if symbol := sym.get_symbol(
                    result[idx], (":", "："), raise_error=False
                ):
                    sym_idx = result[idx].index(symbol)
                    # 如果冒号不是最后一个字符
                    if sym_idx < len(result[idx]) - 1:
                        result.insert(idx + 1, result[idx][sym_idx + 1:])
                        n += 1

                # 开始部分(不记入标题）
                idx += 1
                pre = idx
                while idx < n and (
                    # 单个中文
                    translate_zh_to_number(result[idx]) < chinese_number_index + 1
                    and
                    (   # 不以 ‘中文数字、’ 开头
                        (zh_idx := startswith_chinese_number(result[idx])) == -1
                        or
                        # 以 ‘中文数字、’ 开头，但是小于当前的 index + 1
                        zh_idx < chinese_number_index + 1
                    )
                ):
                    idx += 1
                # 加入片段
                parts[key_part] = result[pre:idx]
            else:
                idx += 1
        else:
            idx += 1
    return parts
