# 存放 KEY 的常量
#
#


# ===================== Constants Value =====================

BID_ITEM_QUANTITY_UNLIMITED = -1
"""
标项-数量没有限制，关键字：不限
"""

BID_ITEM_QUANTITY_UNCLEAR = 0
"""
标项-数量不明确
"""

BID_ITEM_QUANTITY_NOT_DEAL = -2
"""
标项-数量没有成交，即废标
"""

BID_ITEM_AMOUNT_NOT_DEAL = -1
"""
标项-金额没有成交，即废标
"""

# ===================== Scrapy Item Key =====================

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

KEY_PROJECT_BID_ITEMS = "bid_items"
"""
项目-所有标项
"""

KEY_PROJECT_IS_GOVERNMENT_PURCHASE = "is_government_purchase"
"""
项目-是否为项目采购
"""

KEY_PROJECT_DISTRICT_CODE = "district_code"
"""
项目-项目所在行政区划代码
"""

KEY_PROJECT_DISTRICT_NAME = "district_name"
"""
项目-项目所在行政区划名称
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

KEY_PROJECT_PURCHASE_REPRESENTOR = "purchase_representor"
"""
项目-采购代表人
"""

KEY_PROJECT_REVIEW_EXPERT = "review_expert"
"""
项目-评审专家
"""

KEY_PURCHASER_INFORMATION = "purchaser_information"
"""
联系-采购人信息
"""

KEY_PURCHASER_AGENCY_INFORMATION = "purchasing_agency_information"
"""
联系-采购代理机构信息
"""

KEY_CONTACT_NAME = "name"
"""
联系-采购人/采购代理机构名称
"""

KEY_CONTACT_ADDRESS = "address"
"""
联系-采购人/采购代理机构地址
"""

KEY_BID_ITEM_QUANTITY = "quantity"
"""
标项-数量
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
