import json
import logging
import re
from typing import Union

from collect.collect.core.error import SwitchError
from collect.collect.core.parse import common, AbstractFormatParser
from collect.collect.core.parse.errorhandle import raise_error
from collect.collect.middlewares import ParseError
from constants import ProjectKey, BidItemKey, PartKey, CollectDevKey
from utils import debug_stats as stats, symbol_tools, calculate

logger = logging.getLogger(__name__)


class StandardFormatParser(AbstractFormatParser):
    """
    标准格式文件的解析
    """

    PATTERN_PROJECT_INFO_PROJECT_CODE = re.compile(
        r"项目编号[:：](\S+)(?:\d\.)?项目?名称"
    )

    # 解析基本情况的正则表达式
    PATTERN_PROJECT_INFO_PROJECT_NAME = re.compile(
        r"项目?名称[:：](\S+?)(?:\d\.)?(?:采购方式[:：]\S+|预算)"
    )
    # 解析基本情况的正则表达式
    PATTERN_PROJECT_INFO_BUDGET = re.compile(
        r"(?:预算总?金额|招标控制价)\S*?[:：]\D*?(\d+(?:\.\d*)?)(\S*?元|)"
    )

    # 解析标项信息的正则表达式
    PATTERN_BIDDING = re.compile(
        r"(?:标项(\S{1,2}))?标项名称[:：](\S+?)(?:数量[:：]\S+?)?预算金额\S*?[:：](\d+(?:\.\d*)?)(?:数量[:：])?"
    )

    @staticmethod
    @stats.function_stats(logger)
    def parse_project_base_situation(string: str) -> dict:
        """
        解析 项目基本情况
        :param string:
        :return:
        """
        # 去掉空白字符，避免正则匹配失败
        string = symbol_tools.remove_all_spaces(string)

        # 分离为两部分，一部分是前面的基本信息，另一部分是后面的标项信息
        split_idx = string.find("采购需求：")
        if split_idx == -1:
            split_idx = string.find("采购需求:")
        if split_idx == -1:
            split_idx = string.find("采购需求")

        # 如果没有这部分，那么就可能没有对应的数据
        if split_idx == -1:
            contains_suffix = False
            prefix, suffix = string[:split_idx], ""
        else:
            contains_suffix = True
            prefix, suffix = string[:split_idx], string[split_idx:]

        data = dict()
        bidding_items = []
        data[ProjectKey.BID_ITEMS] = bidding_items

        if match := StandardFormatParser.PATTERN_PROJECT_INFO_PROJECT_CODE.search(
            prefix
        ):
            data[ProjectKey.CODE] = match.group(1)
        else:
            data[ProjectKey.CODE] = None

        # 正则表达式匹配基本信息
        if match := StandardFormatParser.PATTERN_PROJECT_INFO_PROJECT_NAME.search(
            prefix
        ):
            # 项目名称
            data[ProjectKey.NAME] = match.group(1)
        else:
            data[ProjectKey.NAME] = None

        if match := StandardFormatParser.PATTERN_PROJECT_INFO_BUDGET.search(prefix):
            # 总预算
            total_budget = float(match.group(1))
            # 单位
            unit = match.group(2)
            # 将单位固定为 元
            total_budget *= calculate.parse_unit(unit)
            data[ProjectKey.TOTAL_BUDGET] = total_budget
            contains_budget = True
        else:
            contains_budget = False
            # 如果不存在总预算，那么这里需要设置为 0
            total_budget = 0

        # 不包含采购需求
        if not contains_suffix:
            data[CollectDevKey.PURCHASE_SPECIAL_FORMAT_1] = True
            data[ProjectKey.TOTAL_BUDGET] = total_budget
            return data

        # 解析标项信息
        if match := StandardFormatParser.PATTERN_BIDDING.findall(suffix):
            if len(match) == 0:
                raise ParseError(msg="基本情况解析失败：无标项信息", content=[string])
            # 标项编号
            item_index = 1

            for m in match:
                index, name, budget = m

                if index is None or name is None or budget is None:
                    raise ParseError(msg="标项解析失败", content=[string])

                # 空串
                if not index:
                    index = item_index
                else:
                    # 阿拉伯数字
                    if index.isdigit():
                        index = int(index)
                    else:
                        # 中文数字
                        index = common.translate_zh_to_number(index)
                item = common.get_template_bid_item(
                    is_win=False, index=index, name=name
                )
                budget = float(budget)
                item[BidItemKey.BUDGET] = budget
                bidding_items.append(item)

                item_index += 1
                if contains_budget:
                    total_budget -= budget
                else:
                    total_budget += budget

            if contains_budget and total_budget > 1e-5:
                raise ParseError(
                    msg="标项预算合计与总预算不符",
                    content=bidding_items + [(f"total_budget: {total_budget}")],
                )
            if not contains_budget:
                data[ProjectKey.TOTAL_BUDGET] = total_budget

        else:
            # 存在特殊情况：7iWKD4Bl0oC8XVdxmCJSQg== 如该公告所示，其标项格式与上面正常采购不同
            data[CollectDevKey.PURCHASE_SPECIAL_FORMAT_1] = True

        return data

    @staticmethod
    @stats.function_stats(logger)
    def parse_project_contact(part: list[str]) -> dict:
        return common.parse_contact_info("".join(part))


def check_useful_part(_: bool, title: str) -> Union[int, None]:
    """
    检查是否包含有用信息的标题
    :param _: (无用，为了统一接口）
    :param title:
    :return:
    """
    if "项目基本情况" in title:
        return PartKey.PROJECT_SITUATION
    return None


@stats.function_stats(logger)
def parse_html(html_content: str):
    """
    解析 采购公告 的详情信息
    :param html_content:
    :return:
    """
    result = common.parse_html(html_content=html_content)

    parts: Union[dict[int, list[str]], None] = {}

    # 将 result 划分为 若干个部分
    # try:
    #     parts = common.split_content_by_titles(
    #         result=result, is_win_bid=False, check_title=check_useful_part, rfind=True
    #     )
    #     # print(json.dumps(parts, ensure_ascii=False, indent=4))
    # except BaseException as e:
    #     raise_error(error=e, msg="解析 parts 出现未完善情况", content=result)

    parts[PartKey.PROJECT_SITUATION] = result

    parts_length = len(parts)
    try:
        if parts_length >= 1:
            res = _parse(parts)

            # 除了特殊格式外
            if not res.get(CollectDevKey.PURCHASE_SPECIAL_FORMAT_1, False):
                # 没有标项信息则切换
                if len(res.get(ProjectKey.BID_ITEMS, [])) == 0:
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
            content=["\n".join(v) for _, v in parts.items()],
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
    if PartKey.PROJECT_SITUATION in parts:
        data.update(
            StandardFormatParser.parse_project_base_situation(
                "".join(parts[PartKey.PROJECT_SITUATION])
            )
        )

    return data


if __name__ == "__main__":
    content = '<style id="fixTableStyle" type="text/css">th,td {border:1px solid #DDD;padding: 5px 10px;}</style>\n<div id="fixTableStyle" type="text/css" cdata_tag="style" cdata_data="th,td {border:1px solid #DDD;padding: 5px 10px;}" _ue_custom_node_="true"></div><div><div style="border:2px solid"><div style="font-family:FangSong;"><p><span style="font-size: 18px;">&nbsp; &nbsp; 项目概况</span> &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;</p><p><span style="font-size: 18px; line-height:30px; ">&nbsp; &nbsp; <span class="bookmark-item uuid-1596015933656 code-00003 addWord single-line-text-input-box-cls">凌云县妇幼保健院整体搬迁项目医疗设备和办公设备采购</span></span><span style="font-size: 18px;">招标项目的潜在投标人应在</span><span style="font-size: 18px; text-decoration: none;"><span class="bookmark-item uuid-1594623824358 code-23007 addWord single-line-text-input-box-cls readonly">“政采云”平台（http：//www.zcygov.cn）</span></span><span style="font-size: 18px;">获取招标文件，并于&nbsp;<span class="bookmark-item uuid-1595940588841 code-23011 addWord date-time-selection-cls">2022年12月19日 09:30</span></span><span style="font-size: 18px;">（北京时间）前递交投标文件。</span>&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;&nbsp;</p></div></div><p style="margin: 17px 0;text-align: justify;line-height: 20px;break-after: avoid;font-size: 18px;font-family: SimHei, sans-serif;white-space: normal"><span style="font-size: 18px;"><strong>一、项目基本情况</strong></span> &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;</p><div style="font-family:FangSong;line-height:20px;"><p><span style="font-size: 18px;">&nbsp; &nbsp; 项目编号：<span class="bookmark-item uuid-1595940643756 code-00004 addWord single-line-text-input-box-cls">BSZC2022-G1-270295-GXYX</span>&nbsp;</span></p><p><span style="font-size: 18px;">&nbsp; &nbsp; 项目名称：<span class="bookmark-item uuid-1596015939851 code-00003 addWord single-line-text-input-box-cls">凌云县妇幼保健院整体搬迁项目医疗设备和办公设备采购</span></span></p><p><span style="font-size: 18px;">&nbsp; &nbsp; 预算总金额（元）：<span class="bookmark-item uuid-1595940673658 code-AM01400034 addWord numeric-input-box-cls">12461000</span>&nbsp;</span>&nbsp;</p><p style="text-indent: 0px; "><span style="font-size: 18px; text-indent: 2em;">&nbsp; &nbsp; 采购需求：</span></p><div style="font-family: FangSong; white-space: normal; line-height: 20px;"><p><span style="font-size: 18px;"></span></p><div><div class="template-bookmark uuid-1593419700012 code-AM014230011 text-招标项目概况 object-panel-cls" style="padding: 10px"><p style="line-height: normal;"><span style="display: inline-block;"><span class="bookmark-item uuid-1595941042480 code-AM014sectionNo editDisable single-line-text-input-box-cls">标项一</span></span><br/>标项名称:<span class="bookmark-item uuid-1593432150293 code-AM014bidItemName editDisable single-line-text-input-box-cls">凌云县妇幼保健院整体搬迁项目医疗设备和办公设备采购1分标</span><br/>数量:<span class="bookmark-item uuid-1595941076685 code-AM014bidItemCount editDisable single-line-text-input-box-cls">不限</span><br/>预算金额（元）:<span class="bookmark-item uuid-1593421137256 code-AM014budgetPrice editDisable single-line-text-input-box-cls">10230000</span><br/>简要规格描述或项目基本概况介绍、用途：<span class="bookmark-item uuid-1593421202487 code-AM014briefSpecificationDesc editDisable single-line-text-input-box-cls">标项名称: 凌云县妇幼保健院整体搬迁项目医疗设备和办公设备采购1分标<br/>数量:1批<br/>预算金额（元）: 10230000.00<br/>简要规格描述或项目基本概况介绍、用途：具体内容详见招标文件；<br/>最高限价：10230000.00元<br/>备注：1分标</span></p><p style="line-height: normal;">最高限价（如有）：<samp class="bookmark-item uuid-1598878264729 code-AM014priceCeilingY editDisable single-line-text-input-box-cls" style="font-family: inherit;">10230000</samp></p><p style="line-height: normal;">合同履约期限：<samp class="bookmark-item uuid-1598878268033 code-AM014ContractPerformancePeriodY editDisable single-line-text-input-box-cls" style="font-family: inherit;">自合同签订之日起设备 30 天内交货并安装调试完毕交付使用。</samp></p><p style="line-height: normal;">本标项（<samp class="bookmark-item uuid-1598878270792 code-AM014allowJointVenture2Bid editDisable single-line-text-input-box-cls" style="font-family: inherit;">是</samp>）接受联合体投标<br/>备注：<span class="bookmark-item uuid-1593432166973 code-AM014remarks editDisable "></span></p></div><div class="template-bookmark uuid-1593419700012 code-AM014230011 text-招标项目概况 object-panel-cls" style="padding: 10px"><p style="line-height: normal;"><span style="display: inline-block;"><span class="bookmark-item uuid-1595941042480 code-AM014sectionNo editDisable single-line-text-input-box-cls">标项二</span></span><br/>标项名称:<span class="bookmark-item uuid-1593432150293 code-AM014bidItemName editDisable single-line-text-input-box-cls">凌云县妇幼保健院整体搬迁项目医疗设备和办公设备采购2分标</span><br/>数量:<span class="bookmark-item uuid-1595941076685 code-AM014bidItemCount editDisable single-line-text-input-box-cls">不限</span><br/>预算金额（元）:<span class="bookmark-item uuid-1593421137256 code-AM014budgetPrice editDisable single-line-text-input-box-cls">2231000</span><br/>简要规格描述或项目基本概况介绍、用途：<span class="bookmark-item uuid-1593421202487 code-AM014briefSpecificationDesc editDisable single-line-text-input-box-cls">标项名称: 凌云县妇幼保健院整体搬迁项目医疗设备和办公设备采购2分标<br/>数量:1批<br/>预算金额（元）:2231000.00<br/>简要规格描述或项目基本概况介绍、用途：具体内容详见招标文件；<br/>最高限价：2231000.00元<br/>备注：2分标</span></p><p style="line-height: normal;">最高限价（如有）：<samp class="bookmark-item uuid-1598878264729 code-AM014priceCeilingY editDisable single-line-text-input-box-cls" style="font-family: inherit;">2231000</samp></p><p style="line-height: normal;">合同履约期限：<samp class="bookmark-item uuid-1598878268033 code-AM014ContractPerformancePeriodY editDisable single-line-text-input-box-cls" style="font-family: inherit;">自合同签订之日起设备 30 天内交货并安装调试完毕交付使用。</samp></p><p style="line-height: normal;">本标项（<samp class="bookmark-item uuid-1598878270792 code-AM014allowJointVenture2Bid editDisable single-line-text-input-box-cls" style="font-family: inherit;">否</samp>）接受联合体投标<br/>备注：<span class="bookmark-item uuid-1593432166973 code-AM014remarks editDisable "></span></p></div></div></div><p><br/></p><p><strong style="font-size: 18px; font-family: SimHei, sans-serif; text-align: justify;">二、申请人的资格要求：</strong><br/></p></div><div style="font-family:FangSong;line-height:20px;"><p><span style="font-size: 18px;">&nbsp; &nbsp; 1.满足《中华人民共和国政府采购法》第二十二条规定；</span></p><p><span style="font-size: 18px;">&nbsp; &nbsp; 2.落实政府采购政策需满足的资格要求：<span class="bookmark-item uuid-1595940687802 code-23021 editDisable multi-line-text-input-box-cls readonly">无</span>&nbsp;</span></p><p><span style="font-size: 18px;">&nbsp; &nbsp; 3.本项目的特定资格要求：<span class="bookmark-item uuid-1596277470067 code-23002 editDisable multi-line-text-input-box-cls readonly"><br/>【分标1】<br/> 国内注册（指按国家有关规定要求注册），具有有效的医疗器械生产许可证或经营许可证或者备案(按《医疗器械监督管理条例》免于经营备案和无需办理医疗器械经营许可或者备案的情形除外)。</span>&nbsp;</span></p></div><p style="margin: 17px 0;text-align: justify;line-height: 20px;break-after: avoid;font-size: 18px;font-family: SimHei, sans-serif;white-space: normal"><span style="font-size: 18px;"><strong>三、获取招标文件</strong></span>&nbsp;</p><div style="font-family:FangSong;line-height:20px;"><p style="line-height:20px;"><span style="font-size: 18px;">&nbsp; &nbsp; </span><span style="font-size: 18px; text-decoration: none;line-height:20px;">时间：<span class="bookmark-item uuid-1587980024345 code-23003 addWord date-selection-cls">2022年11月28日</span>至<span class="bookmark-item uuid-1588129524349 code-23004 addWord date-selection-cls readonly">2022年12月05日</span>&nbsp;，每天上午<span class="bookmark-item uuid-1594624027756 code-23005 addWord morning-time-section-selection-cls">08:00至12:00</span>&nbsp;，下午<span class="bookmark-item uuid-1594624265677 code-23006 addWord afternoon-time-section-selection-cls">15:00至18:00</span>（北京时间，法定节假日除外）</span></p><p><span style="font-size: 18px;">&nbsp; &nbsp; 地点（网址）：<span class="bookmark-item uuid-1588129635457 code-23007 addWord single-line-text-input-box-cls readonly">“政采云”平台（http：//www.zcygov.cn）</span>&nbsp;</span></p><p><span style="font-size: 18px;">&nbsp; &nbsp; 方式：<span class="bookmark-item uuid-1595940713919 code-AM01400046 editDisable single-line-text-input-box-cls readonly">“政采云”平台（http：//www.zcygov.cn）（操作路径：登录“政采云”平台-项目采购-获取采购文件-找到本项目-点击“申请获取采购文件”）自行下载招标文件电子版。</span>&nbsp;</span></p><p><span style="font-size: 18px;">&nbsp; &nbsp; 售价（元）：<span class="bookmark-item uuid-1595940727161 code-23008 addWord numeric-input-box-cls">0</span></span>&nbsp;</p></div><p style="margin: 17px 0;text-align: justify;line-height: 20px;break-after: avoid;font-size: 18px;font-family: SimHei, sans-serif;white-space: normal"><span style="font-size: 18px;line-height:20px;"><strong>四、提交投标文件截止时间、开标时间和地点</strong></span></p><div style="font-family:FangSong;line-height:20px;"><p><span style="font-size: 18px;">&nbsp; &nbsp;</span><span style="font-size: 18px; text-decoration: none;"> 提交投标文件截止时间：<span class="bookmark-item uuid-1595940760210 code-23011 addWord date-time-selection-cls">2022年12月19日 09:30</span>（北京时间）</span></p><p><span style="font-size: 18px;">&nbsp; &nbsp;</span><span style="font-size: 18px; text-decoration: none;"> 投标地点（网址）：<span style="text-decoration: none; font-size: 18px;"><span class="bookmark-item uuid-1594624424199 code-23012 addWord single-line-text-input-box-cls readonly">本项目为百色市全流程电子化项目，通过“政采云”平台（http： //www.zcygov.cn）实行在线电子投标，供应商应先安装“政采云电子交易客户端”（请自行前往“政采云”平台进行下载），并按照本项目招标文件和“政采云”平台的要求编制、加密后在投标截止时间前通过网络上传至“政采云”平台，供应商在“政采云”平台提交电 子版投标文件时，请填写参加远程开标活动经办人联系方式。</span></span></span>&nbsp;</p><p><span style="font-size: 18px; text-decoration: none;">&nbsp; &nbsp; 开标时间：<span style="text-decoration: none; font-size: 18px;"><span class="bookmark-item uuid-1594624443488 code-23013 addWord date-time-selection-cls readonly">2022年12月19日 09:30</span></span></span>&nbsp;</p><p><span style="font-size: 18px; text-decoration: none;">&nbsp; &nbsp; 开标地点：<span style="text-decoration: none; font-size: 18px;"><span class="bookmark-item uuid-1588129973591 code-23015 addWord single-line-text-input-box-cls readonly">“政采云”平台（http：//www.zcygov.cn）</span></span></span>&nbsp;&nbsp;</p></div><p style="margin: 17px 0;text-align: justify;line-height: 20px;break-after: avoid;font-size: 21px;font-family: SimHei, sans-serif;white-space: normal"><span style="font-size: 18px;line-height:20px;"><strong>五、公告期限</strong></span>&nbsp;</p><p><span style="font-size: 18px; font-family:FangSong;">&nbsp; &nbsp; 自本公告发布之日起5个工作日。</span></p><p style="margin: 17px 0;text-align: justify;line-height: 20px;break-after: avoid;font-size: 18px;font-family: SimHei, sans-serif;white-space: normal"><span style="font-size: 18px;"><strong>六、其他补充事宜</strong></span></p><p style="line-height: 1.5em;"><span style="font-size: 18px;font-family:FangSong;line-height:20px;">&nbsp; &nbsp;<span class="bookmark-item uuid-1589194982864 code-31006 addWord multi-line-text-input-box-cls">1.投标保证金：本项目免收投标保证金。<br/>2.网上查询地址<br/>中国政府采购网（www.ccgp.gov.cn）、广西壮族自治区政府采购网（zfcg.gxzf.gov.cn）、全国公共资源交易平台（广西百色）（http://ggzy.jgswj.gxzf.gov.cn/bsggzy）。<br/>3.本项目需要落实的政府采购政策<br/>（1）政府采购促进中小企业发展。<br/>（2）政府采购支持采用本国产品的政策。<br/>（3）强制采购节能产品；优先采购节能产品、环境标志产品。<br/>（4）政府采购促进残疾人就业政策。<br/>（5）政府采购支持监狱企业发展。<br/>4.本项目不专门面向中小企业预留采购份额的情形：预留采购份额无法确保充分供应、充分竞争，或者存在可能影响政府采购目标实现的。</span>&nbsp;</span><span style="font-size: 18px;font-family:FangSong;line-height:20px;">&nbsp;</span></p><p style="margin: 17px 0;text-align: justify;line-height: 32px;break-after: avoid;font-size: 21px;font-family: SimHei, sans-serif;white-space: normal"><span style="font-size: 18px;"><strong>七、对本次采购提出询问，请按以下方式联系</strong></span></p><div style="font-family:FangSong;line-height:20px;"><p><span style="font-size: 18px;">&nbsp; &nbsp; 1.采购人信息</span></p><p><span style="font-size: 18px;">&nbsp; &nbsp; 名&nbsp;&nbsp;&nbsp; 称：<span class="bookmark-item uuid-1596004663203 code-00014 editDisable interval-text-box-cls readonly">凌云县妇幼保健院</span>&nbsp;</span></p><p><span style="font-size: 18px;">&nbsp; &nbsp; 地&nbsp;&nbsp;&nbsp; 址：<span class="bookmark-item uuid-1596004672274 code-00018 addWord single-line-text-input-box-cls">凌云县泗城镇新秀社区西苑小区292号</span>&nbsp;</span></p><p><span style="font-size: 18px;">&nbsp; &nbsp; 项目联系人：<span class="bookmark-item uuid-1596004688403 code-00015 editDisable single-line-text-input-box-cls readonly">冉师至</span>&nbsp;</span>&nbsp;</p><p><span style="font-size: 18px;">&nbsp; &nbsp; 项目联系方式：<span class="bookmark-item uuid-1596004695990 code-00016 editDisable single-line-text-input-box-cls readonly">0776-7617461</span>&nbsp;</span></p><p><span style="font-size: 18px;">&nbsp; &nbsp; <br/>&nbsp; &nbsp; 2.采购代理机构信息</span> &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;</p><p><span style="font-size: 18px;">&nbsp; &nbsp; 名&nbsp;&nbsp;&nbsp; 称：<span class="bookmark-item uuid-1596004721081 code-00009 addWord interval-text-box-cls">广西优信工程建设管理有限公司</span>&nbsp;</span> &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;</p><p><span style="font-size: 18px;">&nbsp; &nbsp; 地&nbsp;&nbsp;&nbsp; 址：<span class="bookmark-item uuid-1596004728442 code-00013 editDisable single-line-text-input-box-cls readonly">百色市右江区龙景街道龙翔路龙景新都三楼</span>&nbsp;</span>&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;</p><p><span style="font-size: 18px;">&nbsp; &nbsp; 项目联系人：<span class="bookmark-item uuid-1596004745033 code-00010 editDisable single-line-text-input-box-cls readonly">陈小秋</span>&nbsp;&nbsp;</span> &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;</p><p><span style="font-size: 18px;">&nbsp; &nbsp; 项目联系方式：<span class="bookmark-item uuid-1596004753055 code-00011 addWord single-line-text-input-box-cls">0776-2801110</span>&nbsp;<br/></span></p></div></div><p><br/></p><p><br/></p><p><br/></p><p><br/></p><p><br/></p><p><br/></p><p><br/></p>'
    print(json.dumps(parse_html(content), indent=4, ensure_ascii=False))
