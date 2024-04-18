import json
import logging
from typing import Union

from collect.collect.core.error import SwitchError
from collect.collect.core.parse import common, AbstractFormatParser
from collect.collect.core.parse.errorhandle import raise_error
from collect.collect.middlewares import ParseError
from collect.collect.utils import symbol_tools as sym, debug_stats as stats
from constant import constants

logger = logging.getLogger(__name__)


class StandardFormatParser(AbstractFormatParser):
    """
    标准格式文件的解析
    """

    @staticmethod
    @stats.function_stats(logger)
    def parse_project_base_situation(part: list[str]) -> dict:
        """
        解析 项目基本情况
        :param part:
        :return:
        """

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

        # print(part)

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
                bid_item = common.get_template_bid_item(
                    is_win=False, index=bid_item_index
                )
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
                bid_item_index += 1
                bid_items.append(complete_purchase_bid_item(bid_item))
            else:
                idx += 1
        data[constants.KEY_PROJECT_BID_ITEMS] = bid_items

        return data

    @staticmethod
    @stats.function_stats(logger)
    def parse_project_contact(part: list[str]) -> dict:
        return common.parse_contact_info(part)


def check_useful_part(title: str) -> Union[int, None]:
    """
    检查是否包含有用信息的标题
    :param title:
    :return:
    """
    if "项目基本情况" in title:
        return constants.KEY_PART_PROJECT_SITUATION
    return None


@stats.function_stats(logger)
def parse_html(html_content: str):
    """
    解析 采购公告 的详情信息
    :param html_content:
    :return:
    """
    result = common.parse_html(html_content=html_content)
    parts = dict[int, list[str]]()
    n, idx, chinese_idx = len(result), 0, 0
    # 将 result 划分为 若干个部分
    try:
        while idx < n:
            # 找以 “一、” 这种格式开头的字符串
            index = common.startswith_chinese_number(result[idx])
            if index > chinese_idx:
                key_part = check_useful_part(title=result[idx])
                if key_part:
                    chinese_idx = index
                    # 开始部分（不算入标题）
                    idx += 1
                    # 从后面开始找
                    r_idx = n - 1
                    # 找与 index 差1序号的标题
                    while (
                        r_idx > idx
                        and common.startswith_chinese_number(result[r_idx]) != index + 1
                    ):
                        r_idx -= 1
                    # 将该部分加入
                    parts[key_part] = result[idx:r_idx]
                    idx = r_idx
                else:
                    idx += 1
            else:
                idx += 1
    except BaseException as e:
        raise_error(error=e, msg="解析 parts 出现未完善情况", content=result)

    parts_length = len(parts)
    try:
        if parts_length >= 1:
            res = _parse(parts)

            # 没有标项信息则切换
            if len(res.get(constants.KEY_PROJECT_BID_ITEMS, [])) == 0:
                raise SwitchError("该采购公告没有标项信息")

            return res
        else:
            raise ParseError(
                msg="解析 parts 出现不足情况",
                content=result,
            )
    except SwitchError as e:
        raise e
    except BaseException as e:
        raise_error(
            error=e,
            msg="解析 __parse_standard_format 失败",
            content=["\n".join(v) for _, v in parts],
        )


@stats.function_stats(logger)
def _parse(parts: dict[int, list[str]]):
    """
    解析 parts 部分
    :param parts:
    :return:
    """

    data = dict()
    # 项目基本情况
    if constants.KEY_PART_PROJECT_SITUATION in parts:
        data.update(
            StandardFormatParser.parse_project_base_situation(
                parts[constants.KEY_PART_PROJECT_SITUATION]
            )
        )

    return data


if __name__ == "__main__":
    content = '<style id="fixTableStyle" type="text/css">th,td {border:1px solid #DDD;padding: 5px 10px;}</style><div><div style="border:2px solid"><div style="font-family:FangSong;"><p><span style="font-size: 18px;">&nbsp; &nbsp; 项目概况</span> &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;</p><p><span style="font-size: 18px; line-height:30px; ">&nbsp; &nbsp; <span class="bookmark-item uuid-1596015933656 code-00003 addWord single-line-text-input-box-cls">医疗设备采购</span></span><span style="font-size: 18px;">招标项目的潜在投标人应在</span><span style="font-size: 18px; text-decoration: none;"><span class="bookmark-item uuid-1594623824358 code-23007 addWord single-line-text-input-box-cls readonly">广西南宁市民族大道141号中鼎万象东方D区五层广西科文招标有限公司财务部</span></span><span style="font-size: 18px;">获取招标文件，并于&nbsp;<span class="bookmark-item uuid-1595940588841 code-23011 addWord date-time-selection-cls">2021年12月27日 09:00</span></span><span style="font-size: 18px;">（北京时间）前递交投标文件。</span>&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;&nbsp;</p></div></div><p style="margin: 17px 0;text-align: justify;line-height: 20px;break-after: avoid;font-size: 18px;font-family: SimHei, sans-serif;white-space: normal"><span style="font-size: 18px;"><strong>一、项目基本情况</strong></span> &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;</p><div style="font-family:FangSong;line-height:20px;"><p><span style="font-size: 18px;">&nbsp; &nbsp; 项目编号：<span class="bookmark-item uuid-1595940643756 code-00004 addWord single-line-text-input-box-cls">GXZC2021-G1-004895-KWZB</span>&nbsp;</span></p><p><span style="font-size: 18px;">&nbsp; &nbsp; 项目名称：<span class="bookmark-item uuid-1596015939851 code-00003 addWord single-line-text-input-box-cls">医疗设备采购</span></span></p><p><span style="font-size: 18px;">&nbsp; &nbsp; 预算总金额（元）：<span class="bookmark-item uuid-1595940673658 code-AM01400034 addWord numeric-input-box-cls">7550000</span>&nbsp;</span>&nbsp;</p><p style="text-indent: 0px; "><span style="font-size: 18px; text-indent: 2em;">&nbsp; &nbsp; 采购需求：</span></p><div style="font-family: FangSong; white-space: normal; line-height: 20px;"><p><span style="font-size: 18px;"></span></p><div><div class="template-bookmark uuid-1593419700012 code-AM014230011 text-招标项目概况 object-panel-cls" style="padding: 10px"><p style="line-height: normal;"><span style="display: inline-block;"><span class="bookmark-item uuid-1595941042480 code-AM014sectionNo editDisable single-line-text-input-box-cls">标项一</span></span><br/>标项名称:<span class="bookmark-item uuid-1593432150293 code-AM014bidItemName editDisable single-line-text-input-box-cls">广西壮族自治区胸科医院体外膜肺氧合系统(ECMO)</span><br/>数量:<span class="bookmark-item uuid-1595941076685 code-AM014bidItemCount editDisable single-line-text-input-box-cls">2</span><br/>预��金额（元）:<span class="bookmark-item uuid-1593421137256 code-AM014budgetPrice editDisable single-line-text-input-box-cls">4000000</span><br/>简要规格描述或项目基本概况介绍、用途：<span class="bookmark-item uuid-1593421202487 code-AM014briefSpecificationDesc editDisable single-line-text-input-box-cls">一、技术参数<br/>1、离心泵系统<br/>1.1、外置离心泵驱动器，液压调控，可灵活调节；<br/>1.2、离心泵驱动器需有流量监测、气泡监测模块；<br/>……<br/></span></p><p style="line-height: normal;">最高限价（如有）：<samp class="bookmark-item uuid-1598878264729 code-AM014priceCeilingY editDisable single-line-text-input-box-cls" style="font-family: inherit;">/</samp></p><p style="line-height: normal;">合同履约期限：<samp class="bookmark-item uuid-1598878268033 code-AM014ContractPerformancePeriodY editDisable single-line-text-input-box-cls" style="font-family: inherit;">自签订合同之日起国产设备30天/进口设备90天内交货并安装调试完毕。</samp></p><p style="line-height: normal;">本标项（<samp class="bookmark-item uuid-1598878270792 code-AM014allowJointVenture2Bid editDisable single-line-text-input-box-cls" style="font-family: inherit;">否</samp>）接受联合体投标<br/>备注：<span class="bookmark-item uuid-1593432166973 code-AM014remarks editDisable "></span></p></div><div class="template-bookmark uuid-1593419700012 code-AM014230011 text-招标项目概况 object-panel-cls" style="padding: 10px"><p style="line-height: normal;"><span style="display: inline-block;"><span class="bookmark-item uuid-1595941042480 code-AM014sectionNo editDisable single-line-text-input-box-cls">标项二</span></span><br/>标项名称:<span class="bookmark-item uuid-1593432150293 code-AM014bidItemName editDisable single-line-text-input-box-cls">广西壮族自治区胸科医院彩色多普勒超声诊断系统</span><br/>数量:<span class="bookmark-item uuid-1595941076685 code-AM014bidItemCount editDisable single-line-text-input-box-cls">1</span><br/>预算金额（元）:<span class="bookmark-item uuid-1593421137256 code-AM014budgetPrice editDisable single-line-text-input-box-cls">3550000</span><br/>简要规格描述或项目基本概况介绍、用途：<span class="bookmark-item uuid-1593421202487 code-AM014briefSpecificationDesc editDisable single-line-text-input-box-cls">一、主要技术规格及系统概述<br/>1、主机成像系统<br/>1.1、高分辨率液晶显示器≥21.5英寸，分辨率1920×1080,无闪烁，不间断逐行扫描，可上下左右任意旋转，可前后折叠；<br/>……<br/></span></p><p style="line-height: normal;">最高限价（如有）：<samp class="bookmark-item uuid-1598878264729 code-AM014priceCeilingY editDisable single-line-text-input-box-cls" style="font-family: inherit;">/</samp></p><p style="line-height: normal;">合同履约期限：<samp class="bookmark-item uuid-1598878268033 code-AM014ContractPerformancePeriodY editDisable single-line-text-input-box-cls" style="font-family: inherit;">自签订合同之日起国产设备30天/进口设备90天内交货并安装调试完毕。</samp></p><p style="line-height: normal;">本标项（<samp class="bookmark-item uuid-1598878270792 code-AM014allowJointVenture2Bid editDisable single-line-text-input-box-cls" style="font-family: inherit;">否</samp>）接受联合体投标<br/>备注：<span class="bookmark-item uuid-1593432166973 code-AM014remarks editDisable "></span></p></div></div></div><p><br/></p><p><strong style="font-size: 18px; font-family: SimHei, sans-serif; text-align: justify;">二、申请人的资格要求：</strong><br/></p></div><div style="font-family:FangSong;line-height:20px;"><p><span style="font-size: 18px;">&nbsp; &nbsp; 1.满足《中华人民共和国政府采购法》第二十二条规定；</span></p><p><span style="font-size: 18px;">&nbsp; &nbsp; 2.落实政府采购政策需满足的资格要求：<span class="bookmark-item uuid-1595940687802 code-23021 editDisable multi-line-text-input-box-cls readonly">无</span>&nbsp;</span></p><p><span style="font-size: 18px;">&nbsp; &nbsp; 3.本项目的特定资格要求：<span class="bookmark-item uuid-1596277470067 code-23002 editDisable multi-line-text-input-box-cls readonly">分标1、2：投标人须具有国家主管部门颁发的有效的医疗器械生产许可证，或按《医疗器械经营监督管理办法》（国家食品药品监督管理总局第8号令）医疗器械分类管理要求具有有效的医疗器械经营备案凭证或许可证。</span>&nbsp;</span></p></div><p style="margin: 17px 0;text-align: justify;line-height: 20px;break-after: avoid;font-size: 18px;font-family: SimHei, sans-serif;white-space: normal"><span style="font-size: 18px;"><strong>三、获取招标文件</strong></span>&nbsp;</p><div style="font-family:FangSong;line-height:20px;"><p style="line-height:20px;"><span style="font-size: 18px;">&nbsp; &nbsp; </span><span style="font-size: 18px; text-decoration: none;line-height:20px;">时间：<span class="bookmark-item uuid-1587980024345 code-23003 addWord date-selection-cls">2021年12月06日</span>至<span class="bookmark-item uuid-1588129524349 code-23004 addWord date-selection-cls readonly">2021年12月13日</span>&nbsp;，每天上午<span class="bookmark-item uuid-1594624027756 code-23005 addWord morning-time-section-selection-cls">08:00至12:00</span>&nbsp;，下午<span class="bookmark-item uuid-1594624265677 code-23006 addWord afternoon-time-section-selection-cls">15:00至18:00</span>（北京时间，法定节假日除外）</span></p><p><span style="font-size: 18px;">&nbsp; &nbsp; 地点（网址）：<span class="bookmark-item uuid-1588129635457 code-23007 addWord single-line-text-input-box-cls readonly">广西南宁市民族大道141号中鼎万象东方D区五层广西科文招标有限公司财务部</span>&nbsp;</span></p><p><span style="font-size: 18px;">&nbsp; &nbsp; 方式：<span class="bookmark-item uuid-1595940713919 code-AM01400046 editDisable single-line-text-input-box-cls readonly">方式：现场购买或邮寄；<br/>售价：每套250元，售后不退（付款方式只接受现金或转账付款，不接受微信、支付宝和银行卡刷卡支付）。<br/></span>&nbsp;</span></p><p><span style="font-size: 18px;">&nbsp; &nbsp; 售价（元）：<span class="bookmark-item uuid-1595940727161 code-23008 addWord numeric-input-box-cls">250</span></span>&nbsp;</p></div><p style="margin: 17px 0;text-align: justify;line-height: 20px;break-after: avoid;font-size: 18px;font-family: SimHei, sans-serif;white-space: normal"><span style="font-size: 18px;line-height:20px;"><strong>四、提交投标文件截止时间、开标时间和地点</strong></span></p><div style="font-family:FangSong;line-height:20px;"><p><span style="font-size: 18px;">&nbsp; &nbsp;</span><span style="font-size: 18px; text-decoration: none;"> 提交投标文件截止时间：<span class="bookmark-item uuid-1595940760210 code-23011 addWord date-time-selection-cls">2021年12月27日 09:00</span>（北京时间）</span></p><p><span style="font-size: 18px;">&nbsp; &nbsp;</span><span style="font-size: 18px; text-decoration: none;"> 投标地点（网址）：<span style="text-decoration: none; font-size: 18px;"><span class="bookmark-item uuid-1594624424199 code-23012 addWord single-line-text-input-box-cls readonly">广西南宁市民族大道141号中鼎万象东方D区五层广西科文招标有限公司开标厅。</span></span></span>&nbsp;</p><p><span style="font-size: 18px; text-decoration: none;">&nbsp; &nbsp; 开标时间：<span style="text-decoration: none; font-size: 18px;"><span class="bookmark-item uuid-1594624443488 code-23013 addWord date-time-selection-cls readonly">2021年12月27日 09:00</span></span></span>&nbsp;</p><p><span style="font-size: 18px; text-decoration: none;">&nbsp; &nbsp; 开标地点：<span style="text-decoration: none; font-size: 18px;"><span class="bookmark-item uuid-1588129973591 code-23015 addWord single-line-text-input-box-cls readonly">广西南宁市民族大道141号中鼎万象东方D区五层广西科文招标有限公司开标厅。</span></span></span>&nbsp;&nbsp;</p></div><p style="margin: 17px 0;text-align: justify;line-height: 20px;break-after: avoid;font-size: 21px;font-family: SimHei, sans-serif;white-space: normal"><span style="font-size: 18px;line-height:20px;"><strong>五、公告期限</strong></span>&nbsp;</p><p><span style="font-size: 18px; font-family:FangSong;">&nbsp; &nbsp; 自本公告发布之日起5个工作日。</span></p><p style="margin: 17px 0;text-align: justify;line-height: 20px;break-after: avoid;font-size: 18px;font-family: SimHei, sans-serif;white-space: normal"><span style="font-size: 18px;"><strong>六、其他补充事宜</strong></span></p><p style="line-height: 1.5em;"><span style="font-size: 18px;font-family:FangSong;line-height:20px;">&nbsp; &nbsp;<span class="bookmark-item uuid-1589194982864 code-31006 addWord multi-line-text-input-box-cls">1、单位负责人为同一人或者存在直接控股、管理关系的不同供应商，不得参加同一合同项下的政府采购活动。为本项目提供过整体设计、规范编制或者项目管理、监理、检测等服务的供应商，不得再参加本项目上述服务以外的其他采购活动；<br/>2、对在“信用中国”网站(www.creditchina.gov.cn)、中国政府采购网(www.ccgp.gov.cn)等管道被列入失信被执行人、重大税收违法案件当事人名单、政府采购严重违法失信行为记录名单及其他不符合《中华人民共和国政府采购法》第二十二条规定条件的供应商，不得参与政府采购活动。<br/>3、本项目不接受未购买本招标文件的投标人投标。<br/>4、为避免供应商不良诚信记录的发生，及配合采购单位政府采购项目执行和备案，未在政采云注册的供应商可在获取采购文件后登录政采云进行注册，如在操作过程中遇到问题或者需要技术支持，请致电政采云客服热线：400-881-7190。<br/>5、依据《国家税务总局关于增值税发票开具有关问题的公告》国家税务总局公告2019年第16号的规定，供应商在索取发票时，请提供纳税人识别号或统一社会信用代码。<br/>6、如需邮寄另加邮费50元，请用电汇或转账方式将300元汇入科文公司以下账户，办理汇款后请将详细的收件人、邮寄地址、邮编、联系电话、传真号码或邮箱、分标号、纳税人识别号等传真到0771-2023829后联系财务负责人，财务联系人：丁华宁，联系方式：0771-2023962。如未能提供联系方式造成招标文件无法邮寄或有更改及补充通知无法联系的，后果由投标人自负。<br/>7、投标保证金账户：<br/>开户名称：广西科文招标有限公司，开户银行：广西北部湾银行营业部，银行账号：0101012090615689<br/>标书及服务费账户：<br/>开户名称：广西科文招标有限公司南宁咨询三分公司，开户银行：广西北部湾银行股份有限公司南宁市云景支行，银行账号：805030313600001<br/>8、本项目需要落实的政府采购政策：（1）政府采购促进中小企业发展；（2）政府采购支持采用本国产品的政策；（3）强制采购节能产品；优先采购节能产品、环境标志产品；（4）政府采购促进残疾人就业政策；（5）政府采购支持监狱企业发展。<br/>9、公告发布媒体：www.ccgp.gov.cn（中国政府采购网）、http://zfcg.gxzf.gov.cn (广西政府采购网)</span>&nbsp;</span><span style="font-size: 18px;font-family:FangSong;line-height:20px;">&nbsp;</span></p><p style="margin: 17px 0;text-align: justify;line-height: 32px;break-after: avoid;font-size: 21px;font-family: SimHei, sans-serif;white-space: normal"><span style="font-size: 18px;"><strong>七、对本次采购提出询问，请按以下方式联系</strong></span></p><div style="font-family:FangSong;line-height:20px;"><p><span style="font-size: 18px;">&nbsp; &nbsp; 1.采购人信息</span></p><p><span style="font-size: 18px;">&nbsp; &nbsp; 名&nbsp;&nbsp;&nbsp; 称：<span class="bookmark-item uuid-1596004663203 code-00014 editDisable interval-text-box-cls readonly">广西壮族自治区胸科医院</span>&nbsp;</span></p><p><span style="font-size: 18px;">&nbsp; &nbsp; 地&nbsp;&nbsp;&nbsp; 址：<span class="bookmark-item uuid-1596004672274 code-00018 addWord single-line-text-input-box-cls">柳州市羊角山路8号</span>&nbsp;</span></p><p><span style="font-size: 18px;">&nbsp; &nbsp; 项目联系人：<span class="bookmark-item uuid-1596004688403 code-00015 editDisable single-line-text-input-box-cls readonly">覃鲁财</span>&nbsp;</span>&nbsp;</p><p><span style="font-size: 18px;">&nbsp; &nbsp; 项目联系方式：<span class="bookmark-item uuid-1596004695990 code-00016 editDisable single-line-text-input-box-cls readonly">0772-3130415</span>&nbsp;</span></p><p><span style="font-size: 18px;">&nbsp; &nbsp; <br/>&nbsp; &nbsp; 2.采购代理机构信息</span> &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;</p><p><span style="font-size: 18px;">&nbsp; &nbsp; 名&nbsp;&nbsp;&nbsp; 称：<span class="bookmark-item uuid-1596004721081 code-00009 addWord interval-text-box-cls">广西科文招标有限公司</span>&nbsp;</span> &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;</p><p><span style="font-size: 18px;">&nbsp; &nbsp; 地&nbsp;&nbsp;&nbsp; 址：<span class="bookmark-item uuid-1596004728442 code-00013 editDisable single-line-text-input-box-cls readonly">南宁市民族大道路141号中鼎万象东方大厦D区五层</span>&nbsp;</span>&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;</p><p><span style="font-size: 18px;">&nbsp; &nbsp; 项目联系人：<span class="bookmark-item uuid-1596004745033 code-00010 editDisable single-line-text-input-box-cls readonly">黄敏、钟文</span>&nbsp;&nbsp;</span> &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;</p><p><span style="font-size: 18px;">&nbsp; &nbsp; 项目联系方式：<span class="bookmark-item uuid-1596004753055 code-00011 addWord single-line-text-input-box-cls">0771-2023837、0771-2023853</span>&nbsp;<br/></span></p></div></div><p><br/></p><p><br/></p><p><br/></p><p><br/></p><p><br/></p><p><br/></p><p><br/></p>'

    print(json.dumps(parse_html(content), indent=4, ensure_ascii=False))
