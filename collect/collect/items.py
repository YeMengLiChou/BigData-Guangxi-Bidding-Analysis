# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class DataItem(scrapy.Item):
    """
    招标数据
    """

    project_name = scrapy.Field()
    """
    项目名称: str | None
    """

    project_code = scrapy.Field()
    """
    项目编号: str | None
    """

    project_introduction = scrapy.Field()
    """
    项目概况: str | None
    """

    procurement_method = scrapy.Field()
    """
    采购方式: str / int
    """

    budget = scrapy.Field()
    """
    预算金额（元）: int
    """

    bid_items = scrapy.Field()
    """
    标项信息: list[BidItem]
    """

    tenderer = scrapy.Field()
    """
    招标人（公司）/采购代理机构: str
    """

    tenderer_date = scrapy.Field()
    """
    招标公告发布信息: int(timestamp)
    """

    procurement_info = scrapy.Field()
    """
    采购人信息: InfoItem
    """

    tenderer_agency_info = scrapy.Field()
    """
    采购代理机构信息: InfoItem
    """

    procurement_publish_date = scrapy.Field()
    """
    采购公告发布时间: int(timestamp)
    """

    procurement_article_id = scrapy.Field()
    """
    采购公告id: str
    """

    result_publish_date = scrapy.Field()
    """
    结果公告发布时间: int(timestamp)
    """

    result_article_id = scrapy.Field()
    """
    结果公告id: str
    """

    scrape_date = scrapy.Field()
    """
    爬取时间: int(timestamp)
    """

    district_code = scrapy.Field()
    """
    地区编码: int
    """

    district_name = scrapy.Field()
    """
    地区名称: str
    """


class BidItem(scrapy.Item):
    """
    标项信息
    """
    index = scrapy.Field()

    name = scrapy.Field()

    result = scrapy.Field()


class BidResultItem(scrapy.Item):
    """
    标项结果信息
    """

    is_win = scrapy.Field()

    bidder_name = scrapy.Field()

    bidder_address = scrapy.Field()

    bid_amount = scrapy.Field()

    reason = scrapy.Field()

    other = scrapy.Field()


class InfoItem(scrapy.Item):
    """
    采购人信息、采购机构信息
    """

    name = scrapy.Field()

    address = scrapy.Field()

    contact_person = scrapy.Field()

    contact_info = scrapy.Field()


