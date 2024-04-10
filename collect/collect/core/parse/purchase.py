import json
import logging
import time
from typing import Type

from lxml import etree

from collect.collect.core.parse import (
    common,
    AbstractFormatParser
)
from collect.collect.utils import log
from collect.collect.core.parse.errorhandle import raise_error
from collect.collect.middlewares import ParseError
from contant import constants

logger = logging.getLogger(__name__)

try:
    from config.config import settings

    _DEBUG = getattr(settings, 'debug.enable', False)
except ImportError:
    _DEBUG = True

if _DEBUG:
    if len(logging.root.handlers) == 0:
        logging.basicConfig(level=logging.DEBUG)


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
        start_time = 0
        if _DEBUG:
            start_time = time.time()
            logger.debug(
                f"{log.get_function_name()} started"
            )

        def check_endswith_colon(s: str) -> bool:
            return s.endswith(":") or s.endswith("：")

        def get_colon_symbol(s: str) -> str:
            if s.endswith(":"):
                return ":"
            if s.endswith("："):
                return "："
            raise ParseError(msg="不以：或: 作为标志符", content=[s])

        def check_project_code(s: str) -> bool:
            return s.startswith("项目编号")

        def check_project_name(s: str) -> bool:

            return s.startswith("项目名称")

        def check_bid_item_quantity(s: str) -> bool:
            endswith_colon = check_endswith_colon(s)
            return s.startswith("数量") and endswith_colon

        def check_bid_item_budget(s: str) -> bool:
            endswith_colon = check_endswith_colon(s)
            return s.startswith("预算金额") and endswith_colon

        def complete_purchase_bid_item(item: dict) -> dict:
            """
            完善标项信息
            :param item:
            :return:
            """
            if not bid_item.get(constants.KEY_BID_ITEM_QUANTITY, None):
                bid_item[constants.KEY_BID_ITEM_QUANTITY] = (
                    constants.BID_ITEM_QUANTITY_UNCLEAR
                )
            return item

        try:
            data, bid_items = dict(), []
            n, idx = len(part), 0
            bid_item_index = 1
            while idx < n:
                text = part[idx]
                # 项目编号
                if check_project_code(text):
                    if not check_endswith_colon(text):
                        colon_symbol = get_colon_symbol(text)
                        project_code = text.split(colon_symbol)[-1]
                        idx += 1
                    else:
                        project_code = part[idx + 1]
                        idx += 2
                    data[constants.KEY_PROJECT_CODE] = project_code
                # 项目名称
                elif check_project_name(text):
                    if not check_endswith_colon(text):
                        colon_symbol = get_colon_symbol(text)
                        project_name = text.split(colon_symbol)[-1]
                        idx += 1
                    else:
                        project_name = part[idx + 1]
                        idx += 2
                    data[constants.KEY_PROJECT_NAME] = project_name
                # 总预算
                elif "预算总金额" in text:
                    budget = float(part[idx + 1])
                    data[constants.KEY_PROJECT_TOTAL_BUDGET] = budget
                    idx += 2
                # 标项解析
                elif text.startswith("标项名称"):
                    bid_item = dict()
                    idx += 1
                    # 标项名称
                    bid_item[constants.KEY_BID_ITEM_NAME] = part[idx]
                    idx += 1
                    while idx < n and not part[idx].startswith("标项名称"):
                        # 标项采购数量
                        if check_bid_item_quantity(part[idx]):
                            quantity = part[idx + 1]
                            if quantity == "不限":
                                quantity = constants.BID_ITEM_QUANTITY_UNLIMITED
                            bid_item[constants.KEY_BID_ITEM_QUANTITY] = quantity
                            idx += 2
                        # 标项预算金额
                        elif check_bid_item_budget(part[idx]):
                            bid_item[constants.KEY_BID_ITEM_BUDGET] = float(part[idx + 1])
                            idx += 2
                        else:
                            idx += 1
                    bid_item[constants.KEY_BID_ITEM_INDEX] = bid_item_index
                    bid_item_index += 1
                    bid_items.append(complete_purchase_bid_item(bid_item))
                else:
                    idx += 1
            data[constants.KEY_PROJECT_BID_ITEMS] = bid_items

            return data
        finally:
            if _DEBUG:
                logger.debug(
                    f"{log.get_function_name()} cost: {time.time() - start_time}"
                )

    @staticmethod
    def parse_project_contact(part: list[str]) -> dict:
        """
        解析 以下方式联系 部分
        :param part:
        :return:
        """

        start_time = 0
        if _DEBUG:
            start_time = time.time()
            logger.debug(
                f"{log.get_function_name()} started"
            )

        def check_information_begin(s: str) -> bool:
            return common.startswith_number_index(s) >= 1

        def check_name(s: str) -> bool:
            startswith_name = s.startswith("名称") or (s.find("名") < s.find("称"))
            endswith_colon = s.endswith(":") or s.endswith("：")
            return startswith_name and endswith_colon

        def check_address(s: str) -> bool:
            startswith_address = s.startswith("地址") or (s.find("地") < s.find("址"))
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
        try:
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
        finally:
            if _DEBUG:
                logger.debug(
                    f"{log.get_function_name()} cost: {time.time() - start_time}"
                )


def parse_html(html_content: str):
    """
    解析 采购公告 的详情信息
    :param html_content:
    :return:
    """
    start_time = 0
    if _DEBUG:
        start_time = time.time()
        logger.debug(
            f"{log.get_function_name()} started"
        )

    html = etree.HTML(html_content)
    # 找出所有的文本，并且进行过滤
    text_list = [text.strip() for text in html.xpath("//text()")]
    result = common.filter_texts(text_list)

    def check_useful_part(title: str) -> bool:
        """
        检查是否包含有用信息的标题
        :param title:
        :return:
        """
        return ("项目基本情况" == title) or ("以下方式联系" in title)

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
                parts.append(result[pre:idx])
            else:
                idx += 1
    except BaseException as e:
        raise_error(error=e, msg="解析 parts 出现未完善情况", content=result)
        if _DEBUG:
            logger.debug(
                f"{log.get_function_name()} (raise) cost: {time.time() - start_time}"
            )

    parts_length = len(parts)
    print('\n'.join(result))
    # print("---\n".join(['\n'.join(part) for part in parts]))
    try:
        if parts_length >= 2:
            return _parse(parts, parser=StandardFormatParser)
        else:
            raise ParseError(msg="解析 parts 出现未完善情况", content=parts)
    except BaseException as e:
        raise_error(error=e, msg="解析 __parse_standard_format 失败", content=parts)
    finally:
        if _DEBUG:
            logger.debug(
                f"{log.get_function_name()} cost: {time.time() - start_time}"
            )


def _parse(parts: list[list[str]], parser: Type[AbstractFormatParser]):
    """
    解析 parts 部分
    :param parts:
    :param parser:
    :return:
    """

    # 通过标题来判断是哪个部分
    def is_project_base_situation(s):
        return s == "项目基本情况"

    def is_project_contact(s):
        return "以下方式联系" in s

    data = dict()
    for part in parts:
        title = part[0]
        if is_project_base_situation(title):
            data.update(parser.parse_project_base_situation(part))
        elif is_project_contact(title):
            data.update(parser.parse_project_contact(part))
    return data


if __name__ == "__main__":
    content = ("<style id=\"fixTableStyle\" type=\"text/css\">th,td {border:1px solid #DDD;padding: 5px 10px;}</style>\n<meta charset=\"utf-8\"/><div id=\"template-center-mark\"><style id=\"template-center-style-mark\">#template-center-mark .selectTdClass{background-color:#edf5fa !important}#template-center-mark ol,#template-center-mark ul{margin:0;pading:0;width:95%}#template-center-mark li{clear:both;}#template-center-mark ol.custom_num2{list-style:none;}#template-center-mark ol.custom_num2 li{background-position:0 3px;background-repeat:no-repeat}#template-center-mark li.list-num2-paddingleft-1{padding-left:35px}#template-center-mark li.list-num2-paddingleft-2{padding-left:40px}#template-center-mark li.list-dash{background-image:url(http://bs.baidu.com/listicon/dash.gif)}#template-center-mark ul.custom_dash{list-style:none;}ul.custom_dash li{background-position:0 3px;background-repeat:no-repeat}#template-center-mark li.list-dash-paddingleft{padding-left:35px}#template-center-mark li.list-dot{background-image:url(http://bs.baidu.com/listicon/dot.gif)}#template-center-mark ul.custom_dot{list-style:none;}ul.custom_dot li{background-position:0 3px;background-repeat:no-repeat}#template-center-mark li.list-dot-paddingleft{padding-left:20px}#template-center-mark .list-paddingleft-1{padding-left:0}#template-center-mark .list-paddingleft-2{padding-left:30px}#template-center-mark .list-paddingleft-3{padding-left:60px}#template-center-mark div{word-wrap:break-word}#template-center-mark div p{word-break:normal}#template-center-mark table.noBorderTable td, #template-center-mark table.noBorderTable th, #template-center-mark table.noBorderTable caption{border:1px dashed #ddd !important}#template-center-mark table{margin-bottom:0px;border-collapse:collapse;display:table;text-indent: 0 !important;}#template-center-mark td,th{padding: 5px 10px !important;border: 1px solid #BBB;}#template-center-mark caption{border:1px dashed #DDD;border-bottom:0;padding:3px;text-align:center;}#template-center-mark th{border-top:1px solid #BBB;}#template-center-mark table tr.firstRow th{border-top-width:1px;}#template-center-mark td p{margin:0;padding:0;}#template-center-mark .sub{padding:0;}#template-center-mark td table{margin-bottom:0;width:100%;}#template-center-mark td table tr td{text-align:center}#template-center-mark td table tr th{text-align:center}#template-center-mark td table tr:first-of-type td{border-top-width:0}#template-center-mark td table tr:first-of-type th{border-top-width:0}#template-center-mark td table tr td:first-of-type{border-left-color:transparent}#template-center-mark td table tr td:nth-last-child(1):first-of-type{border-left-color:transparent;border-bottom-color: transparent}#template-center-mark td table tr th:first-of-type{border-left-color:transparent}#template-center-mark td table tr td:last-of-type{border-right-width:0}#template-center-mark td table tr th:last-of-type{border-right-width:0}#template-center-mark td table tr:last-of-type td{border-bottom-width:0}.hide{display:none}</style><div><div><div style=\"border:2px solid\"><div style=\"font-family:FangSong;\"><p style=\"margin-bottom: 10px;\"><span style=\"font-size: 18px;\">&nbsp; &nbsp; 项目概况</span> &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;</p><p><span style=\"font-size: 18px; line-height:30px; \">&nbsp; &nbsp; &nbsp;&nbsp;<samp style=\"font-family: FangSong\" class=\"bookmark-item uuid-1613995503981 code-projectName editDisable addContent single-line-text-input-box-cls readonly\">广西交通职业技术学院昆仑校区二期建设PPP项目（第一批）</samp>&nbsp;</span><span style=\"font-size: 18px;\">招标项目的潜在资格预审申请人应在&nbsp;<samp style=\"font-family: FangSong\" class=\"bookmark-item uuid-1613995486821 code-saleAddress editDisable addContent single-line-text-input-box-cls readonly\">广西壮族自治区公共资源交易中心网站（网址：http://gxggzy.gxzf.gov.cn）</samp>&nbsp;领取资格预审</span><span style=\"font-size: 18px;\">文件，并于&nbsp;<samp style=\"font-family: FangSong\" class=\"bookmark-item uuid-1613995523706 code-submitEndDate editDisable addContent date-selection-cls readonly\">2021-12-29 11:00:00</samp>&nbsp;</span><span style=\"font-size: 18px;\">（北京时间）前提交（上传）申请文件。</span></p></div></div></div><p style=\"margin: 17px 0;text-align: justify;line-height: 32px;break-after: avoid;font-size: 21px;font-family: SimHei, sans-serif;white-space: normal\"><span style=\"font-size: 18px;\"><strong>一、项目基本情况</strong></span>&nbsp;</p><div style=\"font-family:FangSong;line-height:20px;\"><p><span style=\"font-size: 18px;\">&nbsp; &nbsp; 项目编号：&nbsp;<samp style=\"font-family: FangSong\" class=\"bookmark-item uuid-1613995539680 code-projectCode editDisable addContent single-line-text-input-box-cls readonly\">GXZC2021-G2-005022-GXZB</samp>&nbsp;&nbsp;</span></p><p><span style=\"font-size: 18px;\">&nbsp; &nbsp; 项目名称：<samp style=\"font-family: FangSong\" class=\"bookmark-item uuid-1613995511214 code-projectName editDisable addContent single-line-text-input-box-cls readonly\">广西交通职业技术学院昆仑校区二期建设PPP项目（第一批）</samp>&nbsp;</span></p><p><span style=\"font-size: 18px;\">&nbsp; &nbsp; 采购方式：公开招标</span>&nbsp;</p><p><span style=\"font-size: 18px;\">&nbsp; &nbsp; 采购需求：</span></p><div><div style=\"padding: 10px\" class=\"template-bookmark uuid-1614088072842 code-biddingProject text-采购需求-对象面板 object-panel-cls\"><span style=\"font-size: 18px;\">&nbsp;</span> \n &nbsp; &nbsp; <samp style=\"font-family: inherit\" class=\"bookmark-item uuid-1614088081109 code-sectionNo editDisable addContent\"></samp> \n &nbsp; &nbsp; <span style=\"font-size: 18px;\">&nbsp;&nbsp;<br/><span style=\"font-family: FangSong; font-size: 18px;\">&nbsp;标项名称：</span>&nbsp;</span> \n &nbsp; &nbsp; <samp style=\"font-family: inherit\" class=\"bookmark-item uuid-1614088084067 code-bidItemName editDisable addContent single-line-text-input-box-cls readonly\">广西交通职业技术学院昆仑校区二期建设PPP项目（第一批）</samp> \n &nbsp; &nbsp; <span style=\"font-size: 18px;\">&nbsp;&nbsp;<br/><span style=\"font-family: FangSong; font-size: 18px;\"><span style=\"font-family: FangSong; font-size: 18px;\">&nbsp;预算金额(元)：</span>&nbsp;</span></span> \n &nbsp; &nbsp; <samp class=\"bookmark-item uuid-1614088096981 code-budgetPrice editDisable addContent single-line-text-input-box-cls readonly\" style=\"white-space: normal; font-family: inherit;\">1608715900</samp> \n &nbsp; &nbsp; <span style=\"font-size: 18px;\"><span style=\"font-family: FangSong; font-size: 18px;\">&nbsp;</span>&nbsp;&nbsp;<br/><span style=\"font-family: FangSong; font-size: 18px;\">&nbsp;数量：</span>&nbsp;</span> \n &nbsp; &nbsp; <samp style=\"font-family: inherit\" class=\"bookmark-item uuid-1614088086882 code-bidItemCount editDisable addContent single-line-text-input-box-cls readonly\">1</samp> \n &nbsp; &nbsp; <span style=\"font-size: 18px;\">&nbsp;&nbsp;<br/><span style=\"font-family: FangSong; font-size: 18px;\">&nbsp;单位：</span>&nbsp;</span> \n &nbsp; &nbsp; <samp style=\"font-family: inherit\" class=\"bookmark-item uuid-1614088088566 code-bidItemUnit editDisable addContent single-line-text-input-box-cls readonly\">项</samp> \n &nbsp; &nbsp; <span style=\"font-size: 18px;\">&nbsp;&nbsp;<br/><span style=\"font-family: FangSong; font-size: 18px;\">&nbsp;最高限价(元)：</span>&nbsp;</span> \n &nbsp; &nbsp; <samp style=\"font-family: inherit\" class=\"bookmark-item uuid-1614088090626 code-priceCeiling editDisable addContent single-line-text-input-box-cls readonly\">1608715900</samp> \n &nbsp; &nbsp; <span style=\"font-size: 18px;\">&nbsp;&nbsp;<br/><span style=\"font-family: FangSong; font-size: 18px;\">&nbsp;接受联合体投标：</span>&nbsp;</span> \n &nbsp; &nbsp; <samp style=\"font-family: inherit\" class=\"bookmark-item uuid-1614088092358 code-allowJointVenture2Bid editDisable addContent single-line-text-input-box-cls readonly\">是</samp> \n &nbsp; &nbsp; <span style=\"font-size: 18px;\">&nbsp;&nbsp;<br/><span style=\"font-family: FangSong; font-size: 18px;\">&nbsp;合同履约期限：</span>&nbsp;</span> \n &nbsp; &nbsp; <samp style=\"font-family: inherit\" class=\"bookmark-item uuid-1614088093927 code-ContractPerformancePeriod editDisable addContent single-line-text-input-box-cls readonly\">项目合作期为24年，其中建设期为3年，运营期为21年。</samp> \n &nbsp; &nbsp; <span style=\"font-size: 18px;\">&nbsp;&nbsp;<br/><span style=\"font-family: FangSong; font-size: 18px;\">&nbsp;简要技术或服务需求：</span>&nbsp;</span> \n &nbsp; &nbsp; <samp style=\"font-family: inherit\" class=\"bookmark-item uuid-1614088095536 code-briefSpecificationDesc editDisable addContent single-line-text-input-box-cls readonly\">采购本项目社会资本</samp> \n &nbsp; &nbsp; <span style=\"font-size: 18px;\">&nbsp;&nbsp;</span> \n &nbsp; &nbsp; <br/> \n &nbsp; &nbsp;</div></div><p><strong style=\"font-size: 18px; font-family: SimHei, sans-serif; text-align: justify;\">二、申请人的资格要求：</strong><br/></p></div><div style=\"font-family:FangSong;line-height:20px;\"><p><span style=\"font-size: 18px;\">&nbsp; &nbsp; 1.满足《中华人民共和国政府采购法》第二十二条规定；</span></p><p><span style=\"font-size: 18px;\">&nbsp; &nbsp; 2.落实政府采购政策需满足的资格要求：&nbsp;<samp style=\"font-family: FangSong\" class=\"bookmark-item uuid-1613995582549 code-purchasingPolicy editDisable addContent\"></samp>&nbsp;。&nbsp;<samp style=\"font-family: FangSong\" class=\"bookmark-item uuid-1614050818011 code-otherInfo editDisable addContent\"></samp>&nbsp;&nbsp;</span></p><p><span style=\"font-size: 18px;\">&nbsp; &nbsp; 3.本项目的特定资格要求：&nbsp;&nbsp;<samp style=\"font-family: FangSong\" class=\"bookmark-item uuid-1613995590089 code-biddingQualification editDisable addContent multi-line-text-input-box-cls readonly\">本次招标接受联合体投标。联合体成员不得超过3家，须提供有效的联合体协议书，明确联合体牵头人，约定各方承担的工作和义务，以一个申请人的身份共同投标，联合体中有同类资质的申请人按照联合体分工承担相同工作的，应当按照资质等级较低的申请人确定资质等级。联合体各方均须满足本公告申请人的资格要求第1、2条的要求；以联合体形式参加政府采购活动的，联合体各方不得再单独参加或者与其他申请人另外组成联合体参加同一合同项下的政府采购活动；联合体各方应当共同与采购人签订项目合同就项目合同约定的事项对采购人承担连带责任。<br/>资格要求不符合的申请人其文件按无效投标处理。<br/>对在信用中国、中国政府采购网等渠道列入失信被执行人、重大税收违法案件当事人名单、政府采购严重违法失信行为记录名单及其他不符合《中华人民共和国政府采购法》第二十二条规定条件的申请人，不得参与政府采购活动。如申请人为联合体，联合体各成员均须满足上述要求，联合体中任一成员不满足，视同联合体不符合要求。<br/>申请人已具备相应的资质和能力，依法能够自行建设、生产或者提供本项目勘察设计、施工、货物的，本项目相应的勘察设计、施工、货物可由申请人自行承担，不再招标。<br/></samp>&nbsp;&nbsp;</span></p></div><p style=\"margin: 17px 0;text-align: justify;line-height: 32px;break-after: avoid;font-size: 18px;font-family: SimHei, sans-serif;white-space: normal\"><span style=\"font-size: 18px;\"><strong>三、领取资格预审文件</strong></span></p><div style=\"font-family:FangSong;line-height:20px;\"><p><span style=\"font-size: 18px; text-decoration: none;\">&nbsp; &nbsp; 时间：&nbsp;<samp style=\"font-family: FangSong\" class=\"bookmark-item uuid-1613995599288 code-saleStartDate editDisable addContent date-selection-cls readonly\">2021-12-06</samp>&nbsp;至&nbsp;<samp style=\"font-family: FangSong\" class=\"bookmark-item uuid-1613995603701 code-saleEndDate editDisable addContent date-selection-cls readonly\">2021-12-29</samp>&nbsp;，每天上午&nbsp;<samp style=\"font-family: FangSong\" class=\"bookmark-item uuid-1613995623845 code-saleForenoonStartTime editDisable addContent time-selection-cls readonly\">00:00:00</samp>&nbsp;-&nbsp;<samp style=\"font-family: FangSong\" class=\"bookmark-item uuid-1613995628734 code-saleForenoonEndTime editDisable addContent time-selection-cls readonly\">12:00:00</samp>&nbsp;，下午&nbsp;<samp style=\"font-family: FangSong\" class=\"bookmark-item uuid-1613995631279 code-saleAfternoonStartTime editDisable addContent time-selection-cls readonly\">12:00:00</samp>&nbsp;-&nbsp;<samp style=\"font-family: FangSong\" class=\"bookmark-item uuid-1613995633994 code-saleAfternoonEndTime editDisable addContent time-selection-cls readonly\">23:59:59</samp>&nbsp;（北京时间，法定节假日除外）</span></p><p><span style=\"font-size: 18px;\">&nbsp; &nbsp; 地点：&nbsp;<samp style=\"font-family: FangSong\" class=\"bookmark-item uuid-1613995609681 code-saleAddress editDisable addContent single-line-text-input-box-cls readonly\">广西壮族自治区公共资源交易中心网站（网址：http://gxggzy.gxzf.gov.cn）</samp>&nbsp;&nbsp;</span></p><p><span style=\"font-size: 18px;\">&nbsp; &nbsp; 方式：&nbsp;<samp style=\"font-family: FangSong\" class=\"bookmark-item uuid-1613995612914 code-saleType editDisable addContent single-line-text-input-box-cls readonly\">1.本项目资格预审文件为网上免费下载。凡满足要求并有意参加项目资格预审的申请人，请于2021年12月6日至2021年12月29日，登陆广西壮族自治区公共资源交易中心网站（网址：http://gxggzy.gxzf.gov.cn），完成投标单位账号注册即可下载资格预审文件。 2.本项目无图纸或其他技术资料。</samp>&nbsp;&nbsp;</span></p></div><p style=\"margin: 17px 0;text-align: justify;line-height: 32px;break-after: avoid;font-size: 18px;font-family: SimHei, sans-serif;white-space: normal\"><span style=\"font-size: 18px;\"><strong>四、资格预审申请文件的组成及格式</strong></span></p><div style=\"font-family:FangSong; font-size:18px; line-height:30px;\"><p>&nbsp; &nbsp;&nbsp;<samp style=\"font-family: FangSong\" class=\"bookmark-item uuid-1613995646895 code-compositionAndFormat editDisable addContent multi-line-text-input-box-cls readonly\">详见第四章“资格预审申请文件格式”。</samp>&nbsp;&nbsp; &nbsp;&nbsp;&nbsp;&nbsp;</p></div><p style=\"margin: 17px 0;text-align: justify;line-height: 32px;break-after: avoid;font-size: 18px;font-family: SimHei, sans-serif;white-space: normal\"><span style=\"font-size: 18px;\"><strong>五、资格预审的审查标准及方法</strong></span>&nbsp;</p><div style=\"font-size:18px; font-family:FangSong; line-height:20px;\"><p>&nbsp; &nbsp; 1.资格预审的审查标准：&nbsp;<samp style=\"font-family: FangSong\" class=\"bookmark-item uuid-1613995652938 code-biddingQualificationExaminationStandard editDisable addContent multi-line-text-input-box-cls readonly\">本次资格预审采用有限数量制。</samp>&nbsp;</p><p>&nbsp; &nbsp; 2.资格预审的审查方法：&nbsp;<samp style=\"font-family: FangSong\" class=\"bookmark-item uuid-1613995656914 code-biddingQualificationReviewMethod editDisable addContent multi-line-text-input-box-cls readonly\">具体审查方法详见资格预审文件“第三章资格审查办法”。</samp>&nbsp;&nbsp;</p></div><p style=\"margin: 17px 0;text-align: justify;line-height: 32px;break-after: avoid;font-size: 21px;font-family: SimHei, sans-serif;white-space: normal\"><span style=\"font-size: 18px;line-height:30px;\"><strong>六、拟邀请参加投标的供应商数量</strong></span></p><div style=\"font-family:FangSong; font-size:18px; line-height:20px;\"><p>&nbsp; &nbsp;&nbsp;&nbsp;<samp style=\"font-family:FangSong\" class=\"bookmark-item uuid-1614051157863 code-supplierSelectionMethod editDisable addContent single-line-text-input-box-cls readonly\">邀请全部通过资格预审供应商参加投标</samp>&nbsp;</p></div><p style=\"margin: 17px 0;text-align: justify;line-height: 30px;break-after: avoid;font-size: 21px;font-family: SimHei, sans-serif;white-space: normal\"><span style=\"font-size: 18px;line-height:30px;\"><strong>七、申请文件提交</strong></span></p><p><span style=\"font-size: 18px; font-family:FangSong;\">&nbsp; &nbsp; 应在&nbsp;<samp style=\"font-family: FangSong\" class=\"bookmark-item uuid-1613995681317 code-submitEndDate editDisable addContent date-selection-cls readonly\">2021-12-29 11:00:00</samp>&nbsp;（北京时间）前，将申请文件提交至&nbsp;<samp style=\"font-family: FangSong\" class=\"bookmark-item uuid-1613995688670 code-tenderPlace editDisable addContent single-line-text-input-box-cls readonly\">广西壮族自治区公共资源交易中心(广西南宁市怡宾路6号自治区政务服务中心四楼)（具体资格预审开标时根据电子屏幕显示的安排）</samp>&nbsp;&nbsp;。</span></p><p style=\"margin: 17px 0;text-align: justify;line-height: 30px;break-after: avoid;font-size: 21px;font-family: SimHei, sans-serif;white-space: normal\"><span style=\"font-size: 18px;line-height:30px;\"><strong>八、资格预审日期</strong></span></p><p><span style=\"font-size: 18px; font-family:FangSong;\">&nbsp; &nbsp; 资格预审日期为申请文件提交截止时间至&nbsp;<samp style=\"font-family: FangSong\" class=\"bookmark-item uuid-1613995695296 code-bidOpeningTime editDisable addContent date-selection-cls readonly\">2021-12-29 11:00:00</samp>&nbsp;前。</span></p><p style=\"margin: 17px 0;text-align: justify;line-height: 32px;break-after: avoid;font-size: 21px;font-family: SimHei, sans-serif;white-space: normal\"><span style=\"font-size: 18px;line-height:30px;\"><strong>九、公告期限</strong></span></p><p><span style=\"font-size: 18px; font-family:FangSong;\">&nbsp; &nbsp; 自本公告发布之日起5个工作日。</span></p><p style=\"margin: 17px 0;text-align: justify;line-height: 30px;break-after: avoid;font-size: 18px;font-family: SimHei, sans-serif;white-space: normal\"><span style=\"font-size: 18px;\"><strong>十、其他补充事宜</strong></span></p><p><span style=\"font-size: 18px;font-family:FangSong;line-height:30px;\">&nbsp; &nbsp;&nbsp;<samp style=\"font-family: FangSong\" class=\"bookmark-item uuid-1613995710003 code-otherBusiness editDisable addContent multi-line-text-input-box-cls readonly\">资格预审公告在以下媒体发布：中国政府采购网；广西政府采购网/广西政府购买服务信息平台；广西壮族自治区公共资源交易中心。<br/>采购人可能对本资格预审公告进行修改，有修改将发布澄清公告，与本项目相关的信息以最后发出书面文件为准。<br/>资格预审申请文件递交结束后，采购人组织资格审查委员会对所有递交资格预审申请文件的申请人进行资格预审，按规定将资格预审结果进行公示。公示未能入选成为本项目的申请人，采购人和采购代理机构不承担解释的责任。<br/>采购人于资格预审结束以公告方式通知参加资格预审社会资本，资格预审结果公告发布资格预审公告媒体。<br/>为避免申请人不良诚信记录发生，配合采购单位政府采购项目执行和备案，未在政采云注册申请人可获取采购文件后登录政采云进行注册，在操作过程中遇到问题或者需要技术支持，请致电政采云客服热线：400-881-7190。<br/>落实政府采购政策：政府采购促进中小企业发展管理办法、关于政府采购支持监狱企业发展有关问题的通知、关于促进残疾人就业政府采购政策的通知、节能产品政府采购实施意见、财政部 环保总局关于环境标志产品政府采购实施的意见、关于调整优化节能产品、环境标志产品政府采购执行机制的通知。</samp>&nbsp; &nbsp; &nbsp;</span>&nbsp;</p><p style=\"margin: 17px 0;text-align: justify;line-height: 32px;break-after: avoid;font-size: 21px;font-family: SimHei, sans-serif;white-space: normal\"><span style=\"font-size: 18px;\"><strong>十一、凡对本次资格预审提出询问，请按以下方式联系</strong></span></p><div style=\"font-family:FangSong;line-height:20px;\"><div style=\"font-family:FangSong;line-height:30px;\"><p><span style=\"font-size: 18px;\">&nbsp; &nbsp; 1.采购人信息</span></p><p><span style=\"font-size: 18px;\">&nbsp; &nbsp; 名&nbsp;&nbsp;&nbsp; 称：&nbsp;<samp style=\"font-family: FangSong\" class=\"bookmark-item uuid-1613995724274 code-purchase editDisable addContent single-line-text-input-box-cls readonly\">广西交通职业技术学院</samp>&nbsp;&nbsp;</span></p><p><span style=\"font-size: 18px;\">&nbsp; &nbsp; 地&nbsp;&nbsp;&nbsp; 址：&nbsp;<samp style=\"font-family: FangSong\" class=\"bookmark-item uuid-1613995727902 code-purchaserContactAddr editDisable addContent single-line-text-input-box-cls readonly\">南宁市兴宁区昆仑大道1258号</samp>&nbsp;&nbsp;</span><span style=\"font-size: 18px;\">&nbsp; &nbsp;&nbsp;</span></p><p><span style=\"font-size: 18px;\">&nbsp; &nbsp; 项目联系人：&nbsp;&nbsp;</span><samp class=\"bookmark-item uuid-1613995740962 code-purchaserContactPerson editDisable addContent single-line-text-input-box-cls readonly\" style=\"font-size: 18px; font-family: FangSong;\">梁老师、刘老师</samp><span style=\"font-size: 18px;\">&nbsp;</span></p><p><span style=\"font-size: 18px;\">&nbsp; &nbsp; 项目联系方式：&nbsp;<samp style=\"font-family: FangSong\" class=\"bookmark-item uuid-1613995745754 code-purchaserContactPhone editDisable addContent single-line-text-input-box-cls readonly\">0771-5650225</samp>&nbsp;&nbsp;</span></p><p><span style=\"font-size: 18px;\">&nbsp; &nbsp; 2.采购代理机构信息</span></p><p><span style=\"font-size: 18px;\">&nbsp; &nbsp; 名&nbsp;&nbsp;&nbsp; 称：&nbsp;<samp style=\"font-family: FangSong\" class=\"bookmark-item uuid-1613995757333 code-agencyOrg editDisable addContent single-line-text-input-box-cls readonly\">国信国际工程咨询集团股份有限公司</samp>&nbsp;&nbsp;</span></p><p><span style=\"font-size: 18px;\">&nbsp; &nbsp; 地&nbsp;&nbsp;&nbsp; 址：&nbsp;<samp style=\"font-family: FangSong\" class=\"bookmark-item uuid-1613995761049 code-agencyContactAddr editDisable addContent single-line-text-input-box-cls readonly\">北京市海淀区首体南路22号楼10层（执行机构地址：广西南宁市青秀区中柬路8号龙光世纪2号楼1716室）</samp>&nbsp;&nbsp;</span>&nbsp;</p><p><span style=\"font-size: 18px;\">&nbsp; &nbsp; 项目联系人：&nbsp;<samp style=\"font-family: FangSong\" class=\"bookmark-item uuid-1613995767837 code-agencyContactPerson editDisable addContent single-line-text-input-box-cls readonly\">康晗</samp>&nbsp;&nbsp;</span></p><p><span style=\"font-size: 18px;\">&nbsp; &nbsp; 项目联系方式：&nbsp;<samp style=\"font-family: FangSong\" class=\"bookmark-item uuid-1613995771013 code-agencyContactPhone editDisable addContent single-line-text-input-box-cls readonly\">0771-5514661</samp>&nbsp;&nbsp;</span></p></div></div></div><p><br/></p><p><br/></p><p><br/></p><p><br/></p><p><br/></p><p><br/></p><p><br/></p><p><br/></p><p><br/></p></div><divider></divider><p style=\"white-space: normal; line-height: 24px;\"><strong><span style=\"line-height: 24px; font-family: 宋体;\">附件信息:</span></strong></p><ul class=\"fjxx\" style=\"font-size: 16px;margin-left: 38px;color: #0065ef;list-style-type: none;\"><li><p style=\"display:inline-block\"><a href=\"https://zcy-gov-open-doc.oss-cn-north-2-gov-1.aliyuncs.com/1014AN/339900/10006056170/202112/df5f9e59-a326-473a-a840-2a49b4f1d3fe\">广西交通职业技术学院昆仑校区二期建设PPP项目（第一批）资格预审公告..pdf</a></p><p style=\"display:inline-block;margin-left:20px;width: 8em;\">3.7 M</p></li></ul>")
    print(json.dumps(parse_html(content), indent=4, ensure_ascii=False))
