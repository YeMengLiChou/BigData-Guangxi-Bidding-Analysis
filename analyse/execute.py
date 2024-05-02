from analyse.core import supplier, transactions, methods, bidding
from analyse.sinks.console import batch_to_console
from analyse.sinks.mysql import save_to_mysql
from config.config import settings
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
    # for i in range(len(dfs)):
    #     dfs[i] = batch_to_console(dfs[i])

    # batch_to_console(purchaser.purchaser_related_agency(df))
    # batch_to_console(supplier.supplier_transactions_volume(df))
    # batch_to_console(supplier.supplier_transactions_volume(df))
    save_to_mysql(transactions.transactions_total_volume_all(df), "test2")
    # batch_to_console(transactions.transactions_total_volume(df, False, 2022, 4))
    # batch_to_console(methods.procurement_method_count(df))
    # batch_to_console(bidding.bidding_result(df))
    # batch_to_console(bidding.bidding_district_type(df))
    # save_to_mysql(bidding.bidding_district_type(df))


if __name__ == "__main__":
    execute()