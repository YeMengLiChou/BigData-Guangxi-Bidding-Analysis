import json
from abc import ABC
from typing import Type
from lxml import etree
from collect.collect.core.parse import common
from collect.collect.core.parse import AbstractFormatParser
from contant import constants
from collect.collect.middlewares import ParseError


class StandardFormatParser(AbstractFormatParser):
    """
    标准格式文件的解析
    """

    @staticmethod
    def parse_project_base_situation(part: list[str]) -> dict:
        """
        解析 项目基本情况
        :param part:
        :return:
        """

        def check_bid_item_quantity(s: str) -> bool:
            endswith_colon = s.endswith(":") or s.endswith("：")
            return s.startswith("数量") and endswith_colon

        def check_bid_item_budget(s: str) -> bool:
            endswith_colon = s.endswith(":") or s.endswith("：")
            return s.startswith("预算金额") and endswith_colon

        data = dict()
        bid_items = []
        n, idx = len(part), 0
        while idx < n:
            text = part[idx]
            # 总预算
            if "预算总金额" in text:
                budget = float(part[idx + 1])
                data[constants.KEY_PROJECT_TOTAL_BUDGET] = budget
                idx += 2
            # 标项
            elif text.startswith("标项名称"):
                bid_item = dict()
                # 标项名称
                idx += 1
                bid_item[constants.KEY_BID_ITEM_NAME] = part[idx]

                idx += 1
                while idx < n and not part[idx].startswith("标项名称"):
                    print()
                    # 数量
                    if check_bid_item_quantity(part[idx]):
                        quantity = part[idx + 1]
                        if quantity == "不限":
                            quantity = constants.BID_ITEM_QUANTITY_UNLIMITED
                        bid_item[constants.KEY_BID_ITEM_QUANTITY] = quantity
                        idx += 2
                    elif check_bid_item_budget(part[idx]):
                        bid_item[constants.KEY_BID_ITEM_BUDGET] = float(part[idx + 1])
                        idx += 2
                    else:
                        idx += 1
                bid_items.append(bid_item)
            else:
                idx += 1
        data[constants.KEY_PROJECT_BID_ITEMS] = bid_items
        return data

    @staticmethod
    def parse_project_contact(part: list[str]) -> dict:
        """
        解析 以下方式联系 部分
        :param part:
        :return:
        """
        data = dict()
        n, idx = len(part), 0

        def check_information_begin(s: str) -> bool:
            return common.startswith_number_index(s) >= 1

        def check_name(s: str) -> bool:
            startswith_name = s.startswith("名称") or (s.find("名") < s.find("称"))
            endswith_colon = s.endswith(':') or s.endswith('：')
            return startswith_name and endswith_colon

        def check_address(s: str) -> bool:
            startswith_address = s.startswith("地址") or (s.find("地") < s.find("址"))
            endswith_colon = s.endswith(':') or s.endswith('：')
            return startswith_address and endswith_colon

        def check_person(s: str) -> bool:
            startswith_person = s.startswith("项目联系人") or s.startswith("联系人")
            endswith_colon = s.endswith(':') or s.endswith('：')
            return startswith_person and endswith_colon

        def check_contact_method(s: str) -> bool:
            startswith_contact_method = s.startswith("项目联系方式") or s.startswith("联系方式")
            endswith_colon = s.endswith(':') or s.endswith('：')
            return startswith_contact_method and endswith_colon

        while idx < n:

            text = part[idx]
            print(text)
            if check_information_begin(text):
                # 采购人 / 采购代理机构信息
                key_word = text[2:]
                idx += 1
                info = dict()
                # 开始解析内容
                while idx < n and not check_information_begin(part[idx]):
                    # 名称
                    if check_name(part[idx]):
                        info['name'] = part[idx + 1]
                        idx += 2
                    # 地址
                    elif check_address(part[idx]):
                        info['address'] = part[idx + 1]
                        idx += 2
                    # 联系人
                    elif check_person(part[idx]):
                        info['person'] = part[idx + 1].split('、')
                        idx += 2
                    # 联系方式
                    elif check_contact_method(part[idx]):
                        info['contact_method'] = part[idx + 1]
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


def parse_html(html_content: str):
    """
    解析 采购公告 的详情信息
    :param html_content:
    :return:
    """
    html = etree.HTML(html_content)
    text_list = [text.strip() for text in html.xpath('//text()')]
    result = common.filter_texts(text_list)
    print('\n'.join(result))

    def check_useful_part(title: str) -> bool:
        """
        检查是否包含有用信息的标题
        :param title:
        :return:
        """
        return ("项目基本情况" == title
                or "以下方式联系" in title
                )

    n, idx, parts = len(result), 0, []
    # 将 result 划分为 若干个部分，每部分的第一个字符串是标题
    try:
        while idx < n:
            # 找以 “一、” 这种格式开头的字符串
            index = common.startswith_chinese_number(result[idx])
            if index != -1:
                result[idx] = result[idx][2:]  # 去掉前面的序号
                if not check_useful_part(title=result[idx]):
                    continue
                pre = idx  # 开始部分
                idx += 1
                while idx < n and common.startswith_chinese_number(result[idx]) == -1:
                    idx += 1
                # 将该部分加入
                parts.append(result[pre: idx])
            else:
                idx += 1
    except BaseException as e:
        if isinstance(e, ParseError):
            raise e
        else:
            raise ParseError(
                msg='解析 parts 出现未完善情况',
                content='\n'.join(result),
                error=e
            )

    parts_length = len(parts)
    try:
        if parts_length >= 7:
            return __parse(parts, parser=StandardFormatParser)
        else:
            raise ParseError(
                msg='解析 parts 出现未完善情况',
                content='\n'.join(result)
            )

    except BaseException as e:
        if isinstance(e, ParseError):
            raise e
        raise ParseError(
            msg='解析 __parse_standard_format 失败',
            content='\n'.join(result),
            error=e
        )


def __parse(parts: list[list[str]], parser: Type[AbstractFormatParser]):
    """
    解析 parts 部分
    :param parts:
    :param parser:
    :return:
    """
    data = dict()

    # 通过标题来判断是哪个部分
    def is_project_base_situation(s):
        return s == "项目基本情况"

    def is_project_contact(s):
        return "以下方式联系" in s

    for part in parts:
        title = part[0]
        if is_project_base_situation(title):
            data.update(parser.parse_project_base_situation(part))
        elif is_project_contact(title):
            data.update(parser.parse_project_contact(part))

    return data


if __name__ == '__main__':
    with open('./test.html', 'r', encoding='utf-8') as f:
        content = f.read()
    print(json.dumps(parse_html(content), indent=4, ensure_ascii=False))
