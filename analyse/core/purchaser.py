#
#  关于分析统计 招标人 的信息
#
from pyspark.sql import DataFrame
from pyspark.sql import functions as func
from pyspark.sql.window import Window
from constants import ProjectKey
from utils import dataframe_tools as df_utils


def purchaser_occurrences(
    df: DataFrame, year: int = None, month: int = None, quarter: int = None
) -> DataFrame:
    """
    统计 招标人 的招现次数，支持不同年、月、季度的统计
    """
    time_condition = df_utils.get_time_span_condition(
        ProjectKey.SCRAPE_TIMESTAMP, year, month, quarter
    )

    if time_condition is not None:
        df = df.filter(time_condition)
    return df.groupby(ProjectKey.PURCHASER).count()


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
    window_spec = Window.partitionBy(ProjectKey.PURCHASER)
    # 通过对每个窗口进行count排序，然后用row_number标记行数，然后合并到df中
    numbered_df = df.withColumn(
        "row_number", func.row_number().over(window_spec.orderBy(func.desc("count")))
    )
    # 选出 row_number <= 3 的记录，也就是出现最多的三个
    result_df = numbered_df.filter("row_number <= 3").drop("row_number")
    return result_df


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
    window_spec = Window.partitionBy(ProjectKey.PURCHASER)
    # 通过对每个窗口进行count排序，然后用row_number标记行数，然后合并到df中
    numbered_df = df.withColumn(
        "row_number", func.row_number().over(window_spec.orderBy(func.desc("count")))
    )
    # 选出 row_number <= 3 的记录，也就是出现最多的三个
    result_df = numbered_df.filter("row_number <= 3").drop("row_number")
    return result_df
