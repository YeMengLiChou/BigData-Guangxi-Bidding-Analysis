from pyspark.sql import DataFrame, GroupedData
from pyspark.sql import functions as func

from analyse.core import common
from analyse.schemas import BID_ITEM_SCHEMA
from constants import ProjectKey, DevConstants, BidItemKey
from utils import dataframe_tools


def suppliers_occurrences(df: DataFrame) -> DataFrame:
    """
    统计供应商的出现次数

    +-------------+---------+-----+----+-----+-------+
    |district_code|supplier |count|year|month|quarter|
    +-------------+---------+-----+----+-----+-------+
    """
    df = (
        # 将 bid_items 列表解开，与当前列合并成多条完整的数据
        df.select(
            ProjectKey.DISTRICT_CODE,
            ProjectKey.SCRAPE_TIMESTAMP,
            func.explode(ProjectKey.BID_ITEMS).alias("bid_items"),
        )
        # 选择 地区 和 供应商 字段
        .select(
            ProjectKey.DISTRICT_CODE,
            ProjectKey.SCRAPE_TIMESTAMP,
            func.col(f"bid_items.{BidItemKey.SUPPLIER}").alias("supplier"),
        )
        # 过滤掉供应商为空的数据
        .filter(func.col("supplier").isNotNull())
    )

    df = common.add_time_columns(df)

    days_df = df.groupby(
        ProjectKey.DISTRICT_CODE, "supplier", "year", "month", "day"
    ).count()
    months_df = df.groupby(
        ProjectKey.DISTRICT_CODE, "supplier", "year", "month"
    ).count()
    quarters_df = df.groupby(
        ProjectKey.DISTRICT_CODE, "supplier", "year", "quarter"
    ).count()
    years_df = df.groupby(ProjectKey.DISTRICT_CODE, "supplier", "year").count()

    district_df = dataframe_tools.union_dataframes(
        union_dfs=[days_df, months_df, quarters_df, years_df],
        callback=common.complete_time_columns,
        by_name=True,
    )

    province_df = (
        district_df.withColumn(
            ProjectKey.DISTRICT_CODE, func.col(DevConstants.DISTRICT_CODE_GUANGXI)
        )
        .groupby(
            ProjectKey.DISTRICT_CODE, "supplier", "year", "month", "day", "quarter"
        )
        .agg(func.sum("*").alias("count"))
    )
    return district_df.unionByName(province_df)


def supplier_transactions_volume(
    df: DataFrame,
) -> DataFrame:
    """
    统计 供应商 总的交易量 和 中标个数

    +-------------+--------+-------------------+-------------+----+-----+-------+
    |district_code|supplier|transactions_volume|bidding_count|year|month|quarter|
    +-------------+--------+-------------------+-------------+----+-----+-------+

    """
    df = (
        df.select(
            ProjectKey.DISTRICT_CODE,
            ProjectKey.SCRAPE_TIMESTAMP,
            ProjectKey.TOTAL_BUDGET,
            ProjectKey.IS_WIN_BID,
            func.explode(ProjectKey.BID_ITEMS).alias("bid_items"),
        )
        .select(
            ProjectKey.DISTRICT_CODE,
            ProjectKey.TOTAL_BUDGET,
            ProjectKey.SCRAPE_TIMESTAMP,
            func.col(f"bid_items.{BidItemKey.AMOUNT}").alias("amount"),
            func.col(f"bid_items.{BidItemKey.SUPPLIER}").alias("supplier"),
            func.col(f"bid_items.{BidItemKey.IS_PERCENT}").alias("is_percent"),
            func.col(f"bid_items.{BidItemKey.IS_WIN}").alias("is_win"),
        )
        # 过滤出 中标公告 && 中标标项 && 金额大于 0
        .filter(
            (func.col(ProjectKey.IS_WIN_BID))
            & (func.col("is_win"))
            & (func.col("amount") >= 0)
        )
        # 如果 is_percent 为 True，那么计算当前标项的金额
        .withColumn(
            "amount",
            func.when(
                func.col("is_percent"),
                func.col("amount") * func.col(ProjectKey.TOTAL_BUDGET),
            ).otherwise(func.col("amount")),
        )
        .drop("is_win", "is_percent")
    )
    df = common.add_time_columns(df).drop(ProjectKey.SCRAPE_TIMESTAMP)

    def stats(gd: GroupedData) -> DataFrame:
        return gd.agg(
            func.sum("amount").alias("transactions_volume"),
            func.count("*").alias("bidding_count"),
        )

    days_df = stats(
        df.groupby(ProjectKey.DISTRICT_CODE, "supplier", "year", "month", "day")
    )
    months_df = stats(df.groupby(ProjectKey.DISTRICT_CODE, "supplier", "year", "month"))
    quarters_df = stats(
        df.groupby(ProjectKey.DISTRICT_CODE, "supplier", "year", "quarter")
    )
    year_df = stats(df.groupby(ProjectKey.DISTRICT_CODE, "supplier", "year"))

    district_df = dataframe_tools.union_dataframes(
        union_dfs=[days_df, months_df, quarters_df, year_df],
        callback=common.complete_time_columns,
        by_name=True,
    )

    province_df = (
        district_df.withColumn(
            ProjectKey.DISTRICT_CODE, func.lit(DevConstants.DISTRICT_CODE_GUANGXI)
        )
        .groupby(
            ProjectKey.DISTRICT_CODE, "supplier", "year", "month", "day", "quarter"
        )
        .agg(
            func.sum("transactions_volume").alias("transactions_volume"),
            func.count("*").alias("bidding_count"),
        )
    )

    return district_df.unionByName(province_df)
