import json
import logging
from typing import Union

from collect.collect.core import error
from collect.collect.core.parse import common, errorhandle
from collect.collect.core.parse.result import not_win, win
from collect.collect.middlewares import ParseError
from collect.collect.utils import debug_stats as stats, symbol_tools
from constant import constants

try:
    from .not_win import parse_not_win_bid
    from .win import parse_win_bid
except ImportError:
    # 单个文件DEBUG需要
    from not_win import parse_not_win_bid
    from win import parse_win_bid

__all__ = ["parse_not_win_bid", "parse_win_bid"]

logger = logging.getLogger(__name__)

__ANNOUNCEMENT_TYPE_UNUSEFUL = 1 << 0

__ANNOUNCEMENT_TYPE_WIN = 1 << 1

__ANNOUNCEMENT_TYPE_NOT_WIN = 1 << 2

__ANNOUNCEMENT_TYPE_TERMINATION = 1 << 3


@stats.function_stats(logger)
def parse_response_data(data: list):
    """
    解析列表api响应中的内容
    :param data:
    :return:
    """

    def check_useful_announcement(path_name: str) -> int:
        """
        判断是否是有用的公告
        :param path_name:
        :return: 返回是否为中标、终止、废标
        """
        if path_name in [
            "废标公告",
            "邀请招标资格入围公告",
            "中标（成交）结果公告",
            "中标公告",
            "成交公告",
            "终止公告",
            "公开招标资格入围公告",
        ]:
            if path_name in ["中标公告", "中标（成交）结果公告", "成交公告"]:
                return __ANNOUNCEMENT_TYPE_WIN
            if path_name == "终止公告":
                return __ANNOUNCEMENT_TYPE_TERMINATION

            if path_name == "废标公告":
                return __ANNOUNCEMENT_TYPE_NOT_WIN

            return __ANNOUNCEMENT_TYPE_UNUSEFUL
        else:
            raise ParseError(
                msg=f"出现特殊的的 path_name: {path_name}",
            )

    result = []
    for item in data:
        announcement_type = check_useful_announcement(item["pathName"])
        if announcement_type == __ANNOUNCEMENT_TYPE_UNUSEFUL:
            continue
        if announcement_type == __ANNOUNCEMENT_TYPE_WIN:
            is_win, is_termination = True, False
        elif announcement_type == __ANNOUNCEMENT_TYPE_NOT_WIN:
            is_win, is_termination = False, False
        else:
            is_win, is_termination = False, True

        result_api_meta = {
            # 爬取的时间戳
            constants.KEY_PROJECT_SCRAPE_TIMESTAMP: item["publishDate"],
            # 结果公告的id（可能存在多个）
            constants.KEY_PROJECT_RESULT_ARTICLE_ID: item["articleId"],
            # 发布日期（可能存在多个）
            constants.KEY_PROJECT_RESULT_PUBLISH_DATE: item["publishDate"],
            # 公告发布者
            constants.KEY_PROJECT_AUTHOR: item["author"],
            # 地区编号（可能为空）
            constants.KEY_PROJECT_DISTRICT_CODE: item["districtCode"],
            # 采购物品名称
            constants.KEY_PROJECT_CATALOG: item["gpCatalogName"],
            # 采购方式
            constants.KEY_PROJECT_PROCUREMENT_METHOD: item["procurementMethod"],
            # 开标时间
            constants.KEY_PROJECT_BID_OPENING_TIME: item["bidOpeningTime"],
            # 是否中标
            constants.KEY_PROJECT_IS_WIN_BID: is_win,
            # 是否为终止公告
            constants.KEY_PROJECT_IS_TERMINATION: is_termination,
        }
        result.append(result_api_meta)

    return result


def check_useful_part(is_win: bool, title: str) -> Union[int, None]:
    """
    检查是否包含有用信息的标题
    :param is_win:
    :param title:
    :return:
    """
    print(title)
    # 项目编号部分
    if "项目编号" in title:
        return constants.KEY_PART_PROJECT_CODE

    # 项目编号部分
    if "项目名称" in title:
        return constants.KEY_PART_PROJECT_NAME

    # 评审部分
    if "评审" in title:
        return constants.KEY_PART_REVIEW_EXPERT

    # 联系方式部分
    if "以下方式联系" in title or "联系方式" in title:
        return constants.KEY_PART_CONTACT

    if is_win:
        # 中标结果部分
        if "中标（成交）信息" in title or "中标信息" in title:
            return constants.KEY_PART_WIN_BID
    else:
        # 废标结果部分
        if (("废标" in title or "流标") and ("原因" in title or "理由" in title)) or (
            "采购结果信息" in title
        ):
            return constants.KEY_PART_NOT_WIN_BID
        # 终止原因
        if "终止" in title:
            return constants.KEY_PART_TERMINATION_REASON
    return None


@stats.function_stats(logger)
def parse_html(html_content: str, is_win_bid: bool):
    """
    解析 结果公告 中的 content
    :param html_content:
    :param is_win_bid: 是否为中标结果
    :return:
    """
    result = common.parse_html(html_content=html_content)

    n, idx, parts = len(result), 0, dict[int, list[str]]()
    # chinese_number_index 用于规定顺序，避免某些特殊情况
    project_data, chinese_number_index = dict(), 0
    try:
        while idx < n:
            # 找以 “一、” 这种格式开头的字符串
            index = common.startswith_chinese_number(result[idx])
            if index > chinese_number_index:

                # 存在一种废标情况，标题为 “二、项目废标的原因”，但是文本分开，需要特殊处理
                if not is_win_bid:
                    length = len(result[idx])
                    if length < 9 and index == 2 and result[idx][2:].startswith("项目"):
                        tmp_idx = idx
                        # 往下查找直到长度满足
                        while idx < n and length < 9:
                            idx += 1
                            length += len(result[idx])
                        else:
                            # 拼接
                            result[idx] = "".join(result[tmp_idx : idx + 1])

                # 存在一种情况，“中文数字、”和后面的标题内容分开，也就是 '、' 是最后一个字符
                if result[idx][-1] == "、":
                    result[idx] += result[idx + 1]
                    result.pop(idx + 1)
                    n -= 1

                key_part = check_useful_part(is_win=is_win_bid, title=result[idx])
                # 该部分为所需要的标题信息
                if key_part:
                    chinese_number_index = index

                    # 某些标题可能和后面的内容连成一块，需要分开
                    if sym := symbol_tools.get_symbol(
                        result[idx], (":", "："), raise_error=False
                    ):
                        sym_idx = result[idx].index(sym)
                        # 如果冒号不是最后一个字符
                        if sym_idx < len(result[idx]) - 1:
                            result.insert(idx + 1, result[idx][sym_idx + 1 :])
                            n += 1

                    # 项目编号从 purchase 移动到此处
                    if key_part == constants.KEY_PART_PROJECT_CODE:
                        project_data[constants.KEY_PROJECT_CODE] = result[idx + 1]
                        idx += 2
                        continue

                    # 项目名称从 purchase 移动到此处
                    if key_part == constants.KEY_PART_PROJECT_NAME:
                        project_data[constants.KEY_PROJECT_NAME] = result[idx + 1]
                        idx += 2
                        continue

                    # 开始部分(不记入标题）
                    idx += 1
                    pre = idx
                    while idx < n and (
                        # 单个中文
                        common.translate_zh_to_number(result[idx]) != index + 1
                        and
                        # 不以 ‘中文数字、’ 开头
                        (
                            (zh_idx := common.startswith_chinese_number(result[idx]))
                            == -1
                            and zh_idx != index + 1
                        )
                    ):
                        idx += 1
                    # 将该部分加入
                    parts[key_part] = result[pre:idx]
                else:
                    idx += 1
            else:
                idx += 1
    except BaseException as e:
        errorhandle.raise_error(e, "解析 parts 异常", result)

    try:
        # 成交公告，中标结果
        if is_win_bid:
            data = win.parse_win_bid(parts)
            # 表示没有标项解析，需要切换
            if len(data.get(constants.KEY_PROJECT_BID_ITEMS)) == 0:
                logger.warning(
                    "该结果公告没有爬取到任何标项信息！尝试切换 other_announcements 进行查找！"
                )
                raise error.SwitchError("该结果公告没有解析到标项信息")

            project_data.update(data)

        # 废标结果、终止公告
        else:
            # 废标结果可能没有标项信息，所以不做判断
            data = not_win.parse_not_win_bid(parts)
            project_data.update(data)

        return project_data
    except error.SwitchError as e:
        raise e  # 不能被 raise_error所处理，直接抛出
    except BaseException as e:
        errorhandle.raise_error(e, "解析 bid 异常", content=list(parts.items()))


if __name__ == "__main__":
    content = \
        ""
    res = parse_html(content, False)
    print(json.dumps(res, ensure_ascii=False, indent=4))
