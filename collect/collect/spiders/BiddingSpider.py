import json

import scrapy
from scrapy import Request
from scrapy.http import Response

from collect.collect.core.api.category import CategoryApi
from collect.collect.core.api.detail import DetailApi
from contant import constants
from collect.collect.items import DataItem
from collect.collect.middlewares import ParseError
from collect.collect.utils import log
from collect.collect.core.parse import result, purchase


def parse_purchase_content_html(content) -> dict:
    """
    解析 采购公告 中的 content
    :param content:
    :return:
    """
    # impl delegate to parse.purchase
    return purchase.parse_html(content)


def parse_result_content_html(content, is_win_bid: bool):
    """
    解析 结果公告 中的 content
    :param is_win_bid:
    :param content:
    :return:
    """
    # impl delegate to parse.result
    return result.parse_html(content, is_win_bid)


class BiddingSpider(scrapy.Spider):
    name = "bidding"

    @staticmethod
    def make_result_request(
            pageNo: int,
            pageSize: int,
            callback: callable,
            dont_filter: bool = False
    ):
        """
        生成结果列表的请求
        :return:
        """
        return scrapy.Request(
            url=CategoryApi.base_url,
            callback=callback,
            method=CategoryApi.method,
            # TODO: 根据redis中的缓存数据进行获取, redis 应该记录数据库中最新的数据
            body=CategoryApi.generate_body(
                pageNo,
                pageSize,
                "ZcyAnnouncement2",
                "2022-01-01",
                "2022-01-02"
            ),
            headers={
                "Content-Type": "application/json;charset=UTF-8"
            },
            dont_filter=dont_filter
        )

    @staticmethod
    def make_detail_request(
            articleId: str,
            callback: callable,
            meta: dict
    ):
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
            meta=meta
        )

    def start_requests(self):
        """
        1. 先请求些数据，通过返回的数据中的 total 字段来控制请求数量
        :return:
        """
        yield self.make_result_request(
            1,
            1,
            self.parse_result_amount,
            dont_filter=True
        )

    def parse_result_amount(self, response: Response):
        """
        2. 用于解析 结果公告列表中的 total 字段
        :param response:
        :return:
        """
        data = json.loads(response.text)
        success = data["success"]
        self.logger.info(f'fetch amount success: {success}')
        if success:
            total = int(data['result']['data']['total'])
            self.logger.info(f'initial fetch amount: {total}')
            for i in range(1, total // 100 + 2):
                yield self.make_result_request(
                    pageNo=i,
                    pageSize=100,
                    callback=self.parse_result_data
                )
        else:
            # TODO: 加入 retry 功能
            pass

    def parse_result_data(self, response: Response):
        """
        3. 用于解析 结果公告列表中的数据
        :param response:
        :return:
        """
        response_body = json.loads(response.text)
        if response_body.get('success', False):
            response_data = response_body['result']['data']
            data: list = response_data['data']  # 该数据为一个列表
            for meta in result.parse_response_data(data):
                log.log_json(self.log, meta)
                yield self.make_detail_request(
                    articleId=meta[constants.KEY_PROJECT_RESULT_ARTICLE_ID],
                    callback=self.parse_result_detail_content,
                    meta=meta,
                )
        else:
            # TODO: 加入 retry 功能
            pass

    def parse_result_detail_content(self, response: Response):
        """
        解析 结果公告 的详情
        :param response:
        :return:
        """
        response_body = json.loads(response.text)
        if response_body.get('success', False):
            meta = response.meta
            data = response_body['result']['data']

            meta[constants.KEY_PROJECT_CODE] = data['projectCode']
            meta[constants.KEY_PROJECT_NAME] = data['projectName']
            meta[constants.KEY_PROJECT_IS_GOVERNMENT_PURCHASE] = data['isGovPurchase']

            # 解析 html 结果
            result_data = parse_result_content_html(
                content=data['content'],
                is_win_bid=meta['is_win_bid']
            )
            meta.update(result_data)

            # 解析其他公告的结果
            other_announcements = data['announcementLinkDtoList']
            purchase_article_id = self.parse_other_announcements(other_announcements)
            yield self.make_detail_request(
                articleId=purchase_article_id,
                callback=self.parse_purchase,
                meta=meta
            )
        else:
            # TODO: 加入 retry 功能
            pass

    def parse_other_announcements(self, other_announcements):
        """
        解析 announcementLinkDtoList 中的信息
        :param other_announcements:
        :return:
        """
        if len(other_announcements) > 0:
            for item in other_announcements:
                typeName = item['typeName']
                isExist = item['isExist']
                # 一般是 采购公告 存在
                if typeName == '采购公告' and isExist:
                    return item['articleId']

            # 也有可能 采购公告 是 存在于 “其他公告”
            filtered = [item for item in other_announcements if item['typeName'] == '其他公告' and item['isExist']]
            if len(filtered) > 0:
                return filtered[0]['articleId']
            else:
                # TODO 可能存在其他情况
                raise ParseError(
                    msg="解析其他公告时未发现采购公告相关信息\n",
                    content=json.dumps(other_announcements, indent=4, ensure_ascii=False),
                )

        return None

    def parse_purchase(self, response: Response):
        """
        解析采购公告，最后的步骤
        :param response:
        :return:
        """
        response_body = json.loads(response.text)
        if response_body.get('success', False):
            data = response_body['result']['data']

            meta = response.meta
            # 采购公告id
            meta[constants.KEY_PROJECT_PURCHASE_ARTICLE_ID] = data['articleId']
            meta[constants.KEY_PROJECT_PURCHASE_PUBLISH_DATE] = data['publishDate']
            # html 内容
            detail_data = parse_purchase_content_html(content=data['content'])
            # 更新
            # TODO: 处理标项等信息百分比
            meta.update(detail_data)
            yield self.make_item(meta)
        else:
            # TODO: 加入 retry 功能
            pass

    def make_item(self, data: dict):
        pass
        item = DataItem()
        item['project_name'] = data['project_name']
        item['project_code'] = data['project_code']
        item['procurement_method'] = data['procurement_method']
        item['budget'] = data['budget']
        item['bid_opening_time'] = data['']
        item['district_code'] = data['']
        item['district_name'] = data['']

        return item

    def retry(self, request: Request):
        pass
