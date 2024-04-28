from pyspark.sql import DataFrame
from pyspark.sql import functions as func
from constants import ProjectKey


def stats(df: DataFrame) -> list[DataFrame]:
    """
    统计各种数据的出现情况
    """

    # 公告发布者统计出现次数
    author_count = df.groupby(ProjectKey.AUTHOR).count()

    # 公告采购类型出现次数
    catalog_count = df.groupby(ProjectKey.CATALOG).count()

    # 采购方法的出现次数
    procurement_method_count = df.groupby(ProjectKey.PROCUREMENT_METHOD).count()

    # 成交、中标的出现次数
    is_win_count = df.groupby(ProjectKey.IS_WIN_BID).count()

    purchaser_count = df.groupby(ProjectKey.PURCHASER).count()

    purchase_agency_count = df.groupby(ProjectKey.PURCHASER_AGENCY).count()

    termination_count = df.groupby(ProjectKey.IS_TERMINATION).count()

    # 总预算
    total_amount_summary = (
        df.select(ProjectKey.TOTAL_BUDGET, ProjectKey.TOTAL_AMOUNT)
        .filter(
            (func.col(ProjectKey.TOTAL_BUDGET) > 0)
            & (func.col(ProjectKey.TOTAL_AMOUNT) > 0)
        )
        .summary()
    )

    return [
        # district_count,
        author_count,
        catalog_count,
        procurement_method_count,
        is_win_count,
        total_amount_summary,
    ]
