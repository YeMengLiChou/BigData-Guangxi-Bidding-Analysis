from pyspark.sql import DataFrame, functions as func, GroupedData
from pyspark.sql.types import IntegerType
from analyse.core import common
from constants import ProjectKey, DevConstants
from utils import dataframe_tools as df_utils, dataframe_tools


def __win_bidding_result(df: DataFrame) -> DataFrame:
    # 过滤中标的结果
    df = df.filter(func.col(ProjectKey.IS_WIN_BID)).drop(ProjectKey.IS_WIN_BID)

    def agg_func(gd: GroupedData, columns: list[str]) -> DataFrame:
        if "win_count" not in columns:
            return gd.agg(func.count("*").alias("win_count"))
        else:
            return gd.agg(func.sum("win_count").alias("win_count"))

    return common.stats_all(
        df, groupby_cols=[ProjectKey.DISTRICT_CODE], agg_func=agg_func
    )


def __lose_bidding_result(df: DataFrame) -> DataFrame:
    # 过滤废标结果
    df = df.filter(func.col("is_lose_bid")).drop("is_lose_bid")

    def agg_func(gd: GroupedData, columns: list[str]) -> DataFrame:
        if "lose_count" not in columns:
            return gd.agg(func.count("*").alias("lose_count"))
        else:
            return gd.agg(func.sum("lose_count").alias("lose_count"))

    return common.stats_all(
        df, groupby_cols=[ProjectKey.DISTRICT_CODE], agg_func=agg_func
    )


def __terminate_bidding_result(df: DataFrame) -> DataFrame:
    # 过滤终止结果
    df = df.filter(func.col(ProjectKey.IS_TERMINATION)).drop(ProjectKey.IS_TERMINATION)

    def agg_func(gd: GroupedData, columns: list[str]) -> DataFrame:
        if "terminate_count" not in columns:
            return gd.agg(func.count("*").alias("terminate_count"))
        else:
            return gd.agg(func.sum("terminate_count").alias("terminate_count"))

    return common.stats_all(
        df, groupby_cols=[ProjectKey.DISTRICT_CODE], agg_func=agg_func
    )


def bidding_result(
    df: DataFrame,
) -> DataFrame:
    """
    统计中标、废标、终止数量

    +-------------+-----------+----------+----------+---------------+----+-----+-------+
    |district_code|total_count|wins_count|lose_count|terminate_count|year|month|quarter|
    +-------------+-----------+----------+----------+---------------+----+-----+-------+

    ----------
    :param df
    """
    win_df = __win_bidding_result(
        df.select(
            ProjectKey.DISTRICT_CODE, ProjectKey.SCRAPE_TIMESTAMP, ProjectKey.IS_WIN_BID
        )
    )
    lose_df = __lose_bidding_result(
        df.select(
            ProjectKey.DISTRICT_CODE,
            ProjectKey.SCRAPE_TIMESTAMP,
            ProjectKey.IS_WIN_BID,
            ProjectKey.IS_TERMINATION,
        )
        .withColumn(
            "is_lose_bid",
            (~func.col(ProjectKey.IS_WIN_BID)) & (~func.col(ProjectKey.IS_TERMINATION)),
        )
        .select(ProjectKey.DISTRICT_CODE, ProjectKey.SCRAPE_TIMESTAMP, "is_lose_bid")
    )

    terminate_df = __terminate_bidding_result(
        df.select(
            ProjectKey.DISTRICT_CODE,
            ProjectKey.SCRAPE_TIMESTAMP,
            ProjectKey.IS_TERMINATION,
        )
    )

    res_df = dataframe_tools.join_dataframes(
        dfs=[win_df, lose_df, terminate_df],
        depend_on=[ProjectKey.DISTRICT_CODE, "year", "month", "day", "quarter"],
        how_join="left_outer",
    )

    res_df = dataframe_tools.replace_null(
        res_df, ["win_count", "lose_count", "terminate_count"], 0
    )

    return res_df


def bidding_budget_situation(df: DataFrame) -> DataFrame:
    """
    统计所有数据中 各地区的总预算的最大值、总值、平均值

    +-------------+----------+----------+----------+----------+----------+----------+----+-----+-------+
    |district_code|amount_sum|amount_max|amount_avg|budget_sum|budget_max|budget_avg|year|month|quarter|
    +-------------+----------+----------+----------+----------+----------+----------+----+-----+-------+

    ----------
    :param df
    """

    amount_col = func.col(ProjectKey.TOTAL_AMOUNT)
    budget_col = func.col(ProjectKey.TOTAL_BUDGET)

    # 拿到指定的数据
    df = df.select(
        ProjectKey.DISTRICT_CODE,
        ProjectKey.TOTAL_AMOUNT,
        ProjectKey.TOTAL_BUDGET,
        ProjectKey.SCRAPE_TIMESTAMP,
    ).filter((amount_col >= 0) | (budget_col >= 0))

    # 过滤掉负数和Null的值
    df = df.withColumn(
        ProjectKey.TOTAL_AMOUNT,
        func.when(amount_col.isNull(), 0).when(amount_col < 0, 0).otherwise(amount_col),
    ).withColumn(
        ProjectKey.TOTAL_BUDGET,
        func.when(budget_col.isNull(), 0).when(budget_col < 0, 0).otherwise(budget_col),
    )

    # # 统计数据：总值、最大值、平均值
    # result_df = df.groupby(groupby_cols).agg(
    #     func.sum(ProjectKey.TOTAL_AMOUNT).alias("amount_sum"),
    #     func.max(ProjectKey.TOTAL_AMOUNT).alias("amount_max"),
    #     func.mean(ProjectKey.TOTAL_AMOUNT).alias("amount_avg"),
    #     func.sum(ProjectKey.TOTAL_BUDGET).alias("budget_sum"),
    #     func.max(ProjectKey.TOTAL_BUDGET).alias("budget_max"),
    #     func.mean(ProjectKey.TOTAL_BUDGET).alias("budget_avg"),
    # )
    pass
    # return result_df


def bidding_district_type(df: DataFrame) -> DataFrame:
    """
    地区类型个数：省级、市级、区级
    +----------------+---------------+--------------+
    |provincial_count|municipal_count|district_count|
    +----------------+---------------+--------------+
    |0               |177            |1532          |
    +----------------+---------------+--------------+

    """

    district_code_col = func.col(ProjectKey.DISTRICT_CODE)
    total_amount_col = func.col(ProjectKey.TOTAL_AMOUNT)
    df = (
        df.select(
            district_code_col.cast(IntegerType()),
            ProjectKey.SCRAPE_TIMESTAMP,
            ProjectKey.TOTAL_AMOUNT,
        )
        # 省级，等于 GUANGXI_DISTRICT_CODE
        .withColumn(
            "provincial_level",
            district_code_col == DevConstants.DISTRICT_CODE_GUANGXI,
        )
        # 市级，模100为0
        .withColumn(
            "municipal_level",
            (
                (district_code_col.__mod__(100) == 0)
                | (district_code_col.__mod__(100) == 99)
            )
            & (district_code_col != DevConstants.DISTRICT_CODE_GUANGXI),
        )
        # 区级：模100不为0
        .withColumn("district_level", district_code_col.__mod__(100) != 0).withColumn(
            ProjectKey.TOTAL_AMOUNT,
            func.when(
                (total_amount_col.isNull() | (total_amount_col < 0)), 0
            ).otherwise(total_amount_col),
        )
    )
    # 统计总个数
    total_count = df.count()
    total_df = df.agg(
        func.sum(ProjectKey.TOTAL_AMOUNT).alias("total_amount")
    ).withColumn("total_count", func.lit(total_count))

    provincial_df = (
        df.filter(func.col("provincial_level"))
        .groupby("provincial_level")
        .agg(
            func.count("provincial_level").alias("provincial_count"),
            func.sum(ProjectKey.TOTAL_AMOUNT).alias("provincial_amount"),
        )
    ).drop("provincial_level")

    if provincial_df.count() == 0:
        provincial_df = dataframe_tools.create_dataframe(data=[{"provincial_count": 0}])

    municipal_df = (
        df.filter(func.col("municipal_level"))
        .groupby("municipal_level")
        .agg(
            func.count("municipal_level").alias("municipal_count"),
            func.sum(ProjectKey.TOTAL_AMOUNT).alias("municipal_amount"),
        )
    ).drop("municipal_level")

    if municipal_df.count() == 0:
        municipal_df = dataframe_tools.create_dataframe(data=[{"municipal_count": 0}])

    district_df = (
        df.filter(func.col("district_level"))
        .groupby("district_level")
        .agg(
            func.count("district_level").alias("district_count"),
            func.sum(ProjectKey.TOTAL_AMOUNT).alias("district_amount"),
        )
    ).drop("district_level")

    if district_df.count() == 0:
        district_df = dataframe_tools.create_dataframe(data=[{"district_count": 0}])

    result_df = dataframe_tools.join_dataframes(
        dfs=[provincial_df, municipal_df, district_df, total_df],
        depend_on=None,
        how_join="cross",
    )

    return result_df
