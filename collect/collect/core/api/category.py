import json
from datetime import datetime

from collect.collect.core.api import POSTBaseApi


class CategoryApi(POSTBaseApi):

    base_url = "http://www.ccgp-guangxi.gov.cn/portal/category"

    @staticmethod
    def generate_body(
        page_no: int,
        page_size: int,
        category_code: str,
        publish_date_begin: str,
        publish_date_end: str,
    ) -> str:
        """
        返回请求体的json
        :param category_code:
        :param page_no:
        :param page_size:
        :param publish_date_begin:
        :param publish_date_end:
        :return:
        """
        return json.dumps(
            {
                "pageNo": page_no,
                "pageSize": page_size,
                "categoryCode": category_code,
                "publishDateBegin": publish_date_begin,
                "publishDateEnd": publish_date_end,
                "_t": int(datetime.now().timestamp()),
            }
        )
