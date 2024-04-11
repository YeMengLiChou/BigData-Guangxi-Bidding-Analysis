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
            constants.KEY_PROJECT_IS_TERMINATION: check_is_termination_announcement(
                item["pathName"]
            ),
            # 终止公告原因
            constants.KEY_PROJECT_TERMINATION_REASON: None,
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
    start_time = 0
    if _DEBUG:
        start_time = time.time()
        logger.debug(f"DEBUG INFO: {log.get_function_name()} started")

    result = common.parse_html(html_content=html_content)
    print('\n'.join(result))

    def check_useful_part(title: str) -> bool:
        """
        检查是否包含有用信息的标题
        :param title:
        :return:
        """
        preview = ("评审专家" in title) or ("评审小组" in title)
        if is_wid_bid:
            win_bidding = "中标（成交）信息" == title
            return preview or win_bidding
        else:
            reason = "废标理由" in title
            shutdown = "终止" in title  # 终止原因
            return preview or reason or shutdown

    def check_project_code(title: str) -> bool:
        """
        检查是否包含项目编号
        :param title:
        :return:
        """
        return "项目编号" in title

    def check_project_name(title: str) -> bool:
        """
        检查是否包含项目名称
        :param title:
        :return:
        """
        return "项目名称" in title

    n, idx, parts = len(result), 0, []
    project_data, chinese_number_index = dict(), 1
    try:
        # TODO: 将项目编号等信息从 purchase 转移到此处，保证 result 能够将所有基本信息爬取完毕（部分公告没有采购公告）
        while idx < n:
            # 找以 “一、” 这种格式开头的字符串
            index = common.startswith_chinese_number(result[idx])
            if index >= chinese_number_index:
                # 项目编号从 purchase 移动到此处
                if check_project_code(title=result[idx]):
                    project_data[constants.KEY_PROJECT_CODE] = result[idx + 1]
                    idx += 2
                    continue
                # 项目名称从 purchase 移动到此处
                if check_project_name(title=result[idx]):
                    project_data[constants.KEY_PROJECT_NAME] = result[idx + 1]
                    idx += 2
                    continue

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
                data.update(project_data)
                return data
        else:
            data = not_win.parse_not_win_bid(parts)
            data.update(project_data)
            return data
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
    content = \
        "<style id=\"fixTableStyle\" type=\"text/css\">th,td {border:1px solid #DDD;padding: 5px 10px;}</style><div><p style=\"line-height: 1.5em;\"><strong style=\"font-size: 18px; font-family: SimHei, sans-serif; text-align: justify;\">一、项目编号：</strong><span style=\"font-family: 黑体, SimHei; font-size: 18px;\">&nbsp;<span class=\"bookmark-item uuid-1596280499822 code-00004 addWord single-line-text-input-box-cls\">YLZC2021-J2-210518-GXYY</span>&nbsp;</span>&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;</p><p style=\"margin: 17px 0px; text-align: justify; break-after: avoid; font-size: 18px; font-family: SimHei, sans-serif; white-space: normal; line-height: 1.5em;\"><span style=\"font-size: 18px;\"><strong>二、项目名称：</strong>&nbsp;<span class=\"bookmark-item uuid-1591615489941 code-00003 addWord single-line-text-input-box-cls\">容县容州镇厢西社区荔枝根安置用地道路配套工程项目</span>&nbsp;</span> &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;</p><p style=\"margin-bottom: 15px; line-height: 1.5em;\"><strong><span style=\"font-size: 18px; font-family: SimHei, sans-serif;\">三、中标（成交）信息</span></strong> &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;</p><div style=\" font-size:18px;  font-family:FangSong;  line-height:20px; \"><p style=\"line-height: normal;\"><span style=\"font-size: 18px;\">&nbsp; &nbsp;</span>1.中标结果：</p><table class=\"template-bookmark uuid-1599570948000 code-AM014zbcj001 text-中标/成交结果信息\" width=\"751\" style=\"width:100%;border-collapse:collapse;\"><thead><tr class=\"firstRow\"><th style=\"background-color: rgb(255, 255, 255);\">序号</th><th style=\"background-color: rgb(255, 255, 255);\">中标（成交）金额(元)</th><th style=\"background-color: rgb(255, 255, 255);\">中标供应商名称</th><th style=\"background-color: rgb(255, 255, 255);\">中标供应商地址</th></tr></thead><tbody><tr style=\"text-align: center;\" width=\"100%\"><td class=\"code-sectionNo\">1</td><td class=\"code-summaryPrice\">报价:1444851.19(元)</td><td class=\"code-winningSupplierName\">广西容县建筑工程总公司</td><td class=\"code-winningSupplierAddr\">容县容州镇城西路79号</td></tr></tbody></table><p style=\"line-height: normal; font-family: FangSong; font-size: 18px; white-space: normal;\">&nbsp; &nbsp;2.废标结果:&nbsp;&nbsp;</p><p style=\"margin-bottom: 5px; line-height: normal;\" class=\"sub\">&nbsp; &nbsp;<span class=\"bookmark-item uuid-1589193355355 code-41007  addWord\">\n &nbsp; &nbsp; </span></p><table class=\"form-panel-input-cls\" width=\"100%\"><tbody><tr style=\"text-align: center;\" width=\"100%\" class=\"firstRow\"><td width=\"25.0%\" style=\"word-break:break-all;\">序号</td><td width=\"25.0%\" style=\"word-break:break-all;\">标项名称</td><td width=\"25.0%\" style=\"word-break:break-all;\">废标理由</td><td width=\"25.0%\" style=\"word-break:break-all;\" colspan=\"1\">其他事项</td></tr><tr style=\"text-align: center;\" width=\"100%\"><td width=\"25.0%\" style=\"word-break:break-all;\">/</td><td width=\"25.0%\" style=\"word-break:break-all;\">/</td><td width=\"25.0%\" style=\"word-break:break-all;\">/</td><td width=\"25.0%\" style=\"word-break:break-all;\" colspan=\"1\">/</td></tr></tbody></table>&nbsp;<p></p></div><p style=\"margin: 17px 0;text-align: justify;line-height: 30px;break-after: avoid;font-size: 18px;font-family: SimHei, sans-serif;white-space: normal\"><span style=\"font-size: 18px;\"><strong>四、主要标的信息</strong></span> &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;</p><div style=\" font-size:18px;  font-family:FangSong;  line-height:20px;\"><div class=\"class-condition-filter-block\"><p style=\"line-height: normal;\">&nbsp; &nbsp;工程类主要标的信息：</p><p style=\"line-height: normal;\" class=\"sub\">&nbsp; &nbsp;&nbsp;<span class=\"bookmark-item uuid-1589437807972 code-AM014infoOfEngSubMatter  addWord\">\n &nbsp; &nbsp; &nbsp;</span></p><table class=\"form-panel-input-cls\" width=\"100%\"><tbody><tr style=\"text-align: center;\" width=\"100%\" class=\"firstRow\"><td width=\"14.29%\" style=\"word-break:break-all;\">序号</td><td width=\"14.29%\" style=\"word-break:break-all;\">标项名称</td><td width=\"14.29%\" style=\"word-break:break-all;\">标的名称</td><td width=\"14.29%\" style=\"word-break:break-all;\">施工范围</td><td width=\"14.29%\" style=\"word-break:break-all;\">施工工期</td><td width=\"14.29%\" style=\"word-break:break-all;\">项目经理</td><td width=\"14.29%\" style=\"word-break:break-all;\" colspan=\"1\">执业证书信息</td></tr><tr style=\"text-align: center;\" width=\"100%\"><td width=\"14.29%\" style=\"word-break:break-all;\">1</td><td width=\"14.29%\" style=\"word-break:break-all;\">容县征地服务中心容县容州镇厢西社区荔枝根安置用地道路配套工程</td><td width=\"14.29%\" style=\"word-break:break-all;\">容县容州镇厢西社区荔枝根安置用地道路配套工程</td><td width=\"14.29%\" style=\"word-break:break-all;\">经备案的工程量清单范围内的所有内容</td><td width=\"14.29%\" style=\"word-break:break-all;\">60日内</td><td width=\"14.29%\" style=\"word-break:break-all;\">刘咏薇</td><td width=\"14.29%\" style=\"word-break:break-all;\" colspan=\"1\">桂建安B（2021）0003424</td></tr></tbody></table>&nbsp;&nbsp;<p></p></div></div><p style=\"margin: 17px 0;text-align: justify;line-height: 30px;break-after: avoid;font-size: 18px;font-family: SimHei, sans-serif;white-space: normal\"><span style=\"font-size: 18px;\"><strong>五、评审专家（单一来源采购人员）名单：</strong></span> &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;</p><p><span style=\"font-size: 18px; font-family:FangSong;  line-height:20px; \">&nbsp; &nbsp;&nbsp;<span class=\"bookmark-item uuid-1589193390811 code-85005 addWord multi-line-text-input-box-cls\">陈丽,杨贻钦</span>&nbsp;</span> &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;</p><p style=\"margin: 17px 0;text-align: justify;line-height: 30px;break-after: avoid;font-size: 18px;font-family: SimHei, sans-serif;white-space: normal\"><span style=\"font-size: 18px;\"><strong>六、代理服务收费标准及金额：</strong></span>&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;</p><p><span style=\"font-size: 18px; font-family:FangSong;  line-height:20px; \">&nbsp; &nbsp;1.代理服务收费标准：<span class=\"bookmark-item uuid-1591615554332 code-AM01400039 addWord multi-line-text-input-box-cls\">代理服务费按成交金额的1%收取</span>&nbsp;</span> &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;</p><p><span style=\"font-size: 18px; font-family:FangSong;  line-height:20px; \">&nbsp; &nbsp;2.代理服务收费金额（元）：<span class=\"bookmark-item uuid-1591615558580 code-AM01400040 addWord numeric-input-box-cls readonly\">14450</span>&nbsp;</span>&nbsp;</p><p style=\"margin: 17px 0;text-align: justify;line-height: 30px;break-after: avoid;font-size: 18px;font-family: SimHei, sans-serif;white-space: normal\"><span style=\"font-size: 18px;\"><strong>七、公告期限</strong></span> &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;</p><p><span style=\"font-size: 18px; font-family:FangSong;  line-height:20px; \">&nbsp; &nbsp;自本公告发布之日起1个工作日。</span> &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;</p><p style=\"margin: 17px 0px; text-align: justify; line-height: 30px; break-after: avoid; font-family: SimHei, sans-serif; white-space: normal;\"><span style=\"font-size: 18px;\"><strong>八、其他补充事宜</strong></span>&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;</p><p style=\"line-height: 1.5em;\"><span style=\"font-size: 18px; font-family:FangSong;  line-height:20px; \">&nbsp; &nbsp;&nbsp;</span><span style=\"font-size: 18px; font-family: FangSong; line-height: 20px;\">&nbsp;<span class=\"bookmark-item uuid-1592539159169 code-81205  addWord\"></span>&nbsp;</span>&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;</p><p style=\"margin: 17px 0;text-align: justify;line-height: 32px;break-after: avoid;font-size: 18px;font-family: SimHei, sans-serif;white-space: normal\"><span style=\"font-size: 18px;\"><strong>九、对本次公告内容提出询问，请按以下方式联系</strong><span style=\"font-family: sans-serif; font-size: 16px;\">　　　</span></span><span style=\"font-size: 18px; font-family: FangSong;\">&nbsp; &nbsp;</span> &nbsp; &nbsp; &nbsp; &nbsp;</p><div style=\"font-family:FangSong;line-height:30px;\"><p><span style=\"font-size: 18px;\">&nbsp; &nbsp; 1.采购人信息</span>&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;</p><p><span style=\"font-size: 18px;\">&nbsp; &nbsp; 名&nbsp;&nbsp;&nbsp; 称：<span class=\"bookmark-item uuid-1596004663203 code-00014 editDisable interval-text-box-cls readonly\">容县征地服务中心</span>&nbsp;&nbsp;</span> &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;</p><p><span style=\"font-size: 18px;\">&nbsp; &nbsp; 地&nbsp;&nbsp;&nbsp; 址：<span class=\"bookmark-item uuid-1596004672274 code-00018 addWord single-line-text-input-box-cls\">容县经济开发区金点子园区A4栋</span>&nbsp;</span>&nbsp; &nbsp; &nbsp; &nbsp; &nbsp;</p><p><span style=\"font-size: 18px;\">&nbsp; &nbsp; 项目联系人：<span class=\"bookmark-item uuid-1596004688403 code-00015 editDisable single-line-text-input-box-cls readonly\">刘亚平</span>&nbsp;</span> &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;</p><p><span style=\"font-size: 18px;\">&nbsp; &nbsp; 项目联系方式：<span class=\"bookmark-item uuid-1596004695990 code-00016 editDisable single-line-text-input-box-cls readonly\">0775-5133236</span>&nbsp;&nbsp;</span>&nbsp; &nbsp; &nbsp; &nbsp; &nbsp;</p><p><span style=\"font-size: 18px;\">&nbsp; &nbsp;&nbsp;2.采购代理机构信息</span> &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;</p><p><span style=\"font-size: 18px;\">&nbsp; &nbsp; 名&nbsp;&nbsp;&nbsp; 称：<span class=\"bookmark-item uuid-1596004721081 code-00009 addWord interval-text-box-cls\">广西宇鹰招标代理有限公司</span>&nbsp;</span> &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;</p><p><span style=\"font-size: 18px;\">&nbsp; &nbsp; 地&nbsp;&nbsp;&nbsp; 址：<span class=\"bookmark-item uuid-1596004728442 code-00013 editDisable single-line-text-input-box-cls readonly\">容县容州镇河南大道78号</span>&nbsp;</span>&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;</p><p><span style=\"font-size: 18px;\">&nbsp; &nbsp; 项目联系人：<span class=\"bookmark-item uuid-1596004745033 code-00010 editDisable single-line-text-input-box-cls readonly\">李军</span>&nbsp;&nbsp;</span> &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;</p><p><span style=\"font-size: 18px;\">&nbsp; &nbsp; 项目联系方式：<span class=\"bookmark-item uuid-1596004753055 code-00011 addWord single-line-text-input-box-cls\">0775-5333963</span>&nbsp;</span>&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;</p></div></div>"

    res = parse_html(content, True)
    print(res)
