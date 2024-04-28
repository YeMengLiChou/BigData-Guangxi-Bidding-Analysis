import datetime
from typing import Any

from pyspark.sql import DataFrame, functions as func, Column


def replace_null(df: DataFrame, col_name: list[str], replace_value: Any) -> DataFrame:
    """
    将 ``df`` 中的 ``col_name`` 中为 NULL 的值切换为 ``replace_value``
    """
    for name in col_name:
        df = df.withColumn(
            colName=name,
            col=func.when(func.col(name).isNull(), replace_value).otherwise(
                func.col(name)
            ),
        )
    return df


def filter_and_count(
    df: DataFrame,
    condition,
    groupby_cols: list[str],
    count_col_name: str = "count",
) -> DataFrame:
    """
    过滤出符合 ``condition`` 的数据并按照 ``groupby_cols`` 进行划分并统计，将 count 列重命名为 ``count_col_name``
    """
    return (
        df.filter(condition)
        .groupBy(groupby_cols)
        .agg(func.count("*").alias(count_col_name))
    )


def merge_dataframes(
    dfs: list[DataFrame],
    depend_on: list[Column | str],
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

    depend_cols = []
    for i in range(len(depend_on)):
        if isinstance(depend_on[i], str):
            depend_cols.append(func.col(depend_on[i]))
        else:
            depend_cols.append(func.col(depend_on[i]))

    for i in range(1, n):
        result_df = result_df.join(other=dfs[i], on=depend_on, how=how_join)
    return result_df


def get_time_span_condition(
    timestamp_col_name: str,
    year: int = None,
    month: int = None,
    quarter: int = None,
) -> Column:
    """
    根据所给的 ``year`` ``month`` ``quarter`` 来获取对应的时间范围条件
    """
    # 指定了年和月
    if year and month:
        if quarter:
            raise ValueError(
                "`quarter` must be None when `year` and `month` is not None!"
            )
        from_timestamp = int(
            datetime.datetime(year=year, month=month, day=1, hour=0).timestamp() * 1000
        )
        if month == 12:
            year += 1
            month = 1
        to_timestamp = int(
            datetime.datetime(year=year, month=month, day=1, hour=0).timestamp() * 1000
        )
    # 指定了年 和季度 1、2、3、4
    elif year and quarter:
        if month:
            raise ValueError(
                "`month` must be None when `year` and `quarter` is not None!"
            )

        if quarter < 1 or quarter > 4:
            raise ValueError("`quarter` must be in [1, 2, 3, 4]!")

        from_timestamp = int(
            datetime.datetime(
                year=year, month=quarter * 3 - 2, day=1, hour=0
            ).timestamp()
            * 1000
        )
        to_timestamp = int(
            datetime.datetime(
                year=year + 1, month=quarter * 3, day=1, hour=0
            ).timestamp()
            * 1000
        )
    # 指定了年
    elif year and month is None and quarter is None:
        from_timestamp = int(
            datetime.datetime(year=year, month=1, day=1, hour=0).timestamp() * 1000
        )
        to_timestamp = int(
            datetime.datetime(year=year + 1, month=1, day=1, hour=0).timestamp() * 1000
        )
    else:
        from_timestamp, to_timestamp = None, None

    if from_timestamp and to_timestamp:
        time_condition = (func.col(timestamp_col_name) >= from_timestamp) & (
            func.col(timestamp_col_name) < to_timestamp
        )
    else:
        time_condition = None

    return time_condition
