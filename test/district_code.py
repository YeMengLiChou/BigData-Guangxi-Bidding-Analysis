import requests


def dfs(data, step: int):
    if data is None:
        return
    code = data["code"]
    print("\t" * step + code)
    if not data.get("isLeaf", True):
        for i in data["children"]:
            dfs(i, step + 1)


def request_data():
    url = (
        "http://www.ccgp-guangxi.gov.cn/api/core/remote/announcementDistrict?includeSelf=false&districtCode=450000"
        "&queryWithCode=true&includeAllNode=true&filterNotActive=true&timestamp=1708259649"
    )
    res = requests.get(url=url).json()
    for i in res["data"]:
        dfs(i, 0)


if __name__ == "__main__":
    request_data()
