import analyse.core
from pyspark.sql.types import *

from analyse.core import (
    supplier,
    transactions,
    methods,
    bidding,
    purchaser,
    catalogs,
    agency,
)
from analyse.sinks.console import batch_to_console
from analyse.sinks.mysql import save_to_mysql
from config.config import settings
from utils import dataframe_tools
from utils.spark_utils import SparkUtils
from pyspark.sql import DataFrame
from pyspark.sql import functions as func
from analyse.schemas import BID_DATA_SCHEMA
from constants import ProjectKey, BidItemKey


def get_kafka_source():
    """
    读取配置拿到 streaming
    """
    host = getattr(settings, "kafka.host", None)
    port = getattr(settings, "kafka.port", None)
    kafka_server = f"{host}:{port}"
    topic = getattr(settings, "kafka.spark.topic", None)
    session = SparkUtils.get_spark_sql_session("analyse")
    return SparkUtils.get_kafka_source(session, kafka_server, topics=[topic]).load()


def transform_to_json(df: DataFrame) -> DataFrame:
    """
    将数据转换为json
    """
    return (
        df.selectExpr("CAST(value AS STRING)")
        .withColumn(
            "json",
            col=func.from_json("value", schema=BID_DATA_SCHEMA),
        )
        .select(func.col("json.*"))
    )


def execute():
    source = get_kafka_source()
    df = transform_to_json(source)

    # .show()
    # completed(df)


def completed(df: DataFrame):

    # 省、市、区级别的成交量和个数
    save_to_mysql(bidding.bidding_district_type(df), "bidding_district_stats")

    # 采购方式对应的个数以及总成交量
    save_to_mysql(methods.procurement_method_count(df), "procurement_stats")

    # 每种公告的类型数量
    save_to_mysql(bidding.bidding_result(df), "bidding_stats")

    # 每个地区的总成交金额（已完成）
    save_to_mysql(
        transactions.transactions_total_volume_all(df), "transactions_volumes"
    )

    # 全部原始数据写入到mysql中(已完成)
    # save_to_mysql(df, "bidding_announcement")

    # 供应商的中标个数和其总金额
    save_to_mysql(supplier.supplier_transactions_volume(df), "supplier_transactions")

    # 供应商和对应的采购类型的统计个数
    save_to_mysql(supplier.supplier_situations(df), "supplier_catalogs")

    # 供应商以及对应的地址
    save_to_mysql(supplier.supplier_address(df), "supplier_address")

    # 采购人出现次数 TODO：成交数
    save_to_mysql(purchaser.purchaser_occurrences(df), "purchaser_stats")

    # 采购人对应的种类次数统计
    save_to_mysql(purchaser.purchaser_catalog(df), "purchaser_catalog_stats")

    # 采购人对应的代理机构统计
    save_to_mysql(purchaser.purchaser_related_agency(df), "purchaser_agency_stats")

    # 采购种类的个数
    save_to_mysql(catalogs.catalog_stars(df), "catalog_stats")

    # 代理机构的出现次数
    save_to_mysql(agency.agency_stats(df), "agency_stats")

    # 代理机构和对应种类
    save_to_mysql(agency.agency_catalogs_stats(df), "agency_catalog_stats")


if __name__ == "__main__":
    execute()
