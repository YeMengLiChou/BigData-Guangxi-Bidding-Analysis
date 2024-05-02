from pyspark.sql.types import *

from constants import ProjectKey
from .bid_item import BID_ITEM_SCHEMA

"""
爬取到的数据格式
"""
BID_DATA_SCHEMA = StructType(
    [
        # StructField(ProjectKey.RESULT_SOURCE_ARTICLE_ID, StringType(), nullable=True),
        # StructField(ProjectKey.PURCHASE_SOURCE_ARTICLE_ID, StringType(), nullable=True),
        # StructField(ProjectKey.TITLE, StringType()),
        # StructField(ProjectKey.PURCHASE_TITLE, StringType()),
        StructField(ProjectKey.SCRAPE_TIMESTAMP, LongType()),
        StructField(ProjectKey.NAME, StringType(), nullable=True),
        StructField(ProjectKey.CODE, StringType(), nullable=True),
        StructField(ProjectKey.DISTRICT_CODE, StringType()),
        # StructField(ProjectKey.DISTRICT_NAME, StringType(), nullable=True),
        StructField(ProjectKey.AUTHOR, StringType()),
        StructField(ProjectKey.CATALOG, StringType()),
        StructField(ProjectKey.PROCUREMENT_METHOD, StringType()),
        StructField(ProjectKey.BID_OPENING_TIME, LongType()),
        StructField(ProjectKey.IS_WIN_BID, BooleanType()),
        StructField(
            ProjectKey.RESULT_ARTICLE_ID,
            ArrayType(elementType=StringType(), containsNull=False),
        ),
        StructField(
            ProjectKey.RESULT_PUBLISH_DATE,
            ArrayType(elementType=LongType(), containsNull=False),
        ),
        StructField(
            ProjectKey.PURCHASE_ARTICLE_ID,
            ArrayType(elementType=StringType(), containsNull=False),
        ),
        StructField(
            ProjectKey.PURCHASE_PUBLISH_DATE,
            ArrayType(elementType=LongType(), containsNull=False),
        ),
        StructField(ProjectKey.TOTAL_BUDGET, DoubleType()),
        StructField(ProjectKey.BID_ITEMS, ArrayType(elementType=BID_ITEM_SCHEMA)),
        StructField(ProjectKey.TOTAL_AMOUNT, DoubleType()),
        StructField(ProjectKey.TENDER_DURATION, LongType()),
        StructField(ProjectKey.PURCHASER, StringType(), nullable=True),
        StructField(ProjectKey.PURCHASER_AGENCY, StringType(), nullable=True),
        StructField(
            ProjectKey.REVIEW_EXPERT,
            ArrayType(elementType=StringType(), containsNull=False),
        ),
        StructField(
            ProjectKey.PURCHASE_REPRESENTATIVE,
            ArrayType(elementType=StringType(), containsNull=False),
        ),
        StructField(ProjectKey.IS_TERMINATION, BooleanType()),
        StructField(ProjectKey.TERMINATION_REASON, StringType(), nullable=True),
    ]
)
