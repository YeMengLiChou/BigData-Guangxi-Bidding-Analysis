from collect.collect.middlewares import ParseError
from collect.collect.utils import symbol_tools as sym
from lxml import etree

from contant import constants


__all__ = [
    "filter_texts",
    "startswith_chinese_number",
    "startswith_number_index",
    "parse_review_experts",
    "parse_html",
]

filter_rules = [
    lambda text: isinstance(text, str),
    lambda text: len(text) > 0,  # 过滤空字符串
    lambda text: text not in ['"', "“", "”", "\\n"],  # 过滤双引号、转义回车符
    lambda text: "th, td {\n    border: 1px solid #DDD;\n    padding: 5px 10px;\n}"
    not in text,
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


def parse_review_experts(part: list[str]) -> dict:
    """
    通用的 “评审小组” 部分解析
    :param part:
    :return:
    """
    data = dict()
    # 拿到后面部分的内容
    dist = part[-1]
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

    for person in persons:
        # 采购人代表
        if "采购人代表" in persons:
            # 解析左右括号位置
            l, r = sym.get_parentheses_position(person)
            # 存在括号
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
            representors.append(representor)
            review_experts.append(representor)
        # 非采购人代表
        else:
            if person == "/":
                continue
            review_experts.append(person)

    return data
