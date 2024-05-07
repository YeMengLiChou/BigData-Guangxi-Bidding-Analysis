from typing import Any, Union, Callable

from pyspark.sql import DataFrame, functions as func, Column, Row
from pyspark.sql.session import SparkSession
from pyspark.sql.types import StructField, IntegerType


def append_columns(df: DataFrame, columns: dict[str, Column]) -> DataFrame:
    """
    添加指定的列 ``columns`` 到 ``df`` 中
    """
    for col_name, value in columns.items():
        df = df.withColumn(col_name, value)
    return df


def replace_null(df: DataFrame, cols_name: list[str], replace_value: Any) -> DataFrame:
    """
    将 ``df`` 中的 ``col_name`` 中为 NULL 的值切换为 ``replace_value``
    """
    for name in cols_name:
        df = df.withColumn(
            colName=name,
            col=func.when(func.col(name).isNull(), replace_value).otherwise(
                func.col(name)
            ),
        )
    return df


def filter_and_count(
    df: DataFrame,
    condition: Union[Column, None],
    groupby_cols: list[str],
    count_col_name: str = "count",
) -> DataFrame:
    """
    过滤出符合 ``condition`` 的数据并按照 ``groupby_cols`` 进行划分并统计，将 count 列重命名为 ``count_col_name``
    """
    if condition is None:
        return (df.groupby(groupby_cols)).agg(func.count("*").alias(count_col_name))
    else:
        return (
            df.filter(condition)
            .groupBy(groupby_cols)
            .agg(func.count("*").alias(count_col_name))
        )


def join_dataframes(
    dfs: list[DataFrame],
    depend_on: list[Column | str] | None,
    how_join: str = "left_outer",
) -> DataFrame:
    """
    将 ``dfs`` 中的所有 DataFrame 按照 ``depend_on`` 列用 ``how_join`` 方式合并为一个 DataFrame
    """
    n = len(dfs)
    if n == 0:
        raise ValueError("`dfs` doesn't have any DataFrame!")

    result_df = dfs[0]
    if n == 1:
        return result_df
    if depend_on:
        for i in depend_on:
            if not isinstance(i, (str, Column)):
                raise ValueError(
                    f"`depend_on` expect `Column` or `str`, but got `{type(i)}`!"
                )
    for i in range(1, n):
        result_df = result_df.join(other=dfs[i], on=depend_on, how=how_join)
    return result_df


def union_dataframes(
    union_dfs: list[DataFrame],
    callback: Callable[[DataFrame], DataFrame] = None,
    by_name: bool = True,
    allow_miss_columns: bool = False,
) -> DataFrame:
    """
    合并多个 DataFrame，以第一个的字段作为基准
    """
    result_df = union_dfs[0] if callback is None else callback(union_dfs[0])
    for i in range(1, len(union_dfs)):
        cur_df = union_dfs[i] if callback is None else callback(union_dfs[i])
        if by_name:
            result_df = result_df.unionByName(cur_df, allow_miss_columns)
        else:
            result_df = result_df.union(other=cur_df)
    return result_df


def create_dataframe(data: list[dict[str, Any]]) -> DataFrame:
    return SparkSession.Builder().appName("analyse").getOrCreate().createDataFrame(data)


def get_spark_session() -> SparkSession:
    return SparkSession.Builder().appName("analyse").getOrCreate()


def append_self_increasing_column(df: DataFrame) -> DataFrame:
    """
    给 ``df`` 增加自增列 `id`，返回新的 DataFrame
    """
    # 可能存在某些数据全是NULL，createDataFrame 无法识别这些内容，因此在这里加上一个id
    schema = df.schema
    schema.add(StructField("id", IntegerType()))

    def merge_row(tp: tuple[Row, int]):
        row_content = tp[0].asDict()
        row_content["id"] = tp[1]
        return Row(**row_content)

    rdd = df.rdd.zipWithIndex()
    row_rdd = rdd.map(merge_row)
    return get_spark_session().createDataFrame(row_rdd, schema)
