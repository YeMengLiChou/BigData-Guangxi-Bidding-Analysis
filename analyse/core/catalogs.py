from pyspark.sql import DataFrame
from pyspark.sql import functions as func

from constants import ProjectKey


def catalog_stars(df: DataFrame) -> DataFrame:
    """
    统计种类的个数
    """
    return df.select(ProjectKey.CATALOG).groupby(ProjectKey.CATALOG).count()
