import json
from datetime import datetime

from collect.collect.core.api import POSTBaseApi


class CategoryApi(POSTBaseApi):

    base_url = "http://www.ccgp-guangxi.gov.cn/portal/category"

    @staticmethod
    def generate_body(
        pageNo: int,
        pageSize: int,
        categoryCode: str,
        publishDateBegin: str,
        publishDateEnd: str,
    ) -> str:
        """
        返回请求体的json
        :param categoryCode:
        :param pageNo:
        :param pageSize:
        :param publishDateBegin:
        :param publishDateEnd:
        :return:
        """
        return json.dumps(
            {
                "pageNo": pageNo,
                "pageSize": pageSize,
                "categoryCode": categoryCode,
                "publishDateBegin": publishDateBegin,
                "publishDateEnd": publishDateEnd,
                "_t": int(datetime.now().timestamp()),
            }
        )
