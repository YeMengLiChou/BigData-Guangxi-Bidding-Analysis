import logging

from collect.collect.core.parse import common, errorhandle
from collect.collect.core.parse.result import not_win, win
from collect.collect.utils import debug_stats as stats
from contant import constants

try:
    from .not_win import parse_not_win_bid
    from .win import parse_win_bid
except ImportError:
    # 单个文件DEBUG需要
    from not_win import parse_not_win_bid
    from win import parse_win_bid


__all__ = ["parse_not_win_bid", "parse_win_bid", "SwitchError"]

logger = logging.getLogger(__name__)


@stats.function_stats(logger)
def parse_response_data(data: list):
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

    return result


class SwitchError(Exception):
    """
    切换到另一个结果公告进行搜索
    """

    pass


@stats.function_stats(logger)
def parse_html(html_content: str, is_wid_bid: bool):
    """
    解析 结果公告 中的 content
    :param html_content:
    :param is_wid_bid: 是否为中标结果
    :return:
    """
    result = common.parse_html(html_content=html_content)

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
            # 返回值为 None，表示没有标项解析，需要切换
            if not data:
                raise SwitchError("该结果公告没有解析到标项信息")
            else:
                data.update(project_data)
        else:
            # 废标结果可能没有标项信息，所以暂时不做判断
            data = not_win.parse_not_win_bid(parts)
            data.update(project_data)

        return data
    except SwitchError as e:
        raise e  # 不能被 raise_error所处理，直接抛出
    except BaseException as e:
        errorhandle.raise_error(e, "解析 bid 异常", parts)


if __name__ == "__main__":
    content = "test"

    res = parse_html(content, True)
    print(res)
