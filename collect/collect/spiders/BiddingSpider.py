import json
import logging
import urllib.parse
from typing import Union, Any

from scrapy import signals
from typing_extensions import Self

import scrapy
from scrapy.crawler import Crawler
from scrapy.http import Response

from collect.collect.core.api.category import CategoryApi
from collect.collect.core.api.detail import DetailApi
from collect.collect.core.parse import result, purchase
from collect.collect.core.parse.result import SwitchError
from collect.collect.middlewares import ParseError
from collect.collect.utils import (
    redis_tools as redis,
    time as time_tools,
    log,
    debug_stats as stats,
)
from contant import constants

logger = logging.getLogger(__name__)


@stats.function_stats(logger, log_params=True)
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
    )


@stats.function_stats(logger)
def _parse_other_announcements(other_announcements):
    """
    解析 announcementLinkDtoList 中的信息，得到采购公告的 articleId
    :param other_announcements:
    :return:
    """

    if not other_announcements:
        return None

    # 过滤出存在且非当前结果公告的公告信息
    exist_other_announcements = sorted(
        [
            item
            for item in other_announcements
            if item.get("isExist", False) and (not item.get("isCurrent", False))
        ],
        key=lambda item: item["order"],
        reverse=True,
    )
    # 找出 采购公告
    for item in exist_other_announcements:
        if item["typeName"] == "采购公告":
            return item["articleId"]

    # 也有可能是 “其他公告”
    for item in exist_other_announcements:
        if item["typeName"] == "其他公告":
            return item["articleId"]

    # 存在没有 “采购公告” 的情况
    logger.warning(
        f"解析其他公告时未发现采购公告相关信息: other_announcements: {other_announcements}"
    )
    return None


@stats.function_stats(logger)
def _merge_bid_items(_purchase: list, _result: list) -> list:
    """
    将两部分的标项信息合并
    :param _purchase:
    :param _result:
    :return:
    """
    _purchase.sort(key=lambda x: x[constants.KEY_BID_ITEM_INDEX])
    _result.sort(key=lambda x: x[constants.KEY_BID_ITEM_INDEX])

    n, m = len(_purchase), len(_result)
    if n != m:
        raise ParseError(
            msg="标项数量不一致",
            content=[f"purchase length: {n}, result length: {m}", _purchase, _result],
        )

    for idx in range(n):
        purchase_item = _purchase[idx]
        result_item = _result[idx]
        result_item[constants.KEY_BID_ITEM_NAME] = purchase_item[
            constants.KEY_BID_ITEM_NAME
        ]
        result_item[constants.KEY_BID_ITEM_QUANTITY] = purchase_item[
            constants.KEY_BID_ITEM_QUANTITY
        ]
        result_item[constants.KEY_BID_ITEM_BUDGET] = purchase_item[
            constants.KEY_BID_ITEM_BUDGET
        ]
    return _result


@stats.function_stats(logger)
def make_item(data: dict, purchase_data: Union[dict, None]):
    """
    将 data 所需要的内容提取出来
    :param purchase_data:
    :param data:
    :return:
    """
    if purchase_data:
        # 合并标项
        purchase_bid_items = purchase_data.pop(constants.KEY_PROJECT_BID_ITEMS, [])
        result_bid_items = data.get(constants.KEY_PROJECT_BID_ITEMS, [])
        data[constants.KEY_PROJECT_BID_ITEMS] = _merge_bid_items(
            _purchase=purchase_bid_items, _result=result_bid_items
        )
        # 项目编号和名称，以 api 返回为准，如果没有则用解析出来的补充
        project_name = purchase_data.pop(constants.KEY_PROJECT_NAME, None)
        project_code = purchase_data.pop(constants.KEY_PROJECT_CODE, None)
        if not data.get(constants.KEY_PROJECT_NAME, None):
            data[constants.KEY_PROJECT_NAME] = project_name
        if not data.get(constants.KEY_PROJECT_CODE, None):
            data[constants.KEY_PROJECT_CODE] = project_code

        # 其他内容信息直接合并
        data.update(purchase_data)

    # 从 data 中取出所需要的信息
    item = dict()
    item[constants.KEY_PROJECT_NAME] = data.get(constants.KEY_PROJECT_NAME, None)
    item[constants.KEY_PROJECT_CODE] = data.get(constants.KEY_PROJECT_CODE, None)
    item[constants.KEY_PROJECT_DISTRICT_NAME] = data.get(
        constants.KEY_PROJECT_DISTRICT_NAME, None
    )
    item[constants.KEY_PROJECT_DISTRICT_CODE] = data.get(
        constants.KEY_PROJECT_DISTRICT_CODE, None
    )
    item[constants.KEY_PROJECT_CATALOG] = data.get(constants.KEY_PROJECT_CATALOG, None)
    item[constants.KEY_PROJECT_PROCUREMENT_METHOD] = data.get(
        constants.KEY_PROJECT_PROCUREMENT_METHOD, None
    )
    item[constants.KEY_PROJECT_BID_OPENING_TIME] = data.get(
        constants.KEY_PROJECT_BID_OPENING_TIME, None
    )
    item[constants.KEY_PROJECT_IS_WIN_BID] = data.get(
        constants.KEY_PROJECT_IS_WIN_BID, None
    )
    item[constants.KEY_PROJECT_RESULT_ARTICLE_ID] = data.get(
        constants.KEY_PROJECT_RESULT_ARTICLE_ID, None
    )
    item[constants.KEY_PROJECT_RESULT_PUBLISH_DATE] = data.get(
        constants.KEY_PROJECT_RESULT_PUBLISH_DATE, None
    )
    item[constants.KEY_PROJECT_IS_GOVERNMENT_PURCHASE] = data.get(
        constants.KEY_PROJECT_IS_GOVERNMENT_PURCHASE, None
    )
    item[constants.KEY_PROJECT_PURCHASE_ARTICLE_ID] = data.get(
        constants.KEY_PROJECT_PURCHASE_ARTICLE_ID, None
    )
    item[constants.KEY_PROJECT_PURCHASE_PUBLISH_DATE] = data.get(
        constants.KEY_PROJECT_PURCHASE_PUBLISH_DATE, None
    )
    item[constants.KEY_PROJECT_TOTAL_BUDGET] = data.get(
        constants.KEY_PROJECT_TOTAL_BUDGET, None
    )
    item[constants.KEY_PROJECT_BID_ITEMS] = data.get(
        constants.KEY_PROJECT_BID_ITEMS, None
    )
    item[constants.KEY_PURCHASER_INFORMATION] = data.get(
        constants.KEY_PURCHASER_INFORMATION, None
    )
    item[constants.KEY_PURCHASER_AGENCY_INFORMATION] = data.get(
        constants.KEY_PURCHASER_AGENCY_INFORMATION, None
    )
    item[constants.KEY_PROJECT_REVIEW_EXPERT] = data.get(
        constants.KEY_PROJECT_REVIEW_EXPERT, []
    )
    return item


class BiddingSpider(scrapy.Spider):
    name = "bidding"

    @classmethod
    def from_crawler(cls, crawler: Crawler, *args: Any, **kwargs: Any) -> Self:
        obj = cls()
        crawler.signals.connect(obj.spider_closed, signal=signals.spider_closed)
        return obj

    def spider_closed(self):
        stats.log_stats_collector()

    # ========== use for debug ================
    special_article_ids = [
        # template: ("article_id", is_win: bool)
        ("/VzMNpuL7TfpTeW1j2JlvQ%3D%3D", True)
    ]

    #  =========================================

    def start_requests(self):
        """
        1. 先请求些数据，通过返回的数据中的 total 字段来控制请求数量
        :return:
        """
        if len(self.special_article_ids) > 0:
            # 调试有问题的 article_id
            logger.warning(f"Start Special Requests, total {len(self.special_article_ids)}")
            for article_id, is_win in self.special_article_ids:
                logger.warning(f"Special Article: {article_id}")
                yield _make_detail_request(
                    articleId=urllib.parse.unquote(article_id),
                    callback=self.parse_result_detail_content,
                    meta={
                        constants.KEY_PROJECT_IS_WIN_BID: is_win
                    },
                )
        else:
            yield _make_result_request(
                pageNo=1, pageSize=1, callback=self.parse_result_amount, dont_filter=True
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
                    pageNo=i, pageSize=100, callback=self.parse_result_data
                )
        else:
            # TODO: 加入 retry 功能
            self.logger.error(f"response not success: {response.text}")
            pass

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

            meta[constants.KEY_PROJECT_CODE] = data["projectCode"]
            meta[constants.KEY_PROJECT_NAME] = data["projectName"]
            meta[constants.KEY_PROJECT_IS_GOVERNMENT_PURCHASE] = data["isGovPurchase"]
            meta[constants.KEY_PROJECT_RESULT_PUBLISH_DATE] = data["publishDate"]

            # 解析 html 结果
            try:
                meta.update(
                    result.parse_html(
                        html_content=data["content"],
                        is_wid_bid=meta[constants.KEY_PROJECT_IS_WIN_BID],
                    )
                )
            except SwitchError:
                # 当前结果公告不好使，换一个
                if stats.debug_status():
                    logger.debug(
                        f"DEBUG INFO: {log.get_function_name()} switch other result announcement"
                    )
                yield self.switch_other_result_announcement(
                    other_announcements=data["announcementLinkDtoList"], meta=meta
                )

            # 解析其他公告的结果
            purchase_article_id = _parse_other_announcements(
                other_announcements=data["announcementLinkDtoList"]
            )

            # 存在 “采购公告”
            if purchase_article_id:
                yield _make_detail_request(
                    articleId=purchase_article_id,
                    callback=self.parse_purchase,
                    meta=meta,
                )
            else:
                # 没有 “采购公告”，直接进入 make_item 生成 item
                yield make_item(data=meta, purchase_data=None)
        else:
            # TODO: 加入 retry 功能
            self.logger.error(f"result response not success: {response.text}")

    @stats.function_stats(logger)
    def switch_other_result_announcement(self, other_announcements, meta):
        """
        切换其他结果公告
        :param meta:
        :param other_announcements:
        :return:
        """
        # 对 order 进行排序，取order最大的
        other_result = sorted(
            # 过滤出所有结果公告
            [
                item
                for item in other_announcements
                if (item["typeName"] == "结果公告")
                   and (not item["isCurrent"])
                   and item["isExist"]
            ],
            key=lambda item: item["order"],
            reverse=True,
        )

        if len(other_result) == 0:
            raise ParseError(msg="不存在其他的结果公告可以解析")

        return _make_detail_request(
            articleId=other_result[0]["articleId"],
            callback=self.parse_result_detail_content,
            meta=meta,
        )

    @stats.function_stats(logger)
    def parse_purchase(self, response: Response):
        """
        解析采购公告，最后的步骤
        :param response:
        :return:
        """
        response_body = json.loads(response.text)
        if response_body.get("success", False):
            data = response_body["result"]["data"]
            meta = response.meta
            # 采购公告id
            meta[constants.KEY_PROJECT_PURCHASE_ARTICLE_ID] = data["articleId"]
            meta[constants.KEY_PROJECT_PURCHASE_PUBLISH_DATE] = data["publishDate"]

            # 更新 html 内容
            purchase_data = purchase.parse_html(html_content=data["content"])

            # TODO: 处理标项等信息百分比
            yield make_item(meta, purchase_data)
        else:
            # TODO: 加入 retry 功能
            self.logger.error(f"purchase response not success: {response.text}")


if __name__ == '__main__':
    print("请启动 main-collecting.py 文件，而不是本文件！")
