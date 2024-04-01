from abc import ABC

__all__ = [
    "purchase",
    "common",
    "result",
    "AbstractFormatParser"
]


class AbstractFormatParser(ABC):
    @staticmethod
    def parse_bids_information(part: list[str]) -> dict:
        """
        解析中标信息
        :param part:
        :return:
        """
        raise NotImplementedError()

    @staticmethod
    def parse_review_expert(part: list[str]) -> dict:
        """
        解析评审专家信息
        :param part:
        :return:
        """
        raise NotImplementedError()

    @staticmethod
    def parse_project_base_situation(part: list[str]) -> dict:
        """
        解析 项目基本情况 部分
        :param part:
        :return:
        """
        raise NotImplementedError()

    @staticmethod
    def parse_project_contact(part: list[str]) -> dict:
        """
        解析 联系方式 部分
        :param part:
        :return:
        """
        raise NotImplementedError()
