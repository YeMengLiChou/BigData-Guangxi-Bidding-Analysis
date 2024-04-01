import json
import re
from typing import Type

from lxml import etree

from collect.collect.core.parse import common
from collect.collect.core.parse import AbstractFormatParser
from collect.collect.middlewares import ParseError
from contant import constants


class WinBidStandardFormatParser(AbstractFormatParser):

    @staticmethod
    def __parse_win_bids(part: list[str]) -> list:
        """
        解析 中标结果
        :param part:
        :return:
        """

        def is_bid_item_index(s: str) -> bool:
            return s.isdigit()

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
                address_text = ''.join(part[pre:idx])

                bid_item[constants.KEY_BID_ITEM_INDEX] = int(text)
                bid_item[constants.KEY_BID_ITEM_NAME] = None
                bid_item[constants.KEY_BID_ITEM_AMOUNT] = __parse_win_bit_item_amount(price_text)
                bid_item[constants.KEY_BID_ITEM_SUPPLIER] = supplier_text
                bid_item[constants.KEY_BID_ITEM_SUPPLIER_ADDRESS] = address_text

                data.append(bid_item)
            else:
                idx += 1
        return data

    @staticmethod
    def parse_not_win_bids(part: list[str]) -> list:
        pass

    @staticmethod
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
                    and
                    "中标结果" in s
                    and
                    (s.endswith('：') or s.endswith(":"))
            )

        def is_not_win_bid_result(s: str) -> bool:
            """
            判断是否为 “2.废标结果”
            :param s:
            :return:
            """
            return (
                    common.startswith_number_index(s) == 2
                    and
                    "废标结果" in s
                    and
                    (s.endswith('：') or s.endswith(":"))
            )

        data, idx, n = [], 1, len(part)
        while idx < n:
            text = part[idx]
            if is_win_bid_result(text):
                pre = idx + 1
                while idx < n and not is_not_win_bid_result(part[idx]):
                    idx += 1
                data.append(
                    *WinBidStandardFormatParser.__parse_win_bids(part=part[pre: idx])
                )
            elif is_not_win_bid_result(text):
                data.append(
                    *WinBidStandardFormatParser.__parse_not_win_bids(part=part[idx + 1:])
                )
            else:
                idx += 1
        else:
            return data

    @staticmethod
    def parse_review_expert(part: list[str]) -> dict:
        data = dict()
        dist = part[-1]
        if "，" in dist:
            split_symbol = "，"
        elif "、" in dist:
            split_symbol = "、"
        else:
            split_symbol = ","
        persons = dist.split(split_symbol)
        review_experts = []
        for i in range(len(persons)):
            if "采购人代表" in persons[i]:
                idx = persons[i].index("（")
                if idx == 0:
                    idx = persons[i].rindex("）")
                    representor = persons[i][idx + 1:]
                else:
                    representor = persons[i][: idx]
                data[constants.KEY_PROJECT_PURCHASE_REPRESENTOR] = representor
                review_experts.append(representor)
            else:
                review_experts.append(persons[i])
        return data


def parse_response_data(data):
    """
    解析列表api响应中的内容
    :param data:
    :return:
    """

    def check_is_win_bid(path_name: str) -> bool:
        """
        判断是否中标
        :param path_name:
        :return:
        """
        return path_name == '废标结果'

    result = []
    for item in data:
        result_api_meta = {
            constants.KEY_PROJECT_RESULT_ARTICLE_ID: item['articleId'],  # 结果公告的id
            # "result_announcement_title": item['title'],  # 结果公告的标题
            # "category": item['pathName'],  # 公告类型
            constants.KEY_PROJECT_RESULT_PUBLISH_DATE: int(item['publishDate']),  # 发布日期
            constants.KEY_PROJECT_DISTRICT_CODE: item['districtCode'],  # 地区编号（可能为空串）
            constants.KEY_PROJECT_DISTRICT_NAME: item['districtName'],  # 地区名称（可能为空串）
            constants.KEY_PROJECT_CATALOG: item['gpCatalogName'],  # 采购物品名称
            constants.KEY_PROJECT_PROCUREMENT_METHOD: item['procurementMethod'],  # 采购方式
            constants.KEY_PROJECT_BID_OPENING_TIME: item['bidOpeningTime'],  # 开标时间
            constants.KEY_PROJECT_IS_WIN_BID: check_is_win_bid(item['pathName'])  # 是否中标
        }
        result.append(result_api_meta)
    return result


def parse_html(html_content: str, is_wid_bid: bool):
    """
    解析 结果公告 中的 content
    :param html_content:
    :param is_wid_bid: 是否为中标结果
    :return:
    """

    html = etree.HTML(html_content)
    text_list = [text.strip() for text in html.xpath('//text()')]
    result = common.filter_texts(text_list)

    # print('\n'.join(result))
    def check_useful_part(title: str) -> bool:
        """
        检查是否包含有用信息的标题
        :param title:
        :return:
        """
        return ("中标（成交）信息" == title
                or "评审专家" in title
                )

    n, idx, parts = len(result), 0, []
    try:
        while idx < n:
            # 找以 “一、” 这种格式开头的字符串
            index = common.startswith_chinese_number(result[idx])
            if index != -1:
                # 去掉前面的序号
                result[idx] = result[idx][2:]
                if not check_useful_part(title=result[idx]):
                    continue
                # 开始部分
                pre = idx
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
                msg='解析 parts 异常',
                content='\n'.join(result),
                error=e
            )
    try:
        if is_wid_bid:
            return __parse_win_bid(parts)
        else:
            return __parse_not_win_bid(parts)
    except BaseException as e:
        if isinstance(e, ParseError):
            raise e
        else:
            raise ParseError(
                msg='解析 bid 异常',
                content='\n'.join(parts),
                error=e
            )


def __parse_win_bid(parts: list[list[str]]):
    """
    解析 中标结果
    :param parts:
    :return:
    """
    data, n, idx = dict(), len(parts), 0

    def is_bids_information(title: str) -> bool:
        return "中标（成交）信息" == title

    def is_review_expert(title: str) -> bool:
        return "评审专家" in title

    def parse_bids_information(_part: list[str], parser: Type[AbstractFormatParser]) -> dict:
        """
        解析中标信息
        :param parser:
        :param _part:
        :return:
        """
        return parser.parse_bids_information(part=_part)

    def parse_review_expert(_part: list[str], parser: Type[AbstractFormatParser]) -> dict:
        """
        解析评审专家信息
        :param parser:
        :param _part:
        :return:
        """
        return parser.parse_review_expert(part=_part)

    for part in parts:
        if is_bids_information(title=part[0]):
            data.update(
                parse_bids_information(
                    _part=part,
                    parser=WinBidStandardFormatParser
                )
            )
        elif is_review_expert(title=part[0]):
            data.update(
                parse_review_expert(
                    _part=part,
                    parser=WinBidStandardFormatParser
                )
            )
    return data


def __parse_win_bit_item_amount(text: str) -> tuple[float, bool]:
    """
    解析中标结果中的项目金额
    :param text:
    :return: 返回 (数值， 是否为百分比)
    """

    # TODO 负责解析项目金额，适应各种格式
    try:
        #  格式1：单项合价（元） ③＝①×②：1278820（元）
        if text.startswith('单项合价'):
            # TODO 优化正则表达式
            result = re.match(r'[^0-9]*(\d*(\.\d+)?)[^0-9]*', text)
            if result:
                amount = float(result.group(1))
                is_percent = False
                return amount, is_percent

        if text.startswith("报价"):
            if text.endswith("（元）"):
                result = re.match(r'[^0-9]*(\d*(\.\d+)?)[^0-9]*', text)
                if result:
                    amount = float(result.group(1))
                    is_percent = False
                    return amount, is_percent
            if text.endswith("（%）"):
                result = re.match(r'[^0-9]*(\d*(\.\d+)?)[^0-9]*', text)
                if result:
                    amount = float(result.group(1))
                    is_percent = True
                    return amount, is_percent
        raise ParseError(
            msg='标项金额存在未发现的格式',
            content=text
        )

    except BaseException as e:
        if isinstance(e, ParseError):
            raise e
        raise ParseError(
            msg='解析中标项金额出错',
            content=content,
            error=e
        )


def __parse_not_win_bid(texts: list[str]):
    data = dict()
    vis = dict()
    n = len(texts)
    idx = 0
    print(json.dumps(data, indent=4, ensure_ascii=False))
    return data


if __name__ == '__main__':
    content = ""
    with open('./test.html', 'r', encoding='utf-8') as f:
        content += f.read()
    res = parse_html(content, True)
