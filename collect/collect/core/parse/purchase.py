import json
import logging
import time
from typing import Type

from lxml import etree

from collect.collect.core.parse import common, AbstractFormatParser
from collect.collect.utils import log, symbol_tools as sym
from collect.collect.core.parse.errorhandle import raise_error
from collect.collect.middlewares import ParseError
from contant import constants

logger = logging.getLogger(__name__)

try:
    from config.config import settings

    _DEBUG = getattr(settings, "debug.enable", False)
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
            logger.debug(f"{log.get_function_name()} started")

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
            return s.startswith("数量") and sym.endswith_colon_symbol(s)

        def check_bid_item_budget(s: str) -> bool:
            return s.startswith("预算金额") and sym.endswith_colon_symbol(s)

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
                    if not sym.endswith_colon_symbol(text):
                        colon_symbol = get_colon_symbol(text)
                        project_code = text.split(colon_symbol)[-1]
                        idx += 1
                    else:
                        project_code = part[idx + 1]
                        idx += 2
                    data[constants.KEY_PROJECT_CODE] = project_code
                # 项目名称
                elif check_project_name(text):
                    if not sym.endswith_colon_symbol(text):
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
                            bid_item[constants.KEY_BID_ITEM_BUDGET] = float(
                                part[idx + 1]
                            )
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
            logger.debug(f"{log.get_function_name()} started")

        def check_information_begin(s: str) -> bool:
            return common.startswith_number_index(s) >= 1

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
        logger.debug(f"{log.get_function_name()} started")

    result = common.parse_html(html_content=html_content)

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
                result[idx] = result[idx][
                    result[idx].index("、") + 1 :
                ]  # 去掉前面的序号
                if not check_useful_part(title=result[idx]):
                    continue
                pre = idx  # 开始部分
                idx += 1
                # 以 "<中文数字>、“ 形式划分区域
                # 部分可能带有上面的格式，但是最后面带有冒号：
                while idx < n and (
                    common.startswith_chinese_number(result[idx]) == -1
                    or sym.endswith_colon_symbol(result[idx])
                ):
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
    try:
        if parts_length >= 2:
            return _parse(parts, parser=StandardFormatParser)
        else:
            raise ParseError(
                msg="解析 parts 出现未完善情况",
                content=["\n".join(part) for part in parts],
            )
    except BaseException as e:
        raise_error(error=e, msg="解析 __parse_standard_format 失败", content=parts)
    finally:
        if _DEBUG:
            logger.debug(f"{log.get_function_name()} cost: {time.time() - start_time}")


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
    content = '<style id="fixTableStyle" type="text/css">th,td {border:1px solid #DDD;padding: 5px 10px;}</style><div><div style="border:2px solid"><div style="font-family:FangSong;"><p style="margin-bottom: 10px;"><span style="font-size: 18px;">&nbsp; &nbsp; 项目概况</span> &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;</p><p><span style="font-size: 18px; line-height:30px; ">&nbsp; &nbsp; <span class="bookmark-item uuid-1595987346914 code-00003 addWord single-line-text-input-box-cls">血流动力学检测仪、多功能监护仪采购</span></span><span style="font-size: 18px;">采购项目的潜在供应商应在<span class="bookmark-item uuid-1596255404623 code-24007 editDisable single-line-text-input-box-cls readonly">“政府采购云平台”（https://www.zcygov.cn）</span></span><span style="font-size: 18px;">获取采购文件，并于<span class="bookmark-item uuid-1595988749299 code-24011 addWord date-time-selection-cls">2021年12月31日 09:30</span></span><span style="font-size: 18px;">（北京时间）前提交响应文件。</span>&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;&nbsp;</p></div></div></div><p style="margin: 17px 0;text-align: justify;line-height: 30px;break-after: avoid;font-size: 21px;font-family: SimHei, sans-serif;white-space: normal"><span style="font-size: 18px;"><strong>一、项目基本情况</strong></span> &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;</p><div style="font-family:FangSong;line-height:20px;"><p><span style="font-size: 18px;">&nbsp; &nbsp; 项目编号：<span class="bookmark-item uuid-1595987359344 code-00004 addWord single-line-text-input-box-cls">WZZC2021-J1-000544-ZYZB</span>&nbsp;</span></p><p><span style="font-size: 18px;">&nbsp; &nbsp; 项目名称：<span class="bookmark-item uuid-1595987369689 code-00003 addWord single-line-text-input-box-cls">血流动力学检测仪、多功能监护仪采购</span>&nbsp;</span></p><p><span style="font-size: 18px;">&nbsp; &nbsp; 采购方式：竞争性谈判</span>&nbsp;</p><p><span style="font-size: 18px;">&nbsp; &nbsp; 预算总金额（元）：<span class="bookmark-item uuid-1595987387629 code-AM01400034 addWord numeric-input-box-cls">1540000</span>&nbsp;</span></p><p><span style="font-size: 18px;">&nbsp; &nbsp;&nbsp;</span><span style="font-size: 18px;">采购需求：</span></p><div style="font-family: FangSong; white-space: normal; line-height: 20px;"><p><span style="font-size: 18px;"></span></p><div><div class="template-bookmark uuid-1593419700012 code-AM014230011 text-招标项目概况 object-panel-cls" style="padding: 10px"><p style="line-height: normal;"><span style="display: inline-block;"><span class="bookmark-item uuid-1595941042480 code-AM014sectionNo editDisable single-line-text-input-box-cls">标项一</span></span><br/>标项名称:<span class="bookmark-item uuid-1593432150293 code-AM014bidItemName editDisable single-line-text-input-box-cls">梧州市工人医院血流动力学检测仪</span><br/>数量:<span class="bookmark-item uuid-1595941076685 code-AM014bidItemCount editDisable single-line-text-input-box-cls">1</span><br/>预算金额（元）:<span class="bookmark-item uuid-1593421137256 code-AM014budgetPrice editDisable single-line-text-input-box-cls">640000</span><br/>简要规格描述或项目基本概况介绍、用途：<span class="bookmark-item uuid-1593421202487 code-AM014briefSpecificationDesc editDisable single-line-text-input-box-cls">一、性能特点：<br/>1．功能描述：通过微创方式获得到血流动力学参数，用于监测目标导向的液体治疗和药物干预...<br/>（如需进一步了解详细内容，详见谈判文件第三章）</span></p><p style="line-height: normal;">最高限价（如有）：<samp class="bookmark-item uuid-1598878264729 code-AM014priceCeilingY editDisable single-line-text-input-box-cls" style="font-family: inherit;">/</samp></p><p style="line-height: normal;">合同履约期限：<samp class="bookmark-item uuid-1598878268033 code-AM014ContractPerformancePeriodY editDisable single-line-text-input-box-cls" style="font-family: inherit;">签订合同之日起至付清合同全部款项当日</samp></p><p style="line-height: normal;">本项目（<samp class="bookmark-item uuid-1598878270792 code-AM014allowJointVenture2Bid editDisable single-line-text-input-box-cls" style="font-family: inherit;">否</samp>）接受联合体投标<br/>备注：<span class="bookmark-item uuid-1593432166973 code-AM014remarks editDisable single-line-text-input-box-cls">本项目接受同一供应商对多个分标报价，但同一供应商只能成交其中一个分标。若某供应商为多个分标排序第一成交候选人，则由采购人在确认成交供应商阶段自行选择保留其在某分标作为成交供应商资格。</span></p></div><div class="template-bookmark uuid-1593419700012 code-AM014230011 text-招标项目概况 object-panel-cls" style="padding: 10px"><p style="line-height: normal;"><span style="display: inline-block;"><span class="bookmark-item uuid-1595941042480 code-AM014sectionNo editDisable single-line-text-input-box-cls">标项二</span></span><br/>标项名称:<span class="bookmark-item uuid-1593432150293 code-AM014bidItemName editDisable single-line-text-input-box-cls">梧州市工人医院多功能监护仪</span><br/>数量:<span class="bookmark-item uuid-1595941076685 code-AM014bidItemCount editDisable single-line-text-input-box-cls">6</span><br/>预算金额（元）:<span class="bookmark-item uuid-1593421137256 code-AM014budgetPrice editDisable single-line-text-input-box-cls">900000</span><br/>简要规格描述或项目基本概况介绍、用途：<span class="bookmark-item uuid-1593421202487 code-AM014briefSpecificationDesc editDisable single-line-text-input-box-cls">1.模块化插件式床边监护仪，主机、显示屏和插件槽一体化设计，主机插槽...（如需进一步了解详细内容，详见谈判文件第三章）</span></p><p style="line-height: normal;">最高限价（如有）：<samp class="bookmark-item uuid-1598878264729 code-AM014priceCeilingY editDisable single-line-text-input-box-cls" style="font-family: inherit;">/</samp></p><p style="line-height: normal;">合同履约期限：<samp class="bookmark-item uuid-1598878268033 code-AM014ContractPerformancePeriodY editDisable single-line-text-input-box-cls" style="font-family: inherit;">签订合同之日起至付清合同全部款项当日</samp></p><p style="line-height: normal;">本项目（<samp class="bookmark-item uuid-1598878270792 code-AM014allowJointVenture2Bid editDisable single-line-text-input-box-cls" style="font-family: inherit;">否</samp>）接受联合体投标<br/>备注：<span class="bookmark-item uuid-1593432166973 code-AM014remarks editDisable single-line-text-input-box-cls">本项目接受同一供应商对多个分标报价，但同一供应商只能成交其中一个分标。若某供应商为多个分标排序第一成交候选人，则由采购人在确认成交供应商阶段自行选择保留其在某分标作为成交供应商资格。</span></p></div></div></div><p><strong style="font-size: 18px; font-family: SimHei, sans-serif; text-align: justify;"><br/></strong></p><p><strong style="font-size: 18px; font-family: SimHei, sans-serif; text-align: justify;">二、申请人的资格要求：</strong><span style="font-size: 18px;"><br/></span></p></div><div style="font-family:FangSong;line-height:20px;"><p><span style="font-size: 18px;">&nbsp; &nbsp; 1.满足《中华人民共和国政府采购法》第二十二条规定；</span></p><p><span style="font-size: 18px;">&nbsp; &nbsp; 2.落实政府采购政策需满足的资格要求：<span class="bookmark-item uuid-1595987425520 code-23021 editDisable multi-line-text-input-box-cls readonly">无</span>&nbsp;</span></p><p><span style="font-size: 18px;">&nbsp; &nbsp; 3.本项目的特定资格要求：<span class="bookmark-item uuid-1596277056884 code-24002 editDisable multi-line-text-input-box-cls readonly">分标1、2：持有食品药品监督管理部门颁发的有效证件：生产企业须持有《医疗器械生产许可证》；经营企业经营第二类医疗器械的须持有《第二类医疗器械经营备案凭证》，经营第三类医疗器械的须持有《医疗器械经营许可证》。</span>&nbsp;</span></p></div><p style="margin: 17px 0;text-align: justify;line-height: 30px;break-after: avoid;font-size: 18px;font-family: SimHei, sans-serif;white-space: normal"><span style="font-size: 18px;"><strong>三、获取采购文件</strong></span></p><div style="font-family:FangSong;line-height:20px;"><p><span style="font-size: 18px;">&nbsp; &nbsp; </span><span style="font-size: 18px; text-decoration: none;">时间：<span class="bookmark-item uuid-1595988798365 code-24003 addWord date-selection-cls">2021年12月27日</span>至<span class="bookmark-item uuid-1595988809453 code-24004 editDisable date-selection-cls readonly">2021年12月30日</span>，每天上午<span class="bookmark-item uuid-1595988818147 code-24005 addWord morning-time-section-selection-cls">08:00至12:00</span>，下午<span class="bookmark-item uuid-1595988825597 code-24006 addWord afternoon-time-section-selection-cls">12:00至18:00</span>（北京时间，法定节假日除外）</span></p><p><span style="font-size: 18px;">&nbsp; &nbsp; 地点（网址）：<span class="bookmark-item uuid-1595988837737 code-24007 editDisable single-line-text-input-box-cls readonly">“政府采购云平台”（https://www.zcygov.cn）</span>&nbsp;&nbsp;</span></p><p><span style="font-size: 18px;">&nbsp; &nbsp; 方式：<span class="bookmark-item uuid-1595988845455 code-24008 editDisable single-line-text-input-box-cls readonly">供应商登录政采云平台https://www.zcygov.cn/在线申请获取采购文件（进入“项目采购”应用，在获取采购文件菜单中选择项目，申请获取采购文件）</span>&nbsp;&nbsp;</span></p><p><span style="font-size: 18px;">&nbsp; &nbsp; 售价（元）：<span class="bookmark-item uuid-1595988851488 code-24009 addWord numeric-input-box-cls">0</span>&nbsp;</span></p></div><p style="margin: 17px 0;text-align: justify;line-height: 30px;break-after: avoid;font-size: 18px;font-family: SimHei, sans-serif;white-space: normal"><span style="font-size: 18px;"><strong>四、响应文件提交</strong></span></p><div style="font-family:FangSong; font-size:18px; line-height:20px;"><p>&nbsp; &nbsp; 截止时间：<span class="bookmark-item uuid-1595988880414 code-24011 addWord date-time-selection-cls">2021年12月31日 09:30</span>（北京时间）</p><p>&nbsp; &nbsp; 地点（网址）：<span class="bookmark-item uuid-1595988897695 code-24012 editDisable single-line-text-input-box-cls readonly">本项目通过“政府采购云平台（www.zcygov.cn）”实行在线竞标响应（电子投标），供应商应当在上传响应文件截止时间前，将生成的“电子加密响应文件”上传提交至“政府采购云平台”。通过在线解密开启响应文件（本项目不要求供应商到达截标现场，但供应商应准时在线出席电子开评标会议，随时关注开评标进度，如在开评标过程中有电子询标，应在规定的时间内对电子询标函进行澄清回复。）</span>&nbsp;</p></div><p style="margin: 17px 0;text-align: justify;line-height: 30px;break-after: avoid;font-size: 18px;font-family: SimHei, sans-serif;white-space: normal"><span style="font-size: 18px;"><strong>五、响应文件开启</strong></span>&nbsp;</p><div style="font-size:18px; font-family:FangSong; line-height:20px;"><p>&nbsp; &nbsp; 开启时间：<span class="bookmark-item uuid-1595988911012 code-24011 addWord date-time-selection-cls">2021年12月31日 09:30</span>（北京时间）</p><p>&nbsp; &nbsp; 地点：<span class="bookmark-item uuid-1595988922137 code-24015 editDisable single-line-text-input-box-cls readonly">政府采购云平台（www.zcygov.cn）</span>&nbsp;</p></div><p style="margin: 17px 0;text-align: justify;line-height: 30px;break-after: avoid;font-size: 21px;font-family: SimHei, sans-serif;white-space: normal"><span style="font-size: 18px;line-height:20px;"><strong>六、公告期限</strong></span>&nbsp;</p><p><span style="font-size: 18px; font-family:FangSong;">&nbsp; &nbsp; 自本公告发布之日起3个工作日。</span></p><p style="margin: 17px 0;text-align: justify;line-height: 30px;break-after: avoid;font-size: 18px;font-family: SimHei, sans-serif;white-space: normal"><span style="font-size: 18px;"><strong>七、其他补充事宜</strong></span>&nbsp;</p><p style="line-height: 1.5em;"><span style="font-size: 18px;font-family:FangSong;line-height:20px;">&nbsp; &nbsp;<span class="bookmark-item uuid-1589194982864 code-31006 addWord multi-line-text-input-box-cls">1、本次公告在中国政府采购网、广西壮族自治区政府采购网、梧州市政府采购网、广西中意招标造价咨询有限公司网发布。<br/>2、（1）本项目实行电子投标，供应商应按照本项目谈判文件和政采云平台的要求编制、加密并提交响应文件。供应商在使用系统参与投标过程中遇到涉及平台使用的任何问题，可致电政采云平台技术支持热线咨询，联系方式：400-881-7190。（2）供应商应及时熟悉掌握电子标系统操作指南（见政采云电子卖场首页右上角—服务中心—帮助文档—项目采购）：https://service.zcygov.cn/#/knowledges/tree?tag=AG1DtGwBFdiHxlNdhY0r。（3）供应商应及时完成CA申领和绑定（见广西壮族自治区政府采购网—办事服务—下载专区-政采云CA证书办理操作指南）（4）供应商通过政采云投标客户端软件制作响应文件，政采云投标客户端软件由供应商自行前往下载并安装（见广西壮族自治区政府采购网—办事服务—下载专区-广西壮族自治区全流程电子招投标项目管理系统--供应商客户端）。（5）因未注册入库、未办理CA数字证书、CA证书故障、操作不当等原因造成无法参与或投标失败等后果由供应商自行承担。（6）响应文件递交截止时间后，政采云（电子标系统）自动提取所有响应文件，各供应商须在开启程序开始后30分钟内对上传政采云的响应文件进行解密，所有供应商在规定的解密时限内解密完成或解密时限结束后，本代理机构开启响应文件；供应商超过时间未解密视为响应无效。</span>&nbsp;</span><span style="font-size: 18px;font-family:FangSong;line-height:20px;">&nbsp;</span></p><p style="margin: 17px 0;text-align: justify;line-height: 32px;break-after: avoid;font-size: 21px;font-family: SimHei, sans-serif;white-space: normal"><span style="font-size: 18px;"><strong>八、凡对本次招标提出询问，请按以下方式联系</strong></span></p><div style="font-family:FangSong;line-height:30px;"><div style="font-family:FangSong;line-height:30px;"><p style="line-height: normal;"><span style="font-size: 18px;">&nbsp; &nbsp; 1.采购人信息</span>&nbsp;</p><p style="line-height: normal;"><span style="font-size: 18px;">&nbsp; &nbsp; 名&nbsp;&nbsp;&nbsp; 称：<span class="bookmark-item uuid-1596004663203 code-00014 editDisable interval-text-box-cls readonly">梧州市工人医院</span>&nbsp;</span></p><p style="line-height: normal;"><span style="font-size: 18px;">&nbsp; &nbsp; 地&nbsp;&nbsp;&nbsp; 址：<span class="bookmark-item uuid-1596004672274 code-00018 addWord single-line-text-input-box-cls">梧州市高地路南三巷一号</span>&nbsp;</span></p><p style="line-height: normal;"><span style="font-size: 18px;">&nbsp; &nbsp; 项目联系人：<span class="bookmark-item uuid-1596004688403 code-00015 editDisable single-line-text-input-box-cls readonly">朱先生</span>&nbsp;</span></p><p style="line-height: normal;"><span style="font-size: 18px;">&nbsp; &nbsp; 项目联系方式：<span class="bookmark-item uuid-1596004695990 code-00016 editDisable single-line-text-input-box-cls readonly">0774－2024689</span>&nbsp;</span></p><p style="line-height: normal;"><span style="font-size: 18px;">&nbsp; &nbsp; 2.采购代理机构信息</span></p><p style="line-height: normal;"><span style="font-size: 18px;">&nbsp; &nbsp; 名&nbsp;&nbsp;&nbsp; 称：<span class="bookmark-item uuid-1596004721081 code-00009 addWord interval-text-box-cls">广西中意招标造价咨询有限公司</span>&nbsp;</span></p><p style="line-height: normal;"><span style="font-size: 18px;">&nbsp; &nbsp; 地&nbsp;&nbsp;&nbsp; 址：<span class="bookmark-item uuid-1596004728442 code-00013 editDisable single-line-text-input-box-cls readonly">梧州市长洲区新兴三路30号神冠豪都B栋2单元34层</span>&nbsp;</span></p><p style="line-height: normal;"><span style="font-size: 18px;">&nbsp; &nbsp; 项目联系人（询问）：<span class="bookmark-item uuid-1596004745033 code-00010 editDisable single-line-text-input-box-cls readonly">焦先生</span>&nbsp;</span></p><p style="line-height: normal;"><span style="font-size: 18px;">&nbsp; &nbsp; 项目联系方式（询问）：<span class="bookmark-item uuid-1596004753055 code-00011 addWord single-line-text-input-box-cls">0774-2828000</span>&nbsp;</span></p></div></div><p><br/></p><p><br/></p><p><br/></p><p><br/></p><p><br/></p><p><br/></p>'

    print(json.dumps(parse_html(content), indent=4, ensure_ascii=False))
