from typing import Any
from pyspark.sql import DataFrame
from config.config import settings
from utils import dataframe_tools
from pyspark.sql import functions as func
from pyspark.sql.types import *


def __get(key: str, raise_error=True) -> Any:
    value = getattr(settings, key, None)
    if raise_error and value is None:
        raise ValueError(f"Missing `{key}` in settings.toml!")
    else:
        return value


__host = __get("mysql.host")
__port = __get("mysql.port")
__database = __get("mysql.database")

__mysql_config = {
    "url": f"jdbc:mysql://{__host}:{__port}/{__database}?rewriteBatchedStatements=true",
    "user": __get("mysql.user"),
    "password": __get("mysql.password"),
    "batchsize": __get("mysql.batchSize", False) or 1000,
    "isolationLevel": __get("mysql.isolationLevel") or "NONE",
    "driver": "com.mysql.cj.jdbc.Driver",
    "truncate": "true",
}


def transform_to_mysql_format(df: DataFrame) -> DataFrame:
    """
    将 ``df`` 转换为合适 mysql 存储的格式
    """
    schema = df.schema
    arr_cols = []
    bool_cols = []

    # 将不符合插入mysql的数组类型转成json
    # 将 boolean 类型转为 byte 存储
    for col in df.columns:
        if isinstance(schema[col].dataType, ArrayType):
            arr_cols.append(col)
        elif isinstance(schema[col].dataType, BooleanType):
            bool_cols.append(col)

    for col in arr_cols:
        df = df.withColumn(col, func.to_json(col))

    for col in bool_cols:
        df = df.withColumn(
            col, func.when(func.col(col), 1).otherwise(func.lit(0).astype(ByteType()))
        )

    return df


def save_to_mysql(df: DataFrame, dbtable: str) -> None:
    """
    将 ``df`` 写入 mysql 的 ``dbtable`` 表中
    :param df
    :param dbtable 需要写入的表名
    """
    df = transform_to_mysql_format(df)
    df = dataframe_tools.append_self_increasing_column(df)
    (
        df.write.mode("overwrite")
        .format("jdbc")
        .options(**__mysql_config)
        .option("dbtable", dbtable)
        .save()
    )
