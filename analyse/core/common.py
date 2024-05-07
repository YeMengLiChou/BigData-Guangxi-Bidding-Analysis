from typing import Callable

from pyspark.sql import functions as func
from pyspark.sql import DataFrame, GroupedData
from pyspark.sql.types import TimestampType, IntegerType
from constants import ProjectKey, DevConstants
from utils import dataframe_tools


def add_time_columns(df: DataFrame) -> DataFrame:
    """
    将时间戳计算出对应的年月日和季度：year、month、day、quarter
    """
    a = 1
    tp_col = func.col(ProjectKey.SCRAPE_TIMESTAMP)
    return (
        df.withColumn(
            ProjectKey.SCRAPE_TIMESTAMP, (tp_col / 1000).cast(TimestampType())
        )
        .withColumn("year", func.year(tp_col))
        .withColumn("month", func.month(tp_col))
        .withColumn("day", func.dayofmonth(tp_col))
        # 1: 1 2 3 | 2: 4 5 6 | 3: 7 8 9 | 4: 10 11 12
        .withColumn(
            "quarter",
            ((func.month(tp_col) - 1).cast(IntegerType()) / 3).cast(IntegerType()) + 1,
        )
    )


def complete_time_columns(df: DataFrame) -> DataFrame:
    """
    完善缺失的列: [month, day, quarter]
    """
    check_columns = ["month", "day", "quarter"]
    zero_col = func.lit(0)
    for col in check_columns:
        if col not in df.columns:
            df = df.withColumn(col, zero_col)
    return df


def stats_all(
    df: DataFrame,
    groupby_cols: list[str],
    agg_func: Callable[[GroupedData, list[str]], DataFrame],
    union_action: Callable[[DataFrame], DataFrame] = None,
) -> DataFrame:
    """
    根据时间戳分别计算年月日、季度的数据以及各地区和全省的数据
    """
    # 将时间戳计算出对应的年月日和季度
    df = add_time_columns(df).drop(ProjectKey.SCRAPE_TIMESTAMP)
    # 分别算出年月日和季度的数据
    days_df = agg_func(df.groupby(*groupby_cols, "year", "month", "day"), df.columns)
    months_df = agg_func(df.groupby(*groupby_cols, "year", "month"), df.columns)
    quarters_df = agg_func(df.groupby(*groupby_cols, "year", "quarter"), df.columns)
    years_df = agg_func(df.groupby(*groupby_cols, "year"), df.columns)

    def action(_df: DataFrame) -> DataFrame:
        if union_action:
            return complete_time_columns(union_action(_df))
        else:
            return complete_time_columns(_df)

    # 将这些数据合并到一个表中
    district_df = dataframe_tools.union_dataframes(
        union_dfs=[days_df, months_df, quarters_df, years_df],
        callback=action,
        by_name=True,
    )
    # 将地区的代码改成同一个省的
    province_df = agg_func(
        district_df.withColumn(
            ProjectKey.DISTRICT_CODE,
            func.lit(DevConstants.STATS_DISTRICT_CODE_PROVINCE),
        ).groupby(*groupby_cols, "year", "month", "day", "quarter"),
        district_df.columns,
    )
    return province_df.unionByName(district_df)
