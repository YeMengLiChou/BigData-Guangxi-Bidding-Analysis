from config.config import settings
from utils.spark_utils import SparkUtils
from pyspark.sql import DataFrame
from pyspark.sql import functions as func
from analyse.schemas import BID_DATA_SCHEMA
from constant import constants


def get_kafka_streaming():
    """
    读取配置拿到 streaming
    """
    host = getattr(settings, "kafka.host", None)
    port = getattr(settings, "kafka.port", None)
    kafka_server = f"{host}:{port}"
    topic = getattr(settings, "kafka.spark.topic", None)
    session = SparkUtils.get_spark_sql_session("analyse")
    return SparkUtils.get_kafka_streaming(session, kafka_server, topics=[topic]).load()


def transform_to_json(df: DataFrame) -> DataFrame:
    """
    将数据转换为json
    """
    return (
        df.selectExpr(
            # "CAST(key AS STRING)",
            "CAST(value AS STRING)",  # 只有value有用
            # "topic",
            # "partition",
            # "offset",
            # "timestamp",
            # "timestampType"
        )
        .withColumn(
            "json",
            col=func.from_json(col="value", schema=BID_DATA_SCHEMA),
        )
        .select(func.col("json.*"))
    )


def stats(df: DataFrame) -> list[DataFrame]:
    district_count = df.groupby(constants.KEY_PROJECT_DISTRICT_CODE).count()
    author_count = df.groupby(constants.KEY_PROJECT_AUTHOR).count()
    catalog_count = df.groupby(constants.KEY_PROJECT_CATALOG).count()
    procurement_method_count = df.groupby(
        constants.KEY_PROJECT_PROCUREMENT_METHOD
    ).count()
    is_win_count = df.groupby(constants.KEY_PROJECT_IS_WIN_BID).count()
    total_budget_summary = df.select(
        constants.KEY_PROJECT_TOTAL_BUDGET, constants.KEY_PROJECT_TOTAL_AMOUNT
    ).summary()

    return [
        district_count,
        author_count,
        catalog_count,
        procurement_method_count,
        is_win_count,
        total_budget_summary,
    ]


def execute():
    streaming = get_kafka_streaming()
    df = transform_to_json(streaming)
    # (df.writeStream.foreach(lambda x: print(x)).start().awaitTermination())
    dfs = stats(df)
    for i in range(len(dfs)):
        dfs[i] = dfs[i].writeStream.outputMode("complete").format("console").start()
    dfs[0].awaitTermination()


if __name__ == "__main__":
    execute()
