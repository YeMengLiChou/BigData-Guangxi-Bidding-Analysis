class ProjectKey:
    """
    项目的key
    """
    TITLE = "title"
    """
    公告-标题
    """

    PURCHASE_TITLE = "purchase_title"
    """
    项目-采购公告的标题
    """

    SCRAPE_TIMESTAMP = "scrape_timestamp"
    """
    项目-爬取公告的时间戳
    """

    NAME = "project_name"
    """
    项目-项目名称
    """

    CODE = "project_code"
    """
    项目-项目编号
    """

    ANNOUNCEMENT_TYPE = "announcement_type"
    """
    项目-公告类型
    """

    TOTAL_BUDGET = "total_budget"
    """
    项目-总预算金额
    """

    TOTAL_AMOUNT = "total_amount"
    """
    项目-总中标金额
    """

    BID_ITEMS = "bid_items"
    """
    项目-所有标项
    """

    DISTRICT_CODE = "district_code"
    """
    项目-项目所在行政区划代码
    """

    DISTRICT_NAME = "district_name"
    """
    项目-项目所在行政区名称
    """

    CATALOG = "catalog"
    """
    项目-项目采购所属种类
    """

    PROCUREMENT_METHOD = "procurement_method"
    """
    项目-采购方式
    """

    BID_OPENING_TIME = "bid_opening_time"
    """
    项目-开标时间
    """

    IS_WIN_BID = "is_win_bid"
    """
    项目-是否中标/成交/废标
    """

    AUTHOR = "author"
    """
    项目-公告发表者
    """

    RESULT_PUBLISH_DATE = "result_publish_date"
    """
    项目-结果公告发布日期
    """

    RESULT_SOURCE_ARTICLE_ID = "result_source_article_id"
    """
    项目-数据来源采购公告
    """

    PURCHASE_SOURCE_ARTICLE_ID = "purchase_source_article_id"
    """
    项目-数据来源采购公告
    """

    RESULT_ARTICLE_ID = "result_article_id"
    """
    项目-结果公告id
    """

    PURCHASE_ARTICLE_ID = "purchase_article_id"
    """
    项目-采购公告id
    """

    PURCHASE_PUBLISH_DATE = "purchase_publish_date"
    """
    项目-采购公告发布日期
    """

    TENDER_DURATION = "tender_duration"
    """
    项目-持续时间：从最开始的公告发布开始（一般是意见或采购），到最后的公告结束（一般是合同）
    """

    PURCHASE_REPRESENTATIVE = "purchase_representative"
    """
    项目-采购代表人
    """

    REVIEW_EXPERT = "review_expert"
    """
    项目-评审专家
    """

    IS_TERMINATION = "is_termination"
    """
    项目-是否终止
    """

    TERMINATION_REASON = "termination_reason"
    """
    项目-终止原因
    """

    PURCHASER = "purchaser"
    """
    联系-采购人信息
    """

    PURCHASER_AGENCY = "purchasing_agency"
    """
    联系-采购代理机构信息
    """


class BidItemKey:
    INDEX = "index"
    """
    标项-序号
    """

    NAME = "name"
    """
    标项-名称
    """

    BUDGET = "budget"
    """
    标项-预算金额
    """

    IS_WIN = "is_win"
    """
    标项-是否中标
    """

    SUPPLIER = "supplier"
    """
    标项-中标供应商
    """

    SUPPLIER_ADDRESS = "supplier_address"
    """
    标项-中标供应商地址
    """

    AMOUNT = "amount"
    """
    标项-中标金额/成交金额
    """

    IS_PERCENT = "is_percent"
    """
    标项-成交金额是否为百分比
    """

    REASON = "reason"
    """
    标项-废标原因
    """
