from pyspark.sql.types import *

from .bid_item import BID_ITEM_SCHEMA
from constant.constants import *

"""
爬取到的数据格式
"""
BID_DATA_SCHEMA = StructType(
    [
        StructField(KEY_PROJECT_SCRAPE_TIMESTAMP, LongType()),
        StructField(KEY_PROJECT_NAME, StringType(), nullable=True),
        StructField(KEY_PROJECT_CODE, StringType(), nullable=True),
        StructField(KEY_PROJECT_DISTRICT_CODE, StringType()),
        StructField(KEY_PROJECT_AUTHOR, StringType()),
        StructField(KEY_PROJECT_CATALOG, StringType()),
        StructField(KEY_PROJECT_PROCUREMENT_METHOD, StringType()),
        StructField(KEY_PROJECT_BID_OPENING_TIME, LongType()),
        StructField(KEY_PROJECT_IS_WIN_BID, BooleanType()),
        StructField(
            KEY_PROJECT_RESULT_ARTICLE_ID,
            ArrayType(elementType=StringType(), containsNull=False),
        ),
        StructField(
            KEY_PROJECT_RESULT_PUBLISH_DATE,
            ArrayType(elementType=LongType(), containsNull=False),
        ),
        StructField(
            KEY_PROJECT_PURCHASE_ARTICLE_ID,
            ArrayType(elementType=StringType(), containsNull=False),
        ),
        StructField(
            KEY_PROJECT_PURCHASE_PUBLISH_DATE,
            ArrayType(elementType=LongType(), containsNull=False),
        ),
        StructField(KEY_PROJECT_TOTAL_BUDGET, DoubleType()),
        StructField(KEY_PROJECT_BID_ITEMS, ArrayType(elementType=BID_ITEM_SCHEMA)),
        StructField(KEY_PROJECT_TOTAL_AMOUNT, DoubleType()),
        StructField(KEY_PROJECT_TENDER_DURATION, LongType()),
        StructField(KEY_PURCHASER, StringType(), nullable=True),
        StructField(KEY_PURCHASER_AGENCY, StringType(), nullable=True),
        StructField(
            KEY_PROJECT_REVIEW_EXPERT,
            ArrayType(elementType=StringType(), containsNull=False),
        ),
        StructField(
            KEY_PROJECT_PURCHASE_REPRESENTATIVE,
            ArrayType(elementType=StringType(), containsNull=False),
        ),
        StructField(KEY_PROJECT_IS_TERMINATION, BooleanType()),
        StructField(KEY_PROJECT_TERMINATION_REASON, StringType(), nullable=True),
    ]
)
