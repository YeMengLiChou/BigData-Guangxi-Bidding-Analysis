#
#  关于分析统计 招标人 的信息
#
from pyspark.sql import DataFrame
from pyspark.sql import functions as func
from pyspark.sql.window import Window

from analyse.core import common
from constants import ProjectKey
from utils import dataframe_tools as df_utils
from pyspark.sql import GroupedData


def purchaser_occurrences(df: DataFrame) -> DataFrame:
    """
    统计 招标人 的招现次数，支持不同年、月、季度的统计
    """

    def agg_func(gd: GroupedData, columns: list[str]) -> DataFrame:
        if "count" not in columns:
            return gd.agg(func.count("*").alias("count"))
        else:
            return gd.agg(func.sum("count").alias("count"))

    return common.stats_all(
        df=df.select(
            ProjectKey.SCRAPE_TIMESTAMP, ProjectKey.DISTRICT_CODE, ProjectKey.PURCHASER
        ),
        groupby_cols=[ProjectKey.DISTRICT_CODE, ProjectKey.PURCHASER],
        agg_func=agg_func,
    )


# 分析 采购人和种类的关系
def purchaser_catalog(df: DataFrame) -> DataFrame:
    """
    统计 每个采购者 招标的种类最多
    """
    df = (
        df.select(ProjectKey.PURCHASER, ProjectKey.CATALOG)
        .groupBy(ProjectKey.PURCHASER, ProjectKey.CATALOG)
        .count()
    )
    # 根据 purchaser 划分的 window
    # window_spec = Window.partitionBy(ProjectKey.PURCHASER)
    # # 通过对每个窗口进行count排序，然后用row_number标记行数，然后合并到df中
    # numbered_df = df.withColumn(
    #     "row_number", func.row_number().over(window_spec.orderBy(func.desc("count")))
    # )
    # # 选出 row_number <= 3 的记录，也就是出现最多的三个
    # result_df = numbered_df.filter("row_number <= 3").drop("row_number")
    return df


def purchaser_related_agency(df: DataFrame) -> DataFrame:
    """
    统计 每个采购者 合作最多的代理商
    """
    df = (
        df.select(ProjectKey.PURCHASER, ProjectKey.PURCHASER_AGENCY)
        .groupBy(ProjectKey.PURCHASER, ProjectKey.PURCHASER_AGENCY)
        .count()
    )
    # 根据 purchaser 划分的 window
    # window_spec = Window.partitionBy(ProjectKey.PURCHASER)
    # # 通过对每个窗口进行count排序，然后用row_number标记行数，然后合并到df中
    # numbered_df = df.withColumn(
    #     "row_number", func.row_number().over(window_spec.orderBy(func.desc("count")))
    # )
    # # 选出 row_number <= 3 的记录，也就是出现最多的三个
    # result_df = numbered_df.filter("row_number <= 3").drop("row_number")
    return df
