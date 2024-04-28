from pyspark.sql.types import *
from constants import ProjectKey, BidItemKey

"""
标项信息格式
"""
BID_ITEM_SCHEMA = StructType(
    [
        StructField(BidItemKey.NAME, StringType()),
        StructField(BidItemKey.INDEX, IntegerType()),
        StructField(BidItemKey.IS_WIN, BooleanType()),
        StructField(BidItemKey.BUDGET, DoubleType()),
        StructField(BidItemKey.AMOUNT, DoubleType()),
        StructField(BidItemKey.IS_PERCENT, BooleanType()),
        StructField(BidItemKey.SUPPLIER, StringType(), nullable=True),
        StructField(BidItemKey.SUPPLIER_ADDRESS, StringType(), nullable=True),
        StructField(BidItemKey.REASON, StringType(), nullable=True),
    ]
)
