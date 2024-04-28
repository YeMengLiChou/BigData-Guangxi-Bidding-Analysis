from pyspark.sql import DataFrame
from pyspark.sql.streaming import StreamingQuery


def streaming_to_console(
    df: DataFrame, output_mode: str = "complete", truncate: bool = False, rows: int = 25
) -> StreamingQuery:
    """
    输出到控制台
    :param df:
    :param output_mode: 输出模式
    :param truncate: 是否截断过长的部分
    :param rows: 最多显示的行数
    """
    if not getattr(df, "isStreaming", False):
        raise ValueError("`df` must be a streaming DataFrame/Dataset!")
    return (
        df.writeStream.outputMode(output_mode)
        .format("console")
        .options(truncate=truncate, numRows=rows)
        .start()
    )


def batch_to_console(df: DataFrame, truncate: bool = False, row: int = 25):
    """
    将数据输出到控制台
    """
    if getattr(df, "isStreaming", False):
        raise ValueError("`df` must be not a streaming DataFrame/Dataset")
    return df.show(n=row, truncate=truncate)
