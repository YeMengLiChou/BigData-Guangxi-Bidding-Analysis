"""
统计采购方式的总类
"""

from pyspark.sql import DataFrame, GroupedData, functions as func

from analyse.core import common
from constants import ProjectKey


def procurement_method_count(
    df: DataFrame,
) -> DataFrame:
    """
    统计采购方法的出现次数以及成交的总金额

    +-------------+------------------+----+-----+---+-------+-----+-------------+
    |district_code|procurement_method|year|month|day|quarter|count|total_amount |
    +-------------+------------------+----+-----+---+-------+-----+-------------+
    """
    df = df.select(
        ProjectKey.DISTRICT_CODE,
        ProjectKey.SCRAPE_TIMESTAMP,
        ProjectKey.PROCUREMENT_METHOD,
        ProjectKey.TOTAL_AMOUNT,
    ).withColumn(
        ProjectKey.TOTAL_AMOUNT,
        func.when(func.col(ProjectKey.TOTAL_AMOUNT) < 0, 0).otherwise(
            func.col(ProjectKey.TOTAL_AMOUNT)
        ),
    )

    def agg_func(gd: GroupedData, columns: list[str]) -> DataFrame:
        if "count" not in columns:
            return gd.agg(
                func.count(ProjectKey.PROCUREMENT_METHOD).alias("count"),
                func.sum(ProjectKey.TOTAL_AMOUNT).alias("total_amount"),
            )
        else:
            return gd.agg(
                func.sum("count").alias("count"),
                func.sum("total_amount").alias("total_amount"),
            )

    return common.stats_all(
        df,
        groupby_cols=[ProjectKey.DISTRICT_CODE, ProjectKey.PROCUREMENT_METHOD],
        agg_func=agg_func,
    ).filter(func.col(ProjectKey.DISTRICT_CODE) == 45000)
