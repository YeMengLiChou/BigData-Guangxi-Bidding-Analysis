import datetime
import json
import time

import requests


def send_request(page_no: int):
    res = requests.post(
        "http://www.ccgp-guangxi.gov.cn/portal/category",
        data=json.dumps(
            {
                "pageNo": page_no,
                "pageSize": 100,
                "publishDateBegin": "2022-01-01",
                "publishDateEnd": "2024-04-25",
                "categoryCode": "ZcyAnnouncement2",
                "_t": int(datetime.datetime.now().timestamp() * 1000),
            }
        ),
        headers={"Content-Type": "application/json"},
    )
    data = res.json()['result']['data']
    total = data['total']
    print(total, page_no, len(data['data']))
    print(data['data'][-1]['publishDate'])

# total 54162
if __name__ == "__main__":
    # for i in range(1, 54162 // 100 + 2):
    #     try:
    #         send_request(i)
    #         time.sleep(0.5)
    #     except BaseException as e:
    #         break
    send_request(100)