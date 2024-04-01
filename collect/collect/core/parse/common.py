
__filter_rules = [
    lambda text: isinstance(text, str),
    lambda text: len(text) > 0,  # 过滤空字符串
    lambda text: text not in ["\"", "“", "”", "\\n"],  # 过滤双引号、转义回车符
    lambda text: "th, td {\n    border: 1px solid #DDD;\n    padding: 5px 10px;\n}" not in text,
]

__chinese_number = ['零', '一', '二', '三', '四', '五', '六', '七', '八', '九', '十']
__chinese_number_mapper = {
    '零': 0,
    '一': 1,
    '二': 2,
    '三': 3,
    '四': 4,
    '五': 5,
    '六': 6,
    '七': 7,
    '八': 8,
    '九': 9,
    '十': 10
}


def filter_texts(texts: list, rules=None):
    """
    根据已有规则进行过滤（按照rules中的顺序进行过滤）
    :param texts:
    :param rules:
    :return:
    """
    if rules is None:
        rules = __filter_rules
    for rule in rules:
        result = list(filter(rule, texts))
        del texts
        texts = result
    return texts


def startswith_chinese_number(text: str) -> int:
    """
    判断text是否为 “中文数字、” 开头
    :param text:
    :return:
    """
    if len(text) < 2 or text[1] != '、':
        return -1
    return __chinese_number_mapper.get(text[0], -1)


def startswith_number_index(text: str) -> int:
    """
    判断text是否为 “数字.” 开头
    :param text:
    :return:
    """
    if len(text) < 2 or text[1] != '.':
        return -1
    return int(text[0])

