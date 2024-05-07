import json

import requests

"""
{
    "id": "2134",
    "parentId": "2133",
    "code": "450100",
    "name": "南宁市",
    "fullName": "广西壮族自治区南宁市",
    "fullPathName": "南宁市",
    "shortName": "广西南宁",
    "districtType": "010201",
    "isLeaf": false,
    "status": 0,
    "children": null
},
"""

district_codes = []
max_len = 0


def dfs(data, step: int, parent: int = -1):
    if data is None:
        return

    code = int(data["code"])
    # print("\t" * step + code + " " + data["fullName"])
    if code == 459900 or code == 450000:
        _type = 1
    elif code % 100 == 0 or code % 100 == 99:
        _type = 2
    else:
        _type = 3

    district_codes.append(
        {
            "code": code,
            "name": data["name"],
            "fullName": data["fullName"],
            "shortName": data["shortName"],
            "parentCode": parent,
            "type": _type,
        }
    )
    global max_len
    max_len = max(max_len, len(data["fullName"]))
    if not data.get("isLeaf", True):
        for i in data["children"]:
            dfs(i, step + 1, parent=code)


def request_data():
    url = (
        "http://www.ccgp-guangxi.gov.cn/api/core/remote/announcementDistrict?includeSelf=true&districtCode=450000"
        "&queryWithCode=true&includeAllNode=true&filterNotActive=true&timestamp=1708259649"
    )
    res = requests.get(url=url).json()
    for i in res["data"]:
        dfs(i, 0)
    print(json.dumps(district_codes, ensure_ascii=False))
    print(max_len)


if __name__ == "__main__":
    request_data()
