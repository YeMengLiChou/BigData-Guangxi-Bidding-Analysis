from pyspark.sql import DataFrame, GroupedData
from pyspark.sql import functions as func
from pyspark.sql import window
from analyse.core import common
from constants import ProjectKey, BidItemKey


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

    def agg_fun(gd: GroupedData, columns: list[str]) -> DataFrame:
        if "count" not in columns:
            return gd.agg(func.count("*").alias("count"))
        else:
            return gd.agg(func.sum("count").alias("count"))

    return common.stats_all(
        df=df,
        groupby_cols=[ProjectKey.DISTRICT_CODE, "supplier"],
        agg_func=agg_fun,
    )


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
                func.col("amount")
                * func.when(func.col(ProjectKey.TOTAL_BUDGET) < 0, 0).otherwise(
                    func.col(ProjectKey.TOTAL_BUDGET)
                ),
            ).otherwise(func.col("amount")),
        )
        .drop("is_win", "is_percent")
    )

    def agg_func(gd: GroupedData, columns: list[str]) -> DataFrame:
        if "amount" in columns:
            return gd.agg(
                func.sum("amount").alias("transactions_volume"),
                func.count("*").alias("bidding_count"),
            )
        else:
            return gd.agg(
                func.sum("transactions_volume").alias("transactions_volume"),
                func.sum("bidding_count").alias("bidding_count"),
            )

    return common.stats_all(
        df=df, groupby_cols=[ProjectKey.DISTRICT_CODE, "supplier"], agg_func=agg_func
    )


def supplier_situations(df: DataFrame) -> DataFrame:
    """
    供应生和其采购种类的个数
    """
    df = (
        df.select(ProjectKey.CATALOG, func.explode(ProjectKey.BID_ITEMS).alias("items"))
        .select(
            ProjectKey.CATALOG,
            func.col(f"items.{BidItemKey.SUPPLIER}").alias("supplier"),
        )
        .filter(func.col("supplier").isNotNull())
        .groupby("supplier", ProjectKey.CATALOG)
        .agg(func.count("*").alias("count"))
    )
    return df


def supplier_address(df: DataFrame) -> DataFrame:
    df = (
        df.select(func.explode(ProjectKey.BID_ITEMS).alias("items"))
        .select(
            func.col(f"items.{BidItemKey.SUPPLIER}").alias("supplier"),
            func.col(f"items.{BidItemKey.SUPPLIER_ADDRESS}").alias("address"),
        )
        .filter(func.col("supplier").isNotNull())
        .groupby("supplier", "address")
        .sum()
        .dropDuplicates(["supplier"])  # 去掉重复的供应商
        .filter(func.length("supplier") >= 2)
    )
    return df
