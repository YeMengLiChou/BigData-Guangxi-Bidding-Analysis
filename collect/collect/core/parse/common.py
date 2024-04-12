import logging
from typing import Union

from collect.collect.middlewares import ParseError
from collect.collect.utils import symbol_tools as sym, debug_stats as stats
from lxml import etree

from constant import constants

logger = logging.getLogger(__name__)

__all__ = [
    "filter_texts",
    "startswith_chinese_number",
    "startswith_number_index",
    "parse_review_experts",
    "parse_html",
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
}

chinese_numbers: list = list(chinese_number_mapper.keys())


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
    判断text是否为 “数字.” 开头
    :param text:
    :return:
    """
    if len(text) == 0:
        return -1
    idx = text.find(".")
    if (idx == -1) or (not text[0].isdigit()):
        return -1
    try:
        value = int(text[:idx])
    except ValueError:
        value = -1
    return value


@stats.function_stats(logger)
def parse_review_experts(part: list[str]) -> dict:
    """
    通用的 “评审小组” 部分解析
    :param part: 返回包含 `constants.KEY_PROJECT_PURCHASE_REPRESENTOR` 和 `constants.KEY_PROJECT_REVIEW_EXPERT` 的dict（不为空）
    :return:
    """
    data = dict()
    # 拿到后面部分的内容
    dist = part[-1].replace("评审专家名单：", "")  # 部分带有该前缀
    # 拿到分隔符
    split_symbol = sym.get_symbol(dist, [",", "，", "、"])
    # 分隔
    persons = dist.split(split_symbol)
    # 评审小组
    review_experts = []
    data[constants.KEY_PROJECT_REVIEW_EXPERT] = review_experts
    # 采购代表人
    representors = []
    data[constants.KEY_PROJECT_PURCHASE_REPRESENTOR] = representors

    for p in persons:
        # 部分去掉句号
        p = p.replace("。", "")
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
                    content=part.append(f"{p} l:{l}, r:{r}"),
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
            raise ParseError(msg="评审专家解析部分出现特殊情况", content=part.append(p))
    return data


@stats.function_stats(logger)
def get_template_bid_item(is_win: bool, index: int) -> dict:
    """
    获取一个模板的投标信息，只需要关注已经拿到的值并赋值即可，而无需其他的初始化操作，保证到最后合并的时候都是完整的
    :return:
    """
    return {
        # 名称
        constants.KEY_BID_ITEM_NAME: None,
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
        # 数量
        constants.KEY_BID_ITEM_QUANTITY: constants.BID_ITEM_QUANTITY_UNCLEAR,
        # 供应商
        constants.KEY_BID_ITEM_SUPPLIER: None,
        # 供应商地址
        constants.KEY_BID_ITEM_SUPPLIER_ADDRESS: None,
        # 废标原因
        constants.KEY_BID_ITEM_REASON: (
            constants.BID_ITEM_REASON_NOT_EXIST
            if is_win
            else constants.BID_ITEM_REASON_UNASSIGNED
        ),
    }


@stats.function_stats(logger)
def parse_bid_item_reason(reason: str) -> int:
    if "有效供应商不足三家" in reason:
        return constants.BID_ITEM_REASON_NOT_ENOUGH_SUPPLIERS
    raise ParseError(msg=f"无法解析废标原因: {reason}", content=[reason])


@stats.function_stats(logger)
def parse_contact_info(part: list[str]) -> dict:
    """
    解析 以下方式联系 部分
    :param part:
    :return:
    """

    def check_information_begin(s: str) -> bool:
        return startswith_number_index(s) >= 1

    def check_name(s: str) -> bool:
        startswith_name = s.startswith("名") or (s.find("名") < s.find("称"))
        endswith_colon = s.endswith(":") or s.endswith("：")
        return startswith_name and endswith_colon

    def check_address(s: str) -> bool:
        startswith_address = s.startswith("地") or (s.find("地") < s.find("址"))
        endswith_colon = s.endswith(":") or s.endswith("：")
        return startswith_address and endswith_colon

    def check_person(s: str) -> bool:
        startswith_person = s.startswith("项目联系人") or s.startswith("联系人")
        endswith_colon = s.endswith(":") or s.endswith("：")
        return startswith_person and endswith_colon

    def check_contact_method(s: str) -> bool:
        startswith_contact_method = s.startswith("项目联系方式") or s.startswith(
            "联系方式"
        )
        endswith_colon = s.endswith(":") or s.endswith("：")
        return startswith_contact_method and endswith_colon

    data, n, idx = dict(), len(part), 0
    while idx < n:
        text = part[idx]
        if check_information_begin(text):
            # 采购人 / 采购代理机构信息
            key_word = text[2:]
            idx += 1
            info = dict()
            # 开始解析内容
            while idx < n and not check_information_begin(part[idx]):
                # 名称
                if check_name(part[idx]):
                    info["name"] = part[idx + 1]
                    idx += 2
                # 地址
                elif check_address(part[idx]):
                    info["address"] = part[idx + 1]
                    idx += 2
                # 联系人
                elif check_person(part[idx]):
                    info["person"] = part[idx + 1].split("、")
                    idx += 2
                # 联系方式
                elif check_contact_method(part[idx]):
                    info["contact_method"] = part[idx + 1]
                    idx += 2
                else:
                    idx += 1

            # 加入到 data 中
            if key_word.startswith("采购人"):
                data[constants.KEY_PURCHASER_INFORMATION] = info
            elif key_word.startswith("采购代理机构"):
                data[constants.KEY_PURCHASER_AGENCY_INFORMATION] = info
        else:
            idx += 1
    return data


@stats.function_stats(logger)
def _merge_bid_items(_purchase: list, _result: list) -> list:
    """
    将两部分的标项信息合并
    :param _purchase:
    :param _result:
    :return:
    """
    # TODO: 可能部分标项信息的index不一致，需要其他方法来进行实现
    _purchase.sort(key=lambda x: x[constants.KEY_BID_ITEM_INDEX])
    _result.sort(key=lambda x: x[constants.KEY_BID_ITEM_INDEX])

    n, m = len(_purchase), len(_result)
    if n != m:
        raise ParseError(
            msg="标项数量不一致",
            content=[f"purchase length: {n}, result length: {m}", _purchase, _result],
        )

    for idx in range(n):
        purchase_item = _purchase[idx]
        result_item = _result[idx]
        # 标项名称不一致
        if (
            result_item.get(constants.KEY_BID_ITEM_NAME, None)
            and purchase_item[constants.KEY_BID_ITEM_NAME]
            != result_item[constants.KEY_BID_ITEM_NAME]
        ):
            raise ParseError(
                msg="标项名称不一致",
                content=[f"purchase item: {purchase_item}, result item: {result_item}"],
            )

        result_item[constants.KEY_BID_ITEM_NAME] = purchase_item[
            constants.KEY_BID_ITEM_NAME
        ]
        result_item[constants.KEY_BID_ITEM_QUANTITY] = purchase_item[
            constants.KEY_BID_ITEM_QUANTITY
        ]
        result_item[constants.KEY_BID_ITEM_BUDGET] = purchase_item[
            constants.KEY_BID_ITEM_BUDGET
        ]
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
    for item in bid_items:
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
    # 存在 采购数据, 也就是存在标项
    if purchase_data:
        # 合并标项
        purchase_bid_items = purchase_data.pop(constants.KEY_PROJECT_BID_ITEMS, [])
        result_bid_items = data.get(constants.KEY_PROJECT_BID_ITEMS, [])
        data[constants.KEY_PROJECT_BID_ITEMS] = _merge_bid_items(
            _purchase=purchase_bid_items, _result=result_bid_items
        )
        data.update(purchase_data)

    # 从 data 中取出所需要的信息
    item = dict()
    # 项目名称
    item[constants.KEY_PROJECT_NAME] = data.get(constants.KEY_PROJECT_NAME, None)
    # 项目编号
    item[constants.KEY_PROJECT_CODE] = data.get(constants.KEY_PROJECT_CODE, None)
    # 地区编号 TODO： 设置广西值，如果没有设置默认为广西，或者尝试从标题中解析出来
    item[constants.KEY_PROJECT_DISTRICT_CODE] = data.get(
        constants.KEY_PROJECT_DISTRICT_CODE, None
    )
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
    # 是否政府采购 TODO:此数据似乎都是false， 需要进一步确认
    item[constants.KEY_PROJECT_IS_GOVERNMENT_PURCHASE] = data.get(
        constants.KEY_PROJECT_IS_GOVERNMENT_PURCHASE, None
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
        # TODO: 可能存在误差
        if calculated_budget != total_budget:
            raise ParseError(
                msg=f"项目总预算: {total_budget} 与计算后的预算: {calculated_budget} 不一致",
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
    # 采购方信息
    item[constants.KEY_PURCHASER_INFORMATION] = data.get(
        constants.KEY_PURCHASER_INFORMATION, None
    )
    # 采购方机构信息
    item[constants.KEY_PURCHASER_AGENCY_INFORMATION] = data.get(
        constants.KEY_PURCHASER_AGENCY_INFORMATION, None
    )
    # 审查专家信息
    item[constants.KEY_PROJECT_REVIEW_EXPERT] = data.get(
        constants.KEY_PROJECT_REVIEW_EXPERT, []
    )
    # 采购代表人信息
    item[constants.KEY_PROJECT_PURCHASE_REPRESENTOR] = data.get(
        constants.KEY_PROJECT_PURCHASE_REPRESENTOR, []
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
