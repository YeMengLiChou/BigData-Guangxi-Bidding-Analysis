from typing import Any

from pyspark.sql import DataFrame
from config.config import settings


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


def save_to_mysql(df: DataFrame, dbtable: str) -> None:
    """
    将 ``df`` 写入 mysql 的 ``dbtable`` 表中
    :param df
    :param dbtable 需要写入的表名
    """
    (
        df.write.mode("overwrite")
        .format("jdbc")
        .options(**__mysql_config)
        .option("dbtable", dbtable)
        .save()
    )
