from pyspark.sql.types import *
from constant.constants import *

"""
标项信息格式
"""
BID_ITEM_SCHEMA = StructType(
    [
        StructField(KEY_BID_ITEM_NAME, StringType()),
        StructField(KEY_BID_ITEM_INDEX, IntegerType()),
        StructField(KEY_BID_ITEM_IS_WIN, BooleanType()),
        StructField(KEY_BID_ITEM_BUDGET, DoubleType()),
        StructField(KEY_BID_ITEM_AMOUNT, DoubleType()),
        StructField(KEY_BID_ITEM_IS_PERCENT, BooleanType()),
        StructField(KEY_BID_ITEM_SUPPLIER, StringType(), nullable=True),
        StructField(KEY_BID_ITEM_SUPPLIER_ADDRESS, StringType(), nullable=True),
        StructField(KEY_BID_ITEM_REASON, StringType(), nullable=True),
    ]
)
