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
from collect.collect.core.error import SwitchError
from collect.collect.core.parse import result, purchase, common
from collect.collect.core.parse.result import errorhandle
from collect.collect.middlewares import ParseError
from collect.collect.utils import (
    redis_tools as redis,
    time as time_tools,
    debug_stats as stats,
)
from constant import constants

logger = logging.getLogger(__name__)


def get_articleId_from_url(url: str) -> str:
    """
    从 url 中解析出 articleId
    :param url:
    :return:
    """
    params = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
    return params["articleId"][0]


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
            publishDateEnd="2022-01-31",
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
    tender_duration = time_tools.now_timestamp() - min_publish_date
    if tender_duration <= 0:
        raise ParseError(
            msg=f"解析 other_announcement 时出现异常, duration计算为 {tender_duration}",
            content=[
                other_announcements,
                [
                    f"min_publish_date: {min_publish_date}",
                    f"max_publish_date: {max_publish_date}",
                ],
            ],
        )
    meta[constants.KEY_PROJECT_TENDER_DURATION] = tender_duration


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
        # ("rr91aR+tRtF6REnhbSWTDw==", False),  # 废标理由共用
        # ("NdzojgV6OhU9W3SqCK65nQ==", True),  # 评审专家粘连+无表格的中标信息
        # ("IwcucEsf2aZ4tbS2VN2GGQ==", True),  # 废标理由存在新的格式:标项2投标供应商数量不符合要求,系统自动废标
        # ("2wbHrTckeSdD9gz4WZrPgg==", True),  # 奇葩的金额
        # ("ZojeS8Mufd1qJwHuJAaIbw==", False),  # 新的废标理由
        # ("IvqpsDUCGqo0HqzuGSkTCg==", False),  # 奇怪的废标理由
        # ("kvpgcrvQp13GWXtT8xfZLQ==", True),  # 奇怪的金额
        # ("1YGqWSb+yZPgy8AryGbEwQ==", True),  # 无表格的中标信息
        # ("iHyii/GCTMIcxcVU4diMrQ==", False),  # 采购信息新的
        # ("8lnjOLrOkz9DSUdnjPZfqA==", False),  # 废标理由共用
        # ("HKor1SEeN02slN/XvtayYg==", False),  # 看是废标实际上是终止
        # ("Sfb/HdmkZ9wKtTvcGOIfjQ==", False),  # 需要切换采购公告
        # ("6OPa2XaYAImxu/6nudSv+g==", True),  # 需要切换采购公告
        # ==================== 最近的 ========================
        # ("NtUNOAS3ZpBxTZ7Y%2BnqDaA%3D%3D", True),  # 死循环
        # ("bzHfq7PCKWTHrBHufwfWIQ%3D%3D", True),  # 采购公告存在isExist为True但是api返回的data为None
        # ("Aqick03HkvP6p/zD8IHU6A==", True),  # 出现新的标项序号
        # ("OyDFIFvfxl6BjoGP8klhJQ==", True),  # 出现新的金额格式  单项合价（元） ③＝①×②/费率:650000(元) *2
        # ("4y99t6bWQoaIdhPnt313QQ==", True),  # 出现新的金额格式   每年可行性缺口补助:530000000(元)
        # ("2ST2nVcVaFIlY4NIeie27g==", True),  # 出现新的中标格式： 中标金额
        # ("R99B3UWFEqrLF/tksnsgqw==", True), # 出现新的金额格式  价格:13185000(元)
        # ("QAI+LyiIc1LYJjpYA0omCA==", False),  # 废标理由共用
        ("JfuMrotn+DZtCSb9lr5l8w==", True),  # 采购标项出现错误

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
                    # TODO: 判断是否为中标候选人公示，后期完善
                    title = data["title"]
                    if title and ("中标候选人" in title):
                        meta[constants.KEY_DEV_RESULT_CONTAINS_CANDIDATE] = True

                    if constants.KEY_PROJECT_DISTRICT_CODE not in meta:
                        meta[constants.KEY_PROJECT_DISTRICT_CODE] = data["districtCode"]

                    # 解析其他公告
                    _parse_other_announcements(
                        other_announcements=data["announcementLinkDtoList"], meta=meta
                    )

                    # 判断是否为所需要的结果公告
                    if common.check_unuseful_announcement(data["announcementType"]):
                        raise SwitchError("该结果公告并非所需要的")

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
                        errorhandle.raise_error(
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
                content=["error result_ids", result_ids],
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
                content=[
                    f"parsed_article_id: {bin(parsed_result_id)[2:]}",
                    *result_ids,
                ],
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
                content=[
                    f"parsed_article_id: {bin(parsed_result_id)[2:]}",
                    *result_ids,
                ],
            )

    @stats.function_stats(logger)
    def switch_other_purchase_announcement(self, meta: dict):
        """
        切换其他采购公告
        :param meta:
        :return:
        """
        parsed: int = meta[constants.KEY_DEV_PARRED_PURCHASE_ARTICLE_ID]
        purchase_ids = meta[constants.KEY_PROJECT_PURCHASE_ARTICLE_ID]
        for i in range(len(purchase_ids)):
            if ((parsed >> i) & 1) == 0:
                return _make_detail_request(
                    articleId=purchase_ids[i], callback=self.parse_purchase, meta=meta
                )
        else:
            parsed += 1
            if (parsed & (-parsed)) != parsed:
                raise ParseError(
                    msg="采购公告存在逻辑问题",
                    content=[bin(parsed)[2:]] + purchase_ids
                )
            logger.warning(f"采购公告 {purchase_ids} 没有解析到任何标项信息， 直接生成 item")
            return common.make_item(data=meta, purchase_data=None)

    @stats.function_stats(logger)
    def parse_purchase(self, response: Response):
        """
        5. 解析采购公告，最后的步骤
        :param response:
        :return:
        """
        response_body = json.loads(response.text)
        if response_body.get("success", False):
            meta: dict = response.meta
            data: dict = response_body["result"]["data"]

            purchase_data = {}

            try:
                # 首先判断是不是第一次解析采购公告
                if constants.KEY_DEV_START_PURCHASE_ARTICLE_ID not in meta:
                    # 当前公告id
                    current_id = get_articleId_from_url(response.url)
                    meta[constants.KEY_DEV_START_PURCHASE_ARTICLE_ID] = current_id
                    # 定位解析位置
                    purchase_ids: list = meta[constants.KEY_DEV_START_PURCHASE_ARTICLE_ID]
                    index = purchase_ids.index(current_id)
                    parsed = 1 << index
                    # 标记当前位置
                    meta[constants.KEY_DEV_PARRED_PURCHASE_ARTICLE_ID] = parsed
                else:
                    # 当前公告id
                    current_id = get_articleId_from_url(response.url)
                    parsed = meta[constants.KEY_DEV_PARRED_PURCHASE_ARTICLE_ID]
                    purchase_ids = meta[constants.KEY_PROJECT_PURCHASE_ARTICLE_ID]
                    index = purchase_ids.index(current_id)
                    parsed |= 1 << index
                    meta[constants.KEY_DEV_PARRED_PURCHASE_ARTICLE_ID] = parsed

                # 某些文章id返回的数据为None，需要预选处理
                if data is None:
                    logger.warning(f"请注意 {meta[constants.KEY_PROJECT_PURCHASE_ARTICLE_ID]} 中存在data为None的 id")
                    yield self.switch_other_purchase_announcement
                    return
                else:
                    # 在 2022 前的发布的公告大多格式不统一，直接切换
                    if data['publishDate'] < 1640966400000:
                        logger.warning(f"该公告 {get_articleId_from_url(response.url)} 在2022年前发布")
                        yield self.switch_other_purchase_announcement
                        return

                # 更新 html 内容
                purchase_data = purchase.parse_html(html_content=data["content"])

                # 生成 item
                yield common.make_item(data=meta, purchase_data=purchase_data)
            except SwitchError:
                logger.warning("采购公告没有标项信息")
                yield self.switch_other_purchase_announcement(meta=meta)
                return
            except BaseException as e:
                errorhandle.raise_error(
                    e,
                    "生成 item 时出现异常",
                    content=[
                        "result_data",
                        list(data.items()),
                        "------- split line ----------------",
                        "purchase_data",
                        list(purchase_data.items()),
                    ],
                )
        else:
            self.logger.error(f"purchase response not success: {response.text}")


if __name__ == "__main__":
    print("请启动 main-collecting.py 文件，而不是本文件！")
