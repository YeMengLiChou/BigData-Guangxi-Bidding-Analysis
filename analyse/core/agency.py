from pyspark.sql import DataFrame, functions as func

from constants import ProjectKey


def agency_stats(df: DataFrame) -> DataFrame:
    """
    代理商
    """
    return (
        df.select(ProjectKey.PURCHASER_AGENCY)
        .filter(
            func.col(ProjectKey.PURCHASER_AGENCY).isNotNull()
            & (func.length(ProjectKey.PURCHASER_AGENCY) > 1)
        )
        .groupby(ProjectKey.PURCHASER_AGENCY)
        .count()
    )


def agency_catalogs_stats(df: DataFrame) -> DataFrame:
    """
    代理商+类型
    """
    return (
        df.select(ProjectKey.PURCHASER_AGENCY, ProjectKey.CATALOG)
        .filter(
            func.col(ProjectKey.PURCHASER_AGENCY).isNotNull()
            & (func.length(ProjectKey.PURCHASER_AGENCY) > 1)
        )
        .groupby(ProjectKey.PURCHASER_AGENCY, ProjectKey.CATALOG)
        .count()
        .dropDuplicates([ProjectKey.PURCHASER_AGENCY])
    )
