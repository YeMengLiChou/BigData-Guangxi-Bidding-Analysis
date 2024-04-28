import datetime
from typing import Any
from pyspark.sql import DataFrame, functions as func, Column
from constants import ProjectKey
from utils import dataframe_tools as df_utils


def append_columns(df: DataFrame, columns: dict[str, Any]) -> DataFrame:
    """
    添加指定的列到 ``df`` 中
    """
    for col_name, value in columns.items():
        df = df.withColumn(col_name, value)
    return df


def bidding_result(
    df: DataFrame,
    district_groupby: bool = True,
    year: int = None,
    month: int = None,
    quarter: int = None,
) -> DataFrame:
    """
    统计中标、废标、终止数量

    +-------------+-----------+----------+----------+---------------+----+-----+-------+
    |district_code|total_count|wins_count|lose_count|terminate_count|year|month|quarter|
    +-------------+-----------+----------+----------+---------------+----+-----+-------+

    ----------
    :param df
    :param district_groupby 是否按 ProjectKey.DISTRICT_CODE 分组
    :param year 指定的年
    :param month 指定的月
    :param quarter 指定的季度
    """

    groupby_cols = [ProjectKey.DISTRICT_CODE]
    if not district_groupby:
        df = df.withColumn(ProjectKey.DISTRICT_CODE, func.lit(0))

    time_condition = df_utils.get_time_span_condition(
        ProjectKey.SCRAPE_TIMESTAMP, year, month, quarter
    )

    # 过滤出 成交结果
    condition = func.col(ProjectKey.IS_WIN_BID)
    if time_condition is not None:
        condition = condition & time_condition

    wins_by_district = df_utils.filter_and_count(
        df,
        condition=condition,
        groupby_cols=groupby_cols,
        count_col_name="wins_count",
    )

    # 过滤出 废标结果
    condition = (~func.col(ProjectKey.IS_WIN_BID)) & (
        ~func.col(ProjectKey.IS_TERMINATION)
    )
    if time_condition is not None:
        condition = condition & time_condition

    lose_by_district = df_utils.filter_and_count(
        df,
        condition=condition,
        groupby_cols=groupby_cols,
        count_col_name="lose_count",
    )

    # 过滤出 终止结果
    condition = func.col(ProjectKey.IS_TERMINATION)
    if time_condition is not None:
        condition = condition & time_condition
    terminate_by_district = df_utils.filter_and_count(
        df,
        condition=condition,
        groupby_cols=groupby_cols,
        count_col_name="terminate_count",
    )

    # 根据 地区 统计各个地区的公告次数
    total_transactions_by_district = df.groupBy(ProjectKey.DISTRICT_CODE).agg(
        func.count("*").alias("total_count")
    )

    # 将这些内容合并
    merged_df = df_utils.merge_dataframes(
        dfs=[
            total_transactions_by_district,
            wins_by_district,
            lose_by_district,
            terminate_by_district,
        ],
        depend_on=[ProjectKey.DISTRICT_CODE],
    )
    # 去除合并后产生的 NULL 值
    result_df = df_utils.replace_null(
        merged_df,
        col_name=["wins_count", "lose_count", "terminate_count"],
        replace_value=0,
    )

    # 加上 year、 month、quarter 列
    result_df = append_columns(
        result_df,
        {
            "year": func.lit(year if year else -1),
            "month": func.lit(month if month else -1),
            "quarter": func.lit(quarter if quarter else -1),
        },
    )

    return result_df


def bidding_amount(
    df: DataFrame,
    district_groupby: bool = True,
    year: int = None,
    month: int = None,
    quarter: int = None,
) -> DataFrame:
    """
    统计所有数据中 各地区的总预算、总花费的最大值、总值、平均值

    +-------------+----------+----------+----------+----------+----------+----------+----+-----+-------+
    |district_code|amount_sum|amount_max|amount_avg|budget_sum|budget_max|budget_avg|year|month|quarter|
    +-------------+----------+----------+----------+----------+----------+----------+----+-----+-------+

    ----------
    :param df
    :param district_groupby 是否对地区进行划分, False 为统计全广西的数据
    :param year 指定的年
    :param month 指定的月
    :param quarter 指定的季度
    """
    groupby_cols = [ProjectKey.DISTRICT_CODE]

    if not groupby_cols:
        df = df.withColumn(ProjectKey.DISTRICT_CODE, func.lit(0))

    time_condition = df_utils.get_time_span_condition(
        timestamp_col_name=ProjectKey.SCRAPE_TIMESTAMP,
        year=year,
        month=month,
        quarter=quarter,
    )
    # 过滤出符合时间段的
    if time_condition is not None:
        df = df.filter(condition=time_condition)

    # 拿到指定的数据
    df = df.select(
        ProjectKey.DISTRICT_CODE,
        ProjectKey.TOTAL_AMOUNT,
        ProjectKey.TOTAL_BUDGET,
        ProjectKey.SCRAPE_TIMESTAMP,
    )

    amount_col = func.col(ProjectKey.TOTAL_AMOUNT)
    budget_col = func.col(ProjectKey.TOTAL_BUDGET)

    # 过滤掉负数和Null的值
    df = df.withColumn(
        ProjectKey.TOTAL_AMOUNT,
        func.when(amount_col.isNull(), 0).when(amount_col < 0, 0).otherwise(amount_col),
    ).withColumn(
        ProjectKey.TOTAL_BUDGET,
        func.when(budget_col.isNull(), 0).when(budget_col < 0, 0).otherwise(budget_col),
    )

    # 统计数据：总值、最大值、平均值
    result_df = df.groupby(groupby_cols).agg(
        func.sum(ProjectKey.TOTAL_AMOUNT).alias("amount_sum"),
        func.max(ProjectKey.TOTAL_AMOUNT).alias("amount_max"),
        func.mean(ProjectKey.TOTAL_AMOUNT).alias("amount_avg"),
        func.sum(ProjectKey.TOTAL_BUDGET).alias("budget_sum"),
        func.max(ProjectKey.TOTAL_BUDGET).alias("budget_max"),
        func.mean(ProjectKey.TOTAL_BUDGET).alias("budget_avg"),
    )

    # 加上 year、 month、quarter 列
    result_df = append_columns(
        result_df,
        {
            "year": func.lit(year if year else -1),
            "month": func.lit(month if month else -1),
            "quarter": func.lit(quarter if quarter else -1),
        },
    )

    return result_df
