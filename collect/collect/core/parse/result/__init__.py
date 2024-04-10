import logging
import time

from lxml import etree

from collect.collect.core.parse import common, errorhandle
from collect.collect.core.parse.result import not_win, win
from collect.collect.utils import log
from contant import constants

try:
    from .not_win import parse_not_win_bid
    from .win import parse_win_bid
except ImportError:  # 单个文件DEBUG需要
    from not_win import parse_not_win_bid
    from win import parse_win_bid

__all__ = ["parse_not_win_bid", "parse_win_bid", "SwitchError"]

logger = logging.getLogger(__name__)

try:
    import config.config

    _DEBUG = getattr(config.config.settings, "debug.enable", False)
except ImportError:
    _DEBUG = True

if _DEBUG:
    if len(logging.root.handlers) == 0:
        logging.basicConfig(level=logging.DEBUG)


def parse_response_data(data: list):
    """
    解析列表api响应中的内容
    :param data:
    :return:
    """
    start_time = time.time()
    if _DEBUG:
        logger.debug(f"DEBUG INFO: {log.get_function_name()} started")

    def check_is_win_bid(path_name: str) -> bool:
        """
        判断是否中标
        :param path_name:
        :return:
        """
        return path_name not in ["废标结果", "废标公告", "终止公告", "终止结果"]

    def check_is_termination_announcement(path_name: str) -> bool:
        """
        判断是否终止公告
        :param path_name:
        :return:
        """
        return path_name in ["终止公告", "终止结果"]

    result = []
    for item in data:
        result_api_meta = {
            # 结果公告的id
            constants.KEY_PROJECT_RESULT_ARTICLE_ID: item["articleId"],
            # 发布日期
            constants.KEY_PROJECT_RESULT_PUBLISH_DATE: item["publishDate"],
            # 公告发布者
            constants.KEY_PROJECT_AUTHOR: item["author"],
            # 地区编号（可能为空）
            constants.KEY_PROJECT_DISTRICT_CODE: item["districtCode"],
            # 地区名称（可能为空）
            constants.KEY_PROJECT_DISTRICT_NAME: item["districtName"],
            # 采购物品名称
            constants.KEY_PROJECT_CATALOG: item["gpCatalogName"],
            # 采购方式
            constants.KEY_PROJECT_PROCUREMENT_METHOD: item["procurementMethod"],
            # 开标时间
            constants.KEY_PROJECT_BID_OPENING_TIME: item["bidOpeningTime"],
            # 是否中标
            constants.KEY_PROJECT_IS_WIN_BID: check_is_win_bid(item["pathName"]),
            # 是否为终止公告
            constants.KEY_PROJECT_IS_TERMINATION: check_is_termination_announcement(item['pathName']),
            # 终止公告原因
            constants.KEY_PROJECT_TERMINATION_REASON: None
        }
        result.append(result_api_meta)

    if _DEBUG:
        logger.debug(
            f"DEBUG INFO: {log.get_function_name()} finished, running time: {time.time() - start_time}"
        )
    return result


class SwitchError(Exception):
    """
    切换到另一个结果公告进行搜索
    """

    pass


def parse_html(html_content: str, is_wid_bid: bool):
    """
    解析 结果公告 中的 content
    :param html_content:
    :param is_wid_bid: 是否为中标结果
    :return:
    """
    start_time = time.time()
    if _DEBUG:
        logger.debug(f"DEBUG INFO: {log.get_function_name()} started")

    html = etree.HTML(html_content)
    text_list = [text.strip() for text in html.xpath("//text()")]
    result = common.filter_texts(text_list)

    def check_useful_part(title: str) -> bool:
        """
        检查是否包含有用信息的标题
        :param title:
        :return:
        """
        preview = ("评审专家" in title) or ("评审小组" in title)
        if is_wid_bid:
            win_bidding = ("中标（成交）信息" == title)
            return preview or win_bidding
        else:
            reason = ("废标理由" in title)
            shutdown = ("终止" in title)  # 终止原因
            return preview or reason or shutdown

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
                parts.append(result[pre:idx])
            else:
                idx += 1
    except BaseException as e:
        errorhandle.raise_error(e, "解析 parts 异常", result)

    try:
        if is_wid_bid:
            data = win.parse_win_bid(parts)
            if not data:
                raise SwitchError()
            else:
                return data
        else:
            return not_win.parse_not_win_bid(parts)
    except SwitchError as e:
        raise e  # 不能被 raise_error所处理，直接抛出
    except BaseException as e:
        errorhandle.raise_error(e, "解析 bid 异常", parts)
    finally:
        if _DEBUG:
            logger.debug(
                f"DEBUG INFO: {log.get_function_name()} finished, running: {time.time() - start_time}\n"
            )


if __name__ == "__main__":
    content = ("<style id=\"fixTableStyle\" type=\"text/css\">th,td {border:1px solid #DDD;padding: 5px "
               "10px;}</style>\n<div id=\"fixTableStyle\" type=\"text/css\" cdata_tag=\"style\" cdata_data=\"th,"
               "td {border:1px solid #DDD;padding: 5px 10px;}\" _ue_custom_node_=\"true\"></div><div><p "
               "style=\"line-height: 1.5em;\"><strong style=\"font-size: 18px; font-family: SimHei, sans-serif; "
               "text-align: justify;\">一、项目编号：</strong><span style=\"font-family: 黑体, SimHei; font-size: "
               "18px;\">&nbsp;<span class=\"bookmark-item uuid-1596280499822 code-00004 addWord "
               "single-line-text-input-box-cls\">HCZC2021-C3-210232-HYZX</span>&nbsp;</span>&nbsp; &nbsp; &nbsp; "
               "&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;</p><p style=\"margin: 17px 0px; text-align: justify; "
               "break-after: avoid; font-size: 18px; font-family: SimHei, sans-serif; white-space: normal; "
               "line-height: 1.5em;\"><span style=\"font-size: 18px;\"><strong>二、项目名称：</strong>&nbsp;<span "
               "class=\"bookmark-item uuid-1591615489941 code-00003 addWord "
               "single-line-text-input-box-cls\">采购社会救助经办服务</span>&nbsp;</span> &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; "
               "&nbsp; &nbsp; &nbsp; &nbsp; &nbsp;</p><p style=\"margin-bottom: 15px; line-height: "
               "1.5em;\"><strong><span style=\"font-size: 18px; font-family: SimHei, "
               "sans-serif;\">三、中标（成交）信息</span></strong> &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; "
               "&nbsp; &nbsp;</p><div style=\" font-size:18px;  font-family:FangSong;  line-height:20px; \"><p "
               "style=\"line-height: normal;\"><span style=\"font-size: 18px;\">&nbsp; &nbsp;</span>1.中标结果：</p><table "
               "class=\"template-bookmark uuid-1599570948000 code-AM014zbcj001 text-中标/成交结果信息\" width=\"751\" "
               "style=\"width:100%;border-collapse:collapse;\"><thead><tr class=\"firstRow\"><th "
               "style=\"background-color: rgb(255, 255, 255);\">序号</th><th style=\"background-color: rgb(255, 255, "
               "255);\">中标（成交）金额(元)</th><th style=\"background-color: rgb(255, 255, 255);\">中标供应商名称</th><th "
               "style=\"background-color: rgb(255, 255, 255);\">中标供应商地址</th></tr></thead><tbody><tr "
               "style=\"text-align: center;\" width=\"100%\"><td class=\"code-sectionNo\">1</td><td "
               "class=\"code-summaryPrice\">最终报价:688000.00(元)</td><td "
               "class=\"code-winningSupplierName\">广西大贤通讯设备有限公司</td><td "
               "class=\"code-winningSupplierAddr\">南宁市东葛路9号联发臻品3栋1单元205</td></tr><tr style=\"text-align: center;\" "
               "width=\"100%\"><td class=\"code-sectionNo\">2</td><td class=\"code-summaryPrice\">最终报价:699700("
               "元)</td><td class=\"code-winningSupplierName\">广西助力社会救助服务中心</td><td "
               "class=\"code-winningSupplierAddr\">广西南宁市良庆区凯旋路16号裕达国际中心广东大厦1301-1</td></tr></tbody></table><p "
               "style=\"line-height: normal; font-family: FangSong; font-size: 18px; white-space: normal;\">&nbsp; "
               "&nbsp;2.废标结果:&nbsp;&nbsp;</p><p style=\"margin-bottom: 5px; line-height: normal;\" "
               "class=\"sub\">&nbsp; &nbsp;<span class=\"bookmark-item uuid-1589193355355 code-41007  addWord\">\n "
               "&nbsp; &nbsp; </span></p><table class=\"form-panel-input-cls\" width=\"100%\"><tbody><tr "
               "style=\"text-align: center;\" width=\"100%\" class=\"firstRow\"><td width=\"25.0%\" "
               "style=\"word-break:break-all;\">序号</td><td width=\"25.0%\" "
               "style=\"word-break:break-all;\">标项名称</td><td width=\"25.0%\" "
               "style=\"word-break:break-all;\">废标理由</td><td width=\"25.0%\" style=\"word-break:break-all;\" "
               "colspan=\"1\">其他事项</td></tr><tr style=\"text-align: center;\" width=\"100%\"><td width=\"25.0%\" "
               "style=\"word-break:break-all;\">/</td><td width=\"25.0%\" style=\"word-break:break-all;\">/</td><td "
               "width=\"25.0%\" style=\"word-break:break-all;\">/</td><td width=\"25.0%\" "
               "style=\"word-break:break-all;\" colspan=\"1\">/</td></tr></tbody></table>&nbsp;<p></p></div><p "
               "style=\"margin: 17px 0;text-align: justify;line-height: 30px;break-after: avoid;font-size: "
               "18px;font-family: SimHei, sans-serif;white-space: normal\"><span style=\"font-size: "
               "18px;\"><strong>四、主要标的信息</strong></span> &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; "
               "&nbsp; &nbsp;</p><div style=\" font-size:18px;  font-family:FangSong;  line-height:20px;\"><div "
               "class=\"class-condition-filter-block\"><p style=\"line-height: normal;\">&nbsp; "
               "&nbsp;服务类主要标的信息：</p><p style=\"line-height: normal;\" class=\"sub\">&nbsp; &nbsp;&nbsp;<span "
               "class=\"bookmark-item uuid-1589437811676 code-AM014infoOfServiceObject  addWord\">\n &nbsp; &nbsp; "
               "&nbsp;</span></p><table class=\"form-panel-input-cls\" width=\"100%\"><tbody><tr style=\"text-align: "
               "center;\" width=\"100%\" class=\"firstRow\"><td width=\"14.29%\" "
               "style=\"word-break:break-all;\">序号</td><td width=\"14.29%\" "
               "style=\"word-break:break-all;\">标项名称</td><td width=\"14.29%\" "
               "style=\"word-break:break-all;\">标的名称</td><td width=\"14.29%\" "
               "style=\"word-break:break-all;\">服务范围</td><td width=\"14.29%\" "
               "style=\"word-break:break-all;\">服务要求</td><td width=\"14.29%\" "
               "style=\"word-break:break-all;\">服务时间</td><td width=\"14.29%\" style=\"word-break:break-all;\" "
               "colspan=\"1\">服务标准</td></tr><tr style=\"text-align: center;\" width=\"100%\"><td width=\"14.29%\" "
               "style=\"word-break:break-all;\">1</td><td width=\"14.29%\" "
               "style=\"word-break:break-all;\">采购社会救助经办服务Ⅰ标段</td><td width=\"14.29%\" "
               "style=\"word-break:break-all;\">采购社会救助经办服务Ⅰ标段</td><td width=\"14.29%\" "
               "style=\"word-break:break-all;\">南丹县六寨镇、月里镇、吾隘镇及八圩乡部分。</td><td width=\"14.29%\" "
               "style=\"word-break:break-all;\">详见采购文件采购需求。</td><td width=\"14.29%\" "
               "style=\"word-break:break-all;\">合同签订之日起一年内开展相关社会救助经办服务工作，具体的时间计划安排按照实际要求执行</td><td width=\"14.29%\" "
               "style=\"word-break:break-all;\" colspan=\"1\">详见采购文件采购需求。</td></tr><tr style=\"text-align: center;\" "
               "width=\"100%\"><td width=\"14.29%\" style=\"word-break:break-all;\">2</td><td width=\"14.29%\" "
               "style=\"word-break:break-all;\">采购社会救助经办服务Ⅱ标段</td><td width=\"14.29%\" "
               "style=\"word-break:break-all;\">采购社会救助经办服务Ⅱ标段</td><td width=\"14.29%\" "
               "style=\"word-break:break-all;\">南丹县中堡乡、芒场镇、罗富镇、大厂镇及城关镇、里湖乡、八圩乡部分。</td><td width=\"14.29%\" "
               "style=\"word-break:break-all;\">详见采购文件采购需求。</td><td width=\"14.29%\" "
               "style=\"word-break:break-all;\">合同签订之日起一年内开展相关社会救助经办服务工作，具体的时间计划安排按照实际要求执行。</td><td width=\"14.29%\" "
               "style=\"word-break:break-all;\" "
               "colspan=\"1\">详见采购文件采购需求。</td></tr></tbody></table>&nbsp;<p></p></div></div><p style=\"margin: 17px "
               "0;text-align: justify;line-height: 30px;break-after: avoid;font-size: 18px;font-family: SimHei, "
               "sans-serif;white-space: normal\"><span style=\"font-size: "
               "18px;\"><strong>五、评审专家（单一来源采购人员）名单：</strong></span> &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; "
               "&nbsp; &nbsp; &nbsp;</p><p><span style=\"font-size: 18px; font-family:FangSong;  line-height:20px; "
               "\">&nbsp; &nbsp;&nbsp;<span class=\"bookmark-item uuid-1589193390811 code-85005 addWord "
               "multi-line-text-input-box-cls\">卢广平,李娟,王晓燕</span>&nbsp;</span> &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; "
               "&nbsp; &nbsp; &nbsp; &nbsp; &nbsp;</p><p style=\"margin: 17px 0;text-align: justify;line-height: "
               "30px;break-after: avoid;font-size: 18px;font-family: SimHei, sans-serif;white-space: normal\"><span "
               "style=\"font-size: 18px;\"><strong>六、代理服务收费标准及金额：</strong></span>&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; "
               "&nbsp; &nbsp; &nbsp; &nbsp;</p><p><span style=\"font-size: 18px; font-family:FangSong;  "
               "line-height:20px; \">&nbsp; &nbsp;1.代理服务收费标准：<span class=\"bookmark-item uuid-1591615554332 "
               "code-AM01400039 addWord multi-line-text-input-box-cls\">按国家发展计划委员会《招标代理服务费管理暂行办法》（计价格["
               "2002]1980号）服务类收费标准</span>&nbsp;</span> &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; "
               "&nbsp;</p><p><span style=\"font-size: 18px; font-family:FangSong;  line-height:20px; \">&nbsp; "
               "&nbsp;2.代理服务收费金额（元）：<span class=\"bookmark-item uuid-1591615558580 code-AM01400040 addWord "
               "numeric-input-box-cls readonly\">30815</span>&nbsp;</span>&nbsp;</p><p style=\"margin: 17px "
               "0;text-align: justify;line-height: 30px;break-after: avoid;font-size: 18px;font-family: SimHei, "
               "sans-serif;white-space: normal\"><span style=\"font-size: 18px;\"><strong>七、公告期限</strong></span> "
               "&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;</p><p><span style=\"font-size: "
               "18px; font-family:FangSong;  line-height:20px; \">&nbsp; &nbsp;自本公告发布之日起1个工作日。</span> &nbsp; &nbsp; "
               "&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;</p><p style=\"margin: 17px 0px; text-align: "
               "justify; line-height: 30px; break-after: avoid; font-family: SimHei, sans-serif; white-space: "
               "normal;\"><span style=\"font-size: 18px;\"><strong>八、其他补充事宜</strong></span>&nbsp; &nbsp; &nbsp; "
               "&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;</p><p style=\"line-height: 1.5em;\"><span "
               "style=\"font-size: 18px; font-family:FangSong;  line-height:20px; \">&nbsp; &nbsp;&nbsp;</span><span "
               "style=\"font-size: 18px; font-family: FangSong; line-height: 20px;\">&nbsp;<span "
               "class=\"bookmark-item uuid-1592539159169 code-81205 addWord "
               "multi-line-text-input-box-cls\">1.本次采购公告同时在中国政府采购网（www.ccgp.gov.cn）、广西壮族自治区政府采购网 "
               "（http://zfcg.gxzf.gov.cn/）、全国公共资源交易平台（广西·河池）（http://ggzy.jgswj.gxzf.gov.cn/hcggzy/）发布。</span>&nbsp"
               ";</span>&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;</p><p "
               "style=\"margin: 17px 0;text-align: justify;line-height: 32px;break-after: avoid;font-size: "
               "18px;font-family: SimHei, sans-serif;white-space: normal\"><span style=\"font-size: "
               "18px;\"><strong>九、对本次公告内容提出询问，请按以下方式联系</strong><span style=\"font-family: sans-serif; font-size: "
               "16px;\">　　　</span></span><span style=\"font-size: 18px; font-family: FangSong;\">&nbsp; &nbsp;</span> "
               "&nbsp; &nbsp; &nbsp; &nbsp;</p><div style=\"font-family:FangSong;line-height:30px;\"><p><span "
               "style=\"font-size: 18px;\">&nbsp; &nbsp; 1.采购人信息</span>&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; "
               "&nbsp;</p><p><span style=\"font-size: 18px;\">&nbsp; &nbsp; 名&nbsp;&nbsp;&nbsp; 称：<span "
               "class=\"bookmark-item uuid-1596004663203 code-00014 editDisable interval-text-box-cls "
               "readonly\">南丹县民政局</span>&nbsp;&nbsp;</span> &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;</p><p><span "
               "style=\"font-size: 18px;\">&nbsp; &nbsp; 地&nbsp;&nbsp;&nbsp; 址：<span class=\"bookmark-item "
               "uuid-1596004672274 code-00018 addWord "
               "single-line-text-input-box-cls\">南丹县城关镇民政路01号</span>&nbsp;</span>&nbsp; &nbsp; &nbsp; &nbsp; "
               "&nbsp;</p><p><span style=\"font-size: 18px;\">&nbsp; &nbsp; 项目联系人：<span class=\"bookmark-item "
               "uuid-1596004688403 code-00015 editDisable single-line-text-input-box-cls "
               "readonly\">王艳</span>&nbsp;</span> &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;</p><p><span "
               "style=\"font-size: 18px;\">&nbsp; &nbsp; 项目联系方式：<span class=\"bookmark-item uuid-1596004695990 "
               "code-00016 editDisable single-line-text-input-box-cls "
               "readonly\">0778-7232292</span>&nbsp;&nbsp;</span>&nbsp; &nbsp; &nbsp; &nbsp; &nbsp;</p><p><span "
               "style=\"font-size: 18px;\">&nbsp; &nbsp;&nbsp;2.采购代理机构信息</span> &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; "
               "&nbsp;</p><p><span style=\"font-size: 18px;\">&nbsp; &nbsp; 名&nbsp;&nbsp;&nbsp; 称：<span "
               "class=\"bookmark-item uuid-1596004721081 code-00009 addWord "
               "interval-text-box-cls\">广西浩业工程咨询有限公司</span>&nbsp;</span> &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; "
               "&nbsp;</p><p><span style=\"font-size: 18px;\">&nbsp; &nbsp; 地&nbsp;&nbsp;&nbsp; 址：<span "
               "class=\"bookmark-item uuid-1596004728442 code-00013 editDisable single-line-text-input-box-cls "
               "readonly\">河池市金城江区上任南路27号（金旅国际投资大厦一单元501号）</span>&nbsp;</span>&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; "
               "&nbsp; &nbsp;</p><p><span style=\"font-size: 18px;\">&nbsp; &nbsp; 项目联系人：<span class=\"bookmark-item "
               "uuid-1596004745033 code-00010 editDisable single-line-text-input-box-cls "
               "readonly\">杨睿</span>&nbsp;&nbsp;</span> &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;</p><p><span "
               "style=\"font-size: 18px;\">&nbsp; &nbsp; 项目联系方式：<span class=\"bookmark-item uuid-1596004753055 "
               "code-00011 addWord single-line-text-input-box-cls\">0778-2288567</span>&nbsp;</span>&nbsp; &nbsp; "
               "&nbsp; &nbsp; &nbsp; &nbsp; &nbsp;</p></div></div><p style='font-size' class='fjxx'>附件信息：</p><ul "
               "class=\"fjxx\" style=\"font-size: 16px;margin-left: 38px;color: #0065ef;list-style-type: "
               "none;\"><li><p style=\"display:inline-block\"><a "
               "href=\"https://zcy-gov-open-doc.oss-cn-north-2-gov-1.aliyuncs.com/1024FPA/451202/1000623103/20221"
               "/923590fb-c40a-40af-a12f-7c883c54c63a\">中小企业声明函.zip</a></p><p "
               "style=\"display:inline-block;margin-left:20px\">364.2K</p></li></ul>")
    res = parse_html(content, True)
    print(res)
