import json
import logging
import urllib.parse
from typing import Any

import scrapy
from scrapy import signals
from scrapy.crawler import Crawler
from scrapy.http import Response
from typing_extensions import Self

from collect.collect.core.api.category import CategoryApi
from collect.collect.core.api.detail import DetailApi
from collect.collect.core.parse import result, purchase, common, raise_error
from collect.collect.core.parse.result import SwitchError
from collect.collect.middlewares import ParseError
from collect.collect.utils import (
    redis_tools as redis,
    time as time_tools,
    debug_stats as stats,
)
from constant import constants

logger = logging.getLogger(__name__)


@stats.function_stats(logger)
def _make_result_request(
    pageNo: int, pageSize: int, callback: callable, dont_filter: bool = False
):
    """
    生成结果列表的请求
    :param pageNo 编号
    :param pageSize 返回列表大小
    :param callback 回调
    :param dont_filter 不过滤该请求
    :return:
    """
    # TODO: 根据redis中的缓存数据进行获取, redis 应该记录数据库中最新的数据
    publish_date_begin = redis.get_latest_announcement_timestamp() or "2020-01-01"
    publish_date_end = redis.parse_timestamp(timestamp=time_tools.now_timestamp())
    # logging.info(f"redis lasting info: publish_date_begin: {publish_date_begin}, publish_date_end: {
    # publish_date_end}")
    return scrapy.Request(
        url=CategoryApi.base_url,
        callback=callback,
        method=CategoryApi.method,
        body=CategoryApi.generate_body(
            pageNo=pageNo,
            pageSize=pageSize,
            categoryCode="ZcyAnnouncement2",
            publishDateBegin="2022-01-01",
            publishDateEnd="2022-01-04",
        ),
        headers={"Content-Type": "application/json;charset=UTF-8"},
        dont_filter=dont_filter,
    )


@stats.function_stats(logger, log_params=True)
def _make_detail_request(articleId: str, callback: callable, meta: dict):
    """
    返回 detail api 的请求
    :param articleId:
    :param callback:
    :param meta:
    :return:
    """
    return scrapy.Request(
        url=DetailApi.get_complete_url(articleId),
        callback=callback,
        method=DetailApi.method,
        meta=meta,
        dont_filter=True,
    )


@stats.function_stats(logger)
def _parse_other_announcements(other_announcements: list, meta: dict):
    """
    解析 announcementLinkDtoList 中的信息，用于保证其他情况的出现时先前的不会漏
    :param other_announcements:
    :return:
    """
    if not other_announcements:
        return

    # 如果已经解析过了，则无需解析，（存在于前一个结果公告不能解析，切换到下一个解析）
    # 第一次解析时，不存在该键
    if meta.get(constants.KEY_DEV_START_RESULT_ARTICLE_ID, None):
        return

    # 所有结果公告
    result_article_ids, result_publish_dates = [], []
    # 所有采购公告
    purchase_article_ids, purchase_publish_dates = [], []
    # 所有其他公告（采购公告备选）
    other_ids, other_publish_dates = [], []

    # 计算招标持续时间（最后的合同公告时间 - 最开始的招标时间）
    min_publish_date, max_publish_date = time_tools.now_timestamp(), -1

    other_announcements.sort(key=lambda x: x["order"])

    for item in other_announcements:
        if not item["isExist"]:
            continue

        # 统计时间
        publish_date = item["publishDateTime"]
        min_publish_date = min(min_publish_date, publish_date)
        max_publish_date = max(max_publish_date, publish_date)

        type_name = item["typeName"]
        # 采购公告
        if "采购" in type_name:
            purchase_article_ids.append(item["articleId"])
            purchase_publish_dates.append(publish_date)
        # 结果公告
        elif "结果" in type_name:
            result_article_ids.append(item["articleId"])
            result_publish_dates.append(publish_date)
        # 其他公告
        elif "其他" in type_name:
            other_ids.append(item["articleId"])
            other_publish_dates.append(publish_date)

    # 如果没有采购公告，则使用其他公告
    if len(purchase_article_ids) == 0:
        if len(other_ids) != 0:
            purchase_article_ids.extend(other_ids)
            purchase_publish_dates.extend(other_publish_dates)
        else:
            # 存在没有 “采购公告” 的情况
            logger.warning(
                f"解析其他公告时未发现采购公告相关信息: other_announcements: {other_announcements}"
            )

    # 拿到当前的结果公告
    current_result_id = meta[constants.KEY_PROJECT_RESULT_ARTICLE_ID]

    meta[constants.KEY_PROJECT_RESULT_ARTICLE_ID] = result_article_ids
    meta[constants.KEY_PROJECT_RESULT_PUBLISH_DATE] = result_publish_dates

    meta[constants.KEY_PROJECT_PURCHASE_ARTICLE_ID] = purchase_article_ids
    meta[constants.KEY_PROJECT_PURCHASE_PUBLISH_DATE] = purchase_publish_dates

    # 标记该公告机已经解析
    parsed_result_id = 1 << result_article_ids.index(current_result_id)
    meta[constants.KEY_DEV_PARRED_RESULT_ARTICLE_ID] = parsed_result_id
    # 从现在开始
    meta[constants.KEY_DEV_START_RESULT_ARTICLE_ID] = current_result_id

    # 计算招标持续时间
    if max_publish_date - min_publish_date <= 0:
        raise ParseError(
            msg=f"解析 other_announcement 时出现异常, duration计算为 {max_publish_date - min_publish_date}",
            content=other_announcements.extend(
                [
                    f"min_publish_date: {min_publish_date}",
                    f"max_publish_date: {max_publish_date}",
                ]
            ),
        )
    meta[constants.KEY_PROJECT_TENDER_DURATION] = max_publish_date - min_publish_date


class BiddingSpider(scrapy.Spider):
    name = "bidding"

    @classmethod
    def from_crawler(cls, crawler: Crawler, *args: Any, **kwargs: Any) -> Self:
        obj = cls(*args, **kwargs)
        obj._set_crawler(crawler)
        crawler.signals.connect(obj.spider_closed, signal=signals.spider_closed)
        return obj

    def spider_closed(self):
        stats.log_stats_collector()

    # ========== use for debug ================

    special_article_ids = [
        # template: ("article_id", is_win: bool)
        # ("U4nmS6%2BttFXSjN5otQ77OA%3D%3D", True),  # 存在多个采购公告和结果公告的
        # ("4ove6DOhBSozWjPJ3AxxUg==", False),
        # ("tzq4L6CLqRPYu%2BudtPsf0Q%3D%3D", False),  # 评审专家部分为 '/'
        # ("lFwU0xqj/0siwuKKdvc0dw==", True),  # 没有解析到正常的结果公告，
        # ("NtUNOAS3ZpBxTZ7Y%2BnqDaA%3D%3D", True),  # 同上
        # ("anWmVy9QDIfWu/MveFjsbQ==", True),
        # ("tzq4L6CLqRPYu+udtPsf0Q==", False),  # 解析联系方式存在问题
        ("1jfaoapjjKBCOlDpMP2%2Bwg%3D%3D", True),  # 解析评审专家存在问题
        (
            "Ahi640Zu0NORfgNMr7Aswg%3D%3D",
            False,
        ),  # 解析结果公告异常（说不存在，但是存在）
    ]

    #  =========================================

    def start_requests(self):
        """
        1. 先请求些数据，通过返回的数据中的 total 字段来控制请求数量
        :return:
        """
        # 调试有问题的 article_id
        if len(self.special_article_ids) > 0:
            logger.warning(
                f"Start Special Requests, total {len(self.special_article_ids)}"
            )
            for article_id, is_win in self.special_article_ids:
                logger.warning(f"Special Article: {article_id}")
                yield _make_detail_request(
                    articleId=urllib.parse.unquote(article_id),
                    callback=self.parse_result_detail_content,
                    meta={
                        constants.KEY_PROJECT_RESULT_ARTICLE_ID: urllib.parse.unquote(
                            article_id
                        ),
                        constants.KEY_PROJECT_IS_WIN_BID: is_win,
                    },
                )
        else:
            # 正常爬取
            yield _make_result_request(
                pageNo=1,
                pageSize=1,
                callback=self.parse_result_amount,
                dont_filter=True,
            )

    @stats.function_stats(logger)
    def parse_result_amount(self, response: Response):
        """
        2. 用于解析 结果公告列表中的 total 字段，用于确定需要爬取多少公告数量
        :param response:
        :return:
        """
        data = json.loads(response.text)
        success = data["success"]
        if success:
            total = int(data["result"]["data"]["total"])
            self.logger.debug(f"initial fetch amount: {total}")
            for i in range(1, total // 100 + 2):
                yield _make_result_request(
                    pageNo=i,
                    pageSize=100,
                    callback=self.parse_result_data,
                    dont_filter=True,
                )
        else:
            # TODO: 加入 retry 功能
            self.logger.error(f"response not success: {response.text}")

    @stats.function_stats(logger)
    def parse_result_data(self, response: Response):
        """
        3. 用于解析 结果公告列表中的数据
        :param response:
        :return:
        """
        response_body = json.loads(response.text)
        if response_body.get("success", False):
            response_data = response_body["result"]["data"]
            # 该数据为一个列表
            data: list = response_data["data"]
            # 对于列表中的每个公告数据，都拿到所需要的数据 meta，进而生成对应的请求
            for meta in result.parse_response_data(data):
                yield _make_detail_request(
                    articleId=meta[constants.KEY_PROJECT_RESULT_ARTICLE_ID],
                    callback=self.parse_result_detail_content,
                    meta=meta,
                )
        else:
            # TODO: 加入 retry 功能
            self.logger.error(f"result response not success: {response.text}")

    @stats.function_stats(logger)
    def parse_result_detail_content(self, response: Response):
        """
        4. 解析 结果公告 的详情
        :param response:
        :return:
        """
        response_body = json.loads(response.text)
        if response_body.get("success", False):
            meta: dict = response.meta
            data: dict = response_body["result"]["data"]

            # 解析 html 结果
            try:
                if data:
                    meta[constants.KEY_PROJECT_CODE] = data["projectCode"]
                    meta[constants.KEY_PROJECT_NAME] = data["projectName"]
                    meta[constants.KEY_PROJECT_IS_GOVERNMENT_PURCHASE] = data[
                        "isGovPurchase"
                    ]
                    if constants.KEY_PROJECT_DISTRICT_CODE not in meta:
                        meta[constants.KEY_PROJECT_DISTRICT_CODE] = data["districtCode"]

                    # 解析其他公告
                    _parse_other_announcements(
                        other_announcements=data["announcementLinkDtoList"], meta=meta
                    )

                    meta.update(
                        result.parse_html(
                            html_content=data["content"],
                            is_win_bid=meta[constants.KEY_PROJECT_IS_WIN_BID],
                        )
                    )
                else:
                    raise SwitchError("该结果公告没有任何返回数据")
            except SwitchError:
                # 当前结果公告不好使，换一个
                yield self.switch_other_result_announcement(meta=meta)
                return
            else:
                # 没有出现 SwitchError 则解析采购公告
                purchase_article_ids = meta[constants.KEY_PROJECT_PURCHASE_ARTICLE_ID]
                if len(purchase_article_ids) == 0:
                    # 没有 “采购公告”，直接进入 make_item 生成 item
                    try:
                        yield common.make_item(data=meta, purchase_data=None)
                    except BaseException as e:
                        raise_error(
                            e,
                            "生成 item 时出现异常",
                            content=[json.dumps(meta, ensure_ascii=False, indent=4)],
                        )
                else:
                    # 存在 “采购公告”
                    yield _make_detail_request(
                        articleId=purchase_article_ids[0],
                        callback=self.parse_purchase,
                        meta=meta,
                    )
        else:
            # TODO: 加入 retry 功能
            self.logger.error(f"result response not success: {response.text}")

    @stats.function_stats(logger, log_params=True)
    def switch_other_result_announcement(self, meta: dict):
        """
        切换其他结果公告
        :param meta:
        :return:
        """

        # 已经解析的列表
        result_ids = meta[constants.KEY_PROJECT_RESULT_ARTICLE_ID]
        if not isinstance(result_ids, list):
            raise ParseError(
                msg="switch_other_announcement 存在异常，未解析 result_ids 为 list",
                content=[result_ids],
            )
        # 前一个公告id
        parsed_result_id: int = meta[constants.KEY_DEV_PARRED_RESULT_ARTICLE_ID]
        # 最开始的结果公告
        start_result_id = meta[constants.KEY_DEV_START_RESULT_ARTICLE_ID]
        # 下一个需要切换的结果公告id
        next_result_id, next_idx = None, -1
        m = len(result_ids)
        # 使用位运算找到还没解析的结果公告
        for i in range(m):
            if (parsed_result_id >> i) & 1 == 0:
                next_result_id = result_ids[i]
                next_idx = i
                break

        # 如果和起点一样，则查找逻辑存在问题，需要修改
        if next_result_id and next_result_id == start_result_id:
            raise ParseError(
                msg="遍历结果公告逻辑错误，请检查",
                content=[f"parsed_article_id: {bin(parsed_result_id)[2:]}"].extend(
                    result_ids
                ),
            )

        if next_result_id:
            # 切换到下一个结果公告
            logger.warning(f"已经切换到 {next_result_id} 结果公告进行爬取")
            # 标记该结果已经解析了
            parsed_result_id |= 1 << next_idx
            meta[constants.KEY_DEV_PARRED_RESULT_ARTICLE_ID] = parsed_result_id
            return _make_detail_request(
                articleId=next_result_id,
                callback=self.parse_result_detail_content,
                meta=meta,
            )
        else:
            raise ParseError(
                msg="不存在其他的结果公告可以解析",
                content=[f"parsed_article_id: {bin(parsed_result_id)[2:]}"].extend(
                    result_ids
                ),
            )

    @stats.function_stats(logger)
    def parse_purchase(self, response: Response):
        """
        5. 解析采购公告，最后的步骤
        :param response:
        :return:
        """
        response_body = json.loads(response.text)
        if response_body.get("success", False):
            data = response_body["result"]["data"]
            meta = response.meta

            # TODO: 可能存在多个采购公告，考虑 SwitchError
            # 更新 html 内容
            purchase_data = purchase.parse_html(html_content=data["content"])

            try:
                yield common.make_item(data=meta, purchase_data=purchase_data)
            except BaseException as e:
                raise_error(
                    e,
                    "生成 item 时出现异常",
                    content=[
                        json.dumps(meta, ensure_ascii=False, indent=4),
                        "------- split line ----------------",
                        json.dumps(purchase_data, ensure_ascii=False, indent=4),
                    ],
                )
        else:
            # TODO: 加入 retry 功能
            self.logger.error(f"purchase response not success: {response.text}")


if __name__ == "__main__":
    print("请启动 main-collecting.py 文件，而不是本文件！")
