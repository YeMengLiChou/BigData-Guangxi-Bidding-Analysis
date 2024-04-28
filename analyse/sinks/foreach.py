from pyspark.sql import DataFrame, Row
from abc import ABCMeta, abstractmethod


class ForeachWriter(ABCMeta):
    """
    用于 ``streaming.foreach`` 的基类
    """

    @abstractmethod
    def open(self, partition_id: int, epoch_id: int) -> bool:
        """
        当流开始时调用，用于初始化该类，比如数据库连接等，处理成功返回 True
        """
        pass

    @abstractmethod
    def process_row(self, row: Row):
        """
        处理流中的每一行数据
        """
        pass

    @abstractmethod
    def close(self, error):
        """
        当 ``process_row`` 出现异常时调用该方法
        """
        pass


def send_to_kafka(df: DataFrame):
    pass
