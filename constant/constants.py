# 存放 KEY 的常量

# ===================== Constants Value =====================

BID_ITEM_AMOUNT_NOT_DEAL = -1
"""
标项-金额没有成交，即废标
"""

BID_ITEM_AMOUNT_UNASSIGNED = -2
"""
标项-金额还没被赋值（初始化ing）
"""

BID_ITEM_BUDGET_UNASSIGNED = -1

"""
标项-预算还未赋值（初始化ing）
"""

BID_ITEM_REASON_UNKNOWN = -2
"""
标项-废标理由：未知
"""

BID_ITEM_REASON_UNASSIGNED = -1
"""
标项-废标理由：还未赋值
"""

BID_ITEM_REASON_NOT_EXIST = 0
"""
标项-废标理由不存在，也就是中标了
"""

BID_ITEM_REASON_NOT_ENOUGH_SUPPLIERS = 1
"""
标项-废标理由：供应商不足
"""

BID_ITEM_REASON_BIDDING_DOCUMENTS_AMBIGUITY = 2
"""
标项-废标理由：招标文件存在歧义
"""

BID_ITEM_REASON_ILLEGAL = 3
"""
标项-废标理由：存在违规违法行为
"""

BID_ITEM_REASON_REOPEN = 4
"""
标项-废标理由：重新开展采购
ex:
1.因电子签章原因，资格审查中投标人了出现了几种签章的形式，采购人为了本项目更加公正公开公平，决定废标，重新开展采购;
"""

BID_ITEM_REASON_UNABLE_REVIEW = 5
"""
标项-废标理由：无法评审\n
ex:\n
1.因操作失误，评委人数不符合要求，且系统无法修改，导致项目无法评审，因此流标。
"""

BID_ITEM_REASON_NOT_PASS_COMPLIANCE_REVIEW = 6
"""
标项-废标理由：不通过符合性审查\n
ex:\n
1.三家提供的软件著作权证书均与其投标产品不符。不通过符合性审查
"""

BID_ITEM_REASON_MAJOR_CHANGES_AND_CANCEL = 7
"""
标项-废标理由：重大变故取消采购
ex:
1.因重大变故，采购任务取消
"""

BID_ITEM_REASON_SUPPLIERS_ALLOCATION_COMPLETED = 8
"""
标项-废标理由：供应商已经分配给其他标项，此标项无供应商
ex:
1. 在项目评审中，排名第一的中标侯选供应商在本项目本分标中取得本分标的第一中标侯选供应商资格的，
    在接下来的分标中将不能再取得第一中标候选供应商资格，但能参与接下来分标的评审，以此类推
2. 根据中标候选人推荐原则；在项目评审中，排名第一的中标侯选供应商在本项目本分标中取得本分标的第一中标侯选供应商资格的，
    在接下来的分标中将不能再取得第一中标候选供应商资格，但能参与接下来分标的评审，如排名
    
"""

BID_ITEM_REASON_COPYRIGHT_INCONSISTENT = 9
"""
标项-废标理由：提供的软件著作权证书均与其投标产品不符
ex:
1. 三家提供的软件著作权证书均与其投标产品不符
"""

BID_ITEM_REASON_PROCUREMENT_TERMINATION = 10
"""
标项-废标理由：终止采购
ex:
1. 本项目应采购人要求，经政府采购监督管理部门同意，终止此次采购。

"""



PROJECT_AMOUNT_UNASSIGNED = -1
"""
项目的总金额-未赋值
"""

PROJECT_AMOUNT_FAILED = 0
"""
项目的总金额：废标/终止
"""

# ===================== Scrape Constants ===================

ANNOUNCEMENT_TYPE_WIN_AND_DEAL = 3004
"""
中标(公交)公告
"""

ANNOUNCEMENT_TYPE_WIN = 4005
"""
中标公告
"""

ANNOUNCEMENT_TYPE_NOT_WIN = 3007
"""
废标公告
"""

ANNOUNCEMENT_TYPE_DEAL = 4006
"""
成交公告
"""

ANNOUNCEMENT_TYPE_SHORTLISTED_FOR_TENDER = 3009
"""
招标资格入围公告
"""

ANNOUNCEMENT_TYPE_TERMINATION = 3015
"""
终止公告
"""

ANNOUNCEMENT_TYPE_SHORTLISTED_FOR_PUBLIC_TENDER = 4004
"""
公开招标入围公告
"""

# ===================== Scrapy Item Key =====================

KEY_PROJECT_SCRAPE_TIMESTAMP = "scrape_timestamp"
"""
项目-爬取公告的时间戳
"""


KEY_PROJECT_NAME = "project_name"
"""
项目-项目名称
"""

KEY_PROJECT_CODE = "project_code"
"""
项目-项目编号
"""

KEY_PROJECT_TOTAL_BUDGET = "total_budget"
"""
项目-总预算金额
"""

KEY_PROJECT_TOTAL_AMOUNT = "total_amount"
"""
项目-总中标金额
"""

KEY_PROJECT_BID_ITEMS = "bid_items"
"""
项目-所有标项
"""

KEY_PROJECT_DISTRICT_CODE = "district_code"
"""
项目-项目所在行政区划代码
"""

KEY_PROJECT_CATALOG = "catalog"
"""
项目-项目采购所属种类
"""

KEY_PROJECT_PROCUREMENT_METHOD = "procurement_method"
"""
项目-采购方式
"""

KEY_PROJECT_BID_OPENING_TIME = "bid_opening_time"
"""
项目-开标时间
"""

KEY_PROJECT_IS_WIN_BID = "is_win_bid"
"""
项目-是否中标/成交/废标
"""

KEY_PROJECT_AUTHOR = "author"
"""
项目-公告发表者
"""

KEY_PROJECT_RESULT_PUBLISH_DATE = "result_publish_date"
"""
项目-结果公告发布日期
"""

KEY_PROJECT_RESULT_ARTICLE_ID = "result_article_id"
"""
项目-结果公告id
"""

KEY_PROJECT_PURCHASE_ARTICLE_ID = "purchase_article_id"
"""
项目-采购公告id
"""

KEY_PROJECT_PURCHASE_PUBLISH_DATE = "purchase_publish_date"
"""
项目-采购公告发布日期
"""

KEY_PROJECT_TENDER_DURATION = "tender_duration"
"""
项目-持续时间：从最开始的公告发布开始（一般是意见或采购），到最后的公告结束（一般是合同）
"""

KEY_PROJECT_PURCHASE_REPRESENTATIVE = "purchase_representative"
"""
项目-采购代表人
"""

KEY_PROJECT_REVIEW_EXPERT = "review_expert"
"""
项目-评审专家
"""

KEY_PROJECT_IS_TERMINATION = "is_termination"
"""
项目-是否终止
"""

KEY_PROJECT_TERMINATION_REASON = "termination_reason"
"""
项目-终止原因
"""

KEY_PURCHASER = "purchaser"
"""
联系-采购人信息
"""

KEY_PURCHASER_AGENCY= "purchasing_agency"
"""
联系-采购代理机构信息
"""

KEY_BID_ITEM_INDEX = "index"
"""
标项-序号
"""

KEY_BID_ITEM_NAME = "name"
"""
标项-名称
"""

KEY_BID_ITEM_BUDGET = "budget"
"""
标项-预算金额
"""

KEY_BID_ITEM_IS_WIN = "is_win"
"""
标项-是否中标
"""

KEY_BID_ITEM_SUPPLIER = "supplier"
"""
标项-中标供应商
"""

KEY_BID_ITEM_SUPPLIER_ADDRESS = "supplier_address"
"""
标项-中标供应商地址
"""

KEY_BID_ITEM_AMOUNT = "amount"
"""
标项-中标金额/成交金额
"""

KEY_BID_ITEM_IS_PERCENT = "is_percent"
"""
标项-成交金额是否为百分比
"""

KEY_BID_ITEM_REASON = "reason"
"""
标项-废标原因
"""

# =========================== dev key =====================

KEY_DEV_PARRED_RESULT_ARTICLE_ID = "parsed_result_article_id"
"""
已经解析到的结果公告id——位运算
"""

KEY_DEV_PARRED_PURCHASE_ARTICLE_ID = "parsed_purchase_article_id"
"""
已经解析到的采购公告id——位运算
"""

KEY_DEV_START_RESULT_ARTICLE_ID = "start_result_article_id"
"""
最开始的结果公告id
"""

KEY_DEV_START_PURCHASE_ARTICLE_ID = "start_purchase_article_id"
"""
最开始的结果公告id
"""

KEY_DEV_BIDDING_CANCEL_REASON_ONLY_ONE = "only_one"
"""
废标理由仅有一个（多个标项共用）
"""

KEY_DEV_RESULT_CONTAINS_CANDIDATE = "contains_result_candidate"
"""
中标结果存在候选人公告
"""

KEY_DEV_DEBUG_WRITE = "debug_write"
"""
将该部分内容写入文件的标志
"""

KEY_TEMP_BASE_INFO = "tmp_base_info"
"""
调试用：项目基本情况的内容
"""

# ========================= part key =====================
KEY_PART_PROJECT_CODE = 0
"""
表示项目编号的part
"""

KEY_PART_PROJECT_NAME = 1
"""
表示项目名称的part
"""

KEY_PART_TERMINATION_REASON = 2
"""
表示终止原因的part
"""

KEY_PART_WIN_BID = 3
"""
表示中标信息的part
"""

KEY_PART_NOT_WIN_BID = 4
"""
表示未中标信息的part
"""

KEY_PART_CONTACT = 5
"""
代表联系方式的part
"""

KEY_PART_REVIEW_EXPERT = 6
"""
代表评审专家的part
"""

KEY_PART_PROJECT_SITUATION = 7
"""
表示项目基本情况的part
"""


