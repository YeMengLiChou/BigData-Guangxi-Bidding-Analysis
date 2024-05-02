

# ===================== Constants Value =====================
class CollectConstants:
    BID_ITEM_AMOUNT_NOT_DEAL = -1
    """
    标项-金额没有成交，即废标
    """

    """
    项目的总金额：废标/终止
    """
    BID_ITEM_AMOUNT_UNASSIGNED = -2
    """
    标项-金额还没被赋值（初始化ing）
    """

    BID_ITEM_BUDGET_UNASSIGNED = -1
    """
    标项-预算还未赋值（初始化ing）
    """

    PROJECT_AMOUNT_UNASSIGNED = -1
    """
    项目的总金额-未赋值
    """

    PROJECT_AMOUNT_FAILED = 0


# ===================== Scrape Constants ===================


class AnnouncementType:
    WIN_AND_DEAL = 3004
    """
    中标(公交)公告
    """

    WIN = 4005
    """
    中标公告
    """

    NOT_WIN = 3007
    """
    废标公告
    """

    DEAL = 4006
    """
    成交公告
    """

    SHORTLISTED_FOR_TENDER = 3009
    """
    招标资格入围公告
    """

    TERMINATION = 3015
    """
    终止公告
    """

    SHORTLISTED_FOR_PUBLIC_TENDER = 4004
    """
    公开招标入围公告
    """


# =========================== dev key =====================

class CollectDevKey:

    PARRED_RESULT_ARTICLE_ID = "parsed_result_article_id"
    """
    已经解析到的结果公告id——位运算
    """
    
    PARRED_PURCHASE_ARTICLE_ID = "parsed_purchase_article_id"
    """
    已经解析到的采购公告id——位运算
    """
    
    START_RESULT_ARTICLE_ID = "start_result_article_id"
    """
    最开始的结果公告id
    """
    
    START_PURCHASE_ARTICLE_ID = "start_purchase_article_id"
    """
    最开始的结果公告id
    """
    
    BIDDING_CANCEL_REASON_ONLY_ONE = "only_one"
    """
    废标理由仅有一个（多个标项共用）
    """
    
    RESULT_CONTAINS_CANDIDATE = "contains_result_candidate"
    """
    中标结果存在候选人公告
    """
    
    DEBUG_WRITE = "debug_write"
    """
    将该部分内容写入文件的标志
    """
    
    TEMP_BASE_INFO = "tmp_base_info"
    """
    调试用：项目基本情况的内容
    """

    PURCHASE_SPECIAL_FORMAT_1 = "psf_1"
    """
    采购公告特殊格式：表示该采购公告中存在不符合爬取标准格式的内容：采购需求部分为表格或者无标项信息
    
    解决方案：省略该部分标项信息，直接拿到预算即可
    """

# ========================= part key =====================


class PartKey:
    PROJECT_CODE = 0
    """
    表示项目编号的part
    """

    PROJECT_NAME = 1
    """
    表示项目名称的part
    """

    TERMINATION_REASON = 2
    """
    表示终止原因的part
    """

    WIN_BID = 3
    """
    表示中标信息的part
    """

    NOT_WIN_BID = 4
    """
    表示未中标信息的part
    """

    CONTACT = 5
    """
    代表联系方式的part
    """

    REVIEW_EXPERT = 6
    """
    代表评审专家的part
    """

    PROJECT_SITUATION = 7
    """
    表示项目基本情况的part
    """


# ==================== stats key ===================


class StatsKey:
    FILTERED_COUNT = "filter/count"
    """
    过滤的公告数量(inc)
    """

    REDIS_LATEST_TIMESTAMP = "redis/latest_timestamp"
    """
    redis 的最新时间戳(set)
    """

    REDIS_SCRAPED_ANNOUNCEMENT_COUNT = "redis/announcement_count"
    """
    redis 的所有公告数量(set)
    """

    REDIS_UPDATE_PROCESS_ITEM_COUNT = "redis-update/process_items_count"
    """
    redis-update组件中处理的所有item(inc)
    """

    PARSE_ERROR_TOTAL = "parse-error/total"
    """
    parse error 的总数量(inc)
    """

    PARSE_ERROR_DUPLICATED = "parse-error/duplicated"
    """
    parse error 的重复数量(inc) 废弃
    """

    PARSE_ERROR_NON_DUPLICATED = "parse-error/non-duplicated"
    """
    parse error 的非重复数量(inc) 废弃
    """

    PARSE_ERROR_AMOUNT = "parse-error/amount"
    """
    金额解析异常
    """

    PARSE_ERROR_NOT_WIN_RESULT = "parse-error/not-win-result"
    """
    废标结果新格式异常
    """

    COLLECT_KAFKA_SEND_COUNT = "collect-kafka/send_count"
    """
    collect-kafka 组件中发送到 kafka 的公告数量(inc)
    """

    COLLECT_KAFKA_SEND_FAILED_COUNT = "collect-kafka/send_failed_count"
    """
    collect-kafka 组件中发送到 kafka 失败的公告数量(inc)
    """

    SPIDER_PLANNED_CRAWL_COUNT = "bidding/planned_crawl_count"
    """
    计划爬取的公告总数(set)
    """

    SPIDER_ACTUAL_CRAWL_COUNT = "bidding/actual_crawl_count"
    """
    已经爬取的数量，包括已经过滤的(inc)
    """
