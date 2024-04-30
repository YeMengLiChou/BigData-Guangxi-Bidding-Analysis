from pyspark.sql import DataFrame, GroupedData
from pyspark.sql import functions as func

from analyse.core import common
from constants import ProjectKey


def transactions_total_volume_all(
    df: DataFrame,
) -> DataFrame:
    """
    统计每年、每个月、每日、每季度的交易总量
    +-------------+----+-----+---+--------------------+-------+
    |district_code|year|month|day|transactions_volume |quarter|
    +-------------+----+-----+---+--------------------+-------+
    """
    df = (
        df.select(
            ProjectKey.SCRAPE_TIMESTAMP,
            ProjectKey.DISTRICT_CODE,
            ProjectKey.TOTAL_AMOUNT,
            ProjectKey.IS_WIN_BID,
        )
        # 过滤出中标数据
        .filter(func.col(ProjectKey.IS_WIN_BID)).drop(ProjectKey.IS_WIN_BID)
    )

    def agg_func(gd: GroupedData, columns: list[str]) -> DataFrame:
        if ProjectKey.TOTAL_AMOUNT in columns:
            return gd.agg(
                func.sum(ProjectKey.TOTAL_AMOUNT).alias("transactions_volume")
            )
        else:
            return gd.agg(func.sum("transactions_volume").alias("transactions_volume"))

    return common.stats_all(
        df, groupby_cols=[ProjectKey.DISTRICT_CODE], agg_func=agg_func
    )
