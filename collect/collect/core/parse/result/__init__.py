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


def parse_response_data(data):
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
        return path_name not in ["废标结果", "废标公告"]

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
        }
        result.append(result_api_meta)

    if _DEBUG:
        logger.debug(
            f"DEBUG INFO: {log.get_function_name()} finished\n"
            f"DEBUG INFO: running time: {time.time() - start_time}"
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
            win_bidding = "中标（成交）信息" == title
            return preview or win_bidding
        else:
            reason = "废标理由" in title
            return preview or reason

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
    content = (
        '<style id="fixTableStyle" type="text/css">th,td {border:1px solid #DDD;padding: 5px '
        '10px;}</style>\n<div id="fixTableStyle" type="text/css" cdata_tag="style" cdata_data="th,'
        'td {border:1px solid #DDD;padding: 5px 10px;}" _ue_custom_node_="true"></div><div><p '
        'style="line-height: 1.5em;"><strong style="font-size: 18px; font-family: SimHei, sans-serif; '
        'text-align: justify;">一、项目编号：</strong><span style="font-family: 黑体, SimHei; font-size: '
        '18px;">&nbsp;<span class="bookmark-item uuid-1596280499822 code-00004 addWord '
        'single-line-text-input-box-cls">YLZC2021-J3-210465-GXYY</span>&nbsp;</span>&nbsp; &nbsp; &nbsp; '
        '&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;</p><p style="margin: 17px 0px; text-align: justify; '
        "break-after: avoid; font-size: 18px; font-family: SimHei, sans-serif; white-space: normal; "
        'line-height: 1.5em;"><span style="font-size: 18px;"><strong>二、项目名称：</strong>&nbsp;<span '
        'class="bookmark-item uuid-1591615489941 code-00003 addWord '
        'single-line-text-input-box-cls">容县自然资源局关于招标采购容县农村集体经营性建设用地入市先行推进县技术咨询服务</span>&nbsp;</span> &nbsp; '
        '&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;</p><p style="margin-bottom: 15px; '
        'line-height: 1.5em;"><strong><span style="font-size: 18px; font-family: SimHei, '
        'sans-serif;">三、中标（成交）信息</span></strong> &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; '
        '&nbsp; &nbsp;</p><div style=" font-size:18px;  font-family:FangSong;  line-height:20px; "><p '
        'style="line-height: normal;"><span style="font-size: 18px;">&nbsp; &nbsp;</span>1.中标结果：</p><table '
        'class="template-bookmark uuid-1599570948000 code-AM014zbcj001 text-中标/成交结果信息" width="751" '
        'style="width:100%;border-collapse:collapse;"><thead><tr class="firstRow"><th style="background-color: '
        'rgb(255, 255, 255);">序号</th><th style="background-color: rgb(255, 255, 255);">中标（成交）金额(元)</th><th '
        'style="background-color: rgb(255, 255, 255);">中标供应商名称</th><th style="background-color: rgb(255, 255, '
        '255);">中标供应商地址</th></tr></thead><tbody><tr style="text-align: center;" width="100%"><td '
        'class="code-sectionNo">1</td><td class="code-summaryPrice">报价:798000(元)</td><td '
        'class="code-winningSupplierName">广西北部湾空间规划设计研究院有限公司</td><td '
        'class="code-winningSupplierAddr">南宁市青秀区东葛路118号南宁青秀万达广场东6栋122号商铺</td></tr></tbody></table><p '
        'style="line-height: normal; font-family: FangSong; font-size: 18px; white-space: normal;">&nbsp; '
        '&nbsp;2.废标结果:&nbsp;&nbsp;</p><p style="margin-bottom: 5px; line-height: normal;" class="sub">&nbsp; '
        '&nbsp;<span class="bookmark-item uuid-1589193355355 code-41007  addWord">\n &nbsp; &nbsp; '
        '</span></p><table class="form-panel-input-cls" width="100%"><tbody><tr style="text-align: center;" '
        'width="100%" class="firstRow"><td width="25.0%" style="word-break:break-all;">序号</td><td '
        'width="25.0%" style="word-break:break-all;">标项名称</td><td width="25.0%" '
        'style="word-break:break-all;">废标理由</td><td width="25.0%" style="word-break:break-all;" '
        'colspan="1">其他事项</td></tr><tr style="text-align: center;" width="100%"><td width="25.0%" '
        'style="word-break:break-all;">/</td><td width="25.0%" style="word-break:break-all;">/</td><td '
        'width="25.0%" style="word-break:break-all;">/</td><td width="25.0%" style="word-break:break-all;" '
        'colspan="1">/</td></tr></tbody></table>&nbsp;<p></p></div><p style="margin: 17px 0;text-align: '
        "justify;line-height: 30px;break-after: avoid;font-size: 18px;font-family: SimHei, "
        'sans-serif;white-space: normal"><span style="font-size: 18px;"><strong>四、主要标的信息</strong></span> '
        '&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;</p><div style=" font-size:18px; '
        ' font-family:FangSong;  line-height:20px;"><div class="class-condition-filter-block"><p '
        'style="line-height: normal;">&nbsp; &nbsp;服务类主要标的信息：</p><p style="line-height: normal;" '
        'class="sub">&nbsp; &nbsp;&nbsp;<span class="bookmark-item uuid-1589437811676 '
        'code-AM014infoOfServiceObject  addWord">\n &nbsp; &nbsp; &nbsp;</span></p><table '
        'class="form-panel-input-cls" width="100%"><tbody><tr style="text-align: center;" width="100%" '
        'class="firstRow"><td width="14.29%" style="word-break:break-all;">序号</td><td width="14.29%" '
        'style="word-break:break-all;">标项名称</td><td width="14.29%" style="word-break:break-all;">标的名称</td><td '
        'width="14.29%" style="word-break:break-all;">服务范围</td><td width="14.29%" '
        'style="word-break:break-all;">服务要求</td><td width="14.29%" style="word-break:break-all;">服务时间</td><td '
        'width="14.29%" style="word-break:break-all;" colspan="1">服务标准</td></tr><tr style="text-align: '
        'center;" width="100%"><td width="14.29%" style="word-break:break-all;">1</td><td width="14.29%" '
        'style="word-break:break-all;">容县自然资源局关于招标采购容县农村集体经营性建设用地入市先行推进县技术咨询服务</td><td width="14.29%" '
        'style="word-break:break-all;">容县自然资源局关于招标采购容县农村集体经营性建设用地入市先行推进县技术咨询服务</td><td width="14.29%" '
        'style="word-break:break-all;">容县</td><td width="14.29%" '
        'style="word-break:break-all;">容县自然资源局关于招标采购容县农村集体经营性建设用地入市先行推进县技术咨询服务</td><td width="14.29%" '
        'style="word-break:break-all;">自签订合同之日起至容县农村集体经营性建设用地成功入市3个实例为基准之日止（若因实际工作需要，经双方协</td><td '
        'width="14.29%" style="word-break:break-all;" '
        'colspan="1">符合国家规定的标准、政策和现行技术规范、规程要求。</td></tr></tbody></table>&nbsp;<p></p></div></div><p '
        'style="margin: 17px 0;text-align: justify;line-height: 30px;break-after: avoid;font-size: '
        '18px;font-family: SimHei, sans-serif;white-space: normal"><span style="font-size: '
        '18px;"><strong>五、评审专家（单一来源采购人员）名单：</strong></span> &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; '
        '&nbsp; &nbsp; &nbsp;</p><p><span style="font-size: 18px; font-family:FangSong;  line-height:20px; '
        '">&nbsp; &nbsp;&nbsp;<span class="bookmark-item uuid-1589193390811 code-85005 addWord '
        'multi-line-text-input-box-cls">明俭,吕春林,钟金成(采购人代表)</span>&nbsp;</span> &nbsp; &nbsp; &nbsp; &nbsp; '
        '&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;</p><p style="margin: 17px 0;text-align: '
        "justify;line-height: 30px;break-after: avoid;font-size: 18px;font-family: SimHei, "
        'sans-serif;white-space: normal"><span style="font-size: '
        '18px;"><strong>六、代理服务收费标准及金额：</strong></span>&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; '
        '&nbsp;</p><p><span style="font-size: 18px; font-family:FangSong;  line-height:20px; ">&nbsp; '
        '&nbsp;1.代理服务收费标准：<span class="bookmark-item uuid-1591615554332 code-AM01400039 addWord '
        'multi-line-text-input-box-cls">成交供应商应在领取成交通知书前，向采购代理机构广西宇鹰招标代理有限公司一次性付清采购代理服务费。本项目的采购代理服务费为成交价的1.5'
        "%收取。</span>&nbsp;</span> &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; "
        '&nbsp;</p><p><span style="font-size: 18px; font-family:FangSong;  line-height:20px; ">&nbsp; '
        '&nbsp;2.代理服务收费金额（元）：<span class="bookmark-item uuid-1591615558580 code-AM01400040 addWord '
        'numeric-input-box-cls readonly">11970</span>&nbsp;</span>&nbsp;</p><p style="margin: 17px '
        "0;text-align: justify;line-height: 30px;break-after: avoid;font-size: 18px;font-family: SimHei, "
        'sans-serif;white-space: normal"><span style="font-size: 18px;"><strong>七、公告期限</strong></span> &nbsp; '
        '&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;</p><p><span style="font-size: 18px; '
        'font-family:FangSong;  line-height:20px; ">&nbsp; &nbsp;自本公告发布之日起1个工作日。</span> &nbsp; &nbsp; &nbsp; '
        '&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;</p><p style="margin: 17px 0px; text-align: justify; '
        'line-height: 30px; break-after: avoid; font-family: SimHei, sans-serif; white-space: normal;"><span '
        'style="font-size: 18px;"><strong>八、其他补充事宜</strong></span>&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; '
        '&nbsp; &nbsp; &nbsp; &nbsp;</p><p style="line-height: 1.5em;"><span style="font-size: 18px; '
        'font-family:FangSong;  line-height:20px; ">&nbsp; &nbsp;&nbsp;</span><span style="font-size: 18px; '
        'font-family: FangSong; line-height: 20px;">&nbsp;<span class="bookmark-item uuid-1592539159169 '
        'code-81205  addWord"></span>&nbsp;</span>&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; '
        '&nbsp; &nbsp; &nbsp;</p><p style="margin: 17px 0;text-align: justify;line-height: 32px;break-after: '
        'avoid;font-size: 18px;font-family: SimHei, sans-serif;white-space: normal"><span style="font-size: '
        '18px;"><strong>九、对本次公告内容提出询问，请按以下方式联系</strong><span style="font-family: sans-serif; font-size: '
        '16px;">　　　</span></span><span style="font-size: 18px; font-family: FangSong;">&nbsp; &nbsp;</span> '
        '&nbsp; &nbsp; &nbsp; &nbsp;</p><div style="font-family:FangSong;line-height:30px;"><p><span '
        'style="font-size: 18px;">&nbsp; &nbsp; 1.采购人信息</span>&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; '
        '&nbsp;</p><p><span style="font-size: 18px;">&nbsp; &nbsp; 名&nbsp;&nbsp;&nbsp; 称：<span '
        'class="bookmark-item uuid-1596004663203 code-00014 editDisable interval-text-box-cls '
        'readonly">容县自然资源局</span>&nbsp;&nbsp;</span> &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;</p><p><span '
        'style="font-size: 18px;">&nbsp; &nbsp; 地&nbsp;&nbsp;&nbsp; 址：<span class="bookmark-item '
        "uuid-1596004672274 code-00018 addWord "
        'single-line-text-input-box-cls">容州镇桂南路150号</span>&nbsp;</span>&nbsp; &nbsp; &nbsp; &nbsp; '
        '&nbsp;</p><p><span style="font-size: 18px;">&nbsp; &nbsp; 项目联系人：<span class="bookmark-item '
        "uuid-1596004688403 code-00015 editDisable single-line-text-input-box-cls "
        'readonly">杨克武</span>&nbsp;</span> &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;</p><p><span '
        'style="font-size: 18px;">&nbsp; &nbsp; 项目联系方式：<span class="bookmark-item uuid-1596004695990 '
        "code-00016 editDisable single-line-text-input-box-cls "
        'readonly">0775-5337899</span>&nbsp;&nbsp;</span>&nbsp; &nbsp; &nbsp; &nbsp; &nbsp;</p><p><span '
        'style="font-size: 18px;">&nbsp; &nbsp;&nbsp;2.采购代理机构信息</span> &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; '
        '&nbsp;</p><p><span style="font-size: 18px;">&nbsp; &nbsp; 名&nbsp;&nbsp;&nbsp; 称：<span '
        'class="bookmark-item uuid-1596004721081 code-00009 addWord '
        'interval-text-box-cls">广西宇鹰招标代理有限公司</span>&nbsp;</span> &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; '
        '&nbsp;</p><p><span style="font-size: 18px;">&nbsp; &nbsp; 地&nbsp;&nbsp;&nbsp; 址：<span '
        'class="bookmark-item uuid-1596004728442 code-00013 editDisable single-line-text-input-box-cls '
        'readonly">广西容县容州镇河南中街8号</span>&nbsp;</span>&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; '
        '&nbsp;</p><p><span style="font-size: 18px;">&nbsp; &nbsp; 项目联系人：<span class="bookmark-item '
        "uuid-1596004745033 code-00010 editDisable single-line-text-input-box-cls "
        'readonly">庞羽晴</span>&nbsp;&nbsp;</span> &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;</p><p><span '
        'style="font-size: 18px;">&nbsp; &nbsp; 项目联系方式：<span class="bookmark-item uuid-1596004753055 '
        'code-00011 addWord single-line-text-input-box-cls">0775-5333963</span>&nbsp;</span>&nbsp; &nbsp; '
        "&nbsp; &nbsp; &nbsp; &nbsp; &nbsp;</p></div></div>"
    )
    res = parse_html(content, True)
    print(res)
