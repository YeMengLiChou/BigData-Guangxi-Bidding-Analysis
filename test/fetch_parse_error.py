import json
import sys
import json
import time
import urllib.parse

import requests


def request_detail(article_id: str):
    article_id = urllib.parse.unquote(article_id)
    article_id = urllib.parse.quote(article_id)
    res = requests.get(
        f"http://www.ccgp-guangxi.gov.cn/portal/detail?articleId={article_id}&parentId"
        f"=66485&timestamp={int(time.time() * 1000)}",
        timeout=10,
    )
    if res.status_code == 200:
        json_data = json.loads(res.text)
        if json_data["success"]:
            data = json_data["result"]["data"]
            if data:
                print(f"current_article_id: {data['articleId']}")
                other_announcement = data["announcementLinkDtoList"]
                print("other_announcements: ")
                idx = 1
                for item in other_announcement:
                    if item["isExist"]:
                        print(
                            f"\t{idx}.{item['typeName']}: {item['articleId']} {'(current)' if item['isCurrent'] else ''}",
                            end="",
                        )
                        print(
                            f"http://www.ccgp-guangxi.gov.cn/site/detail?parentId=66485&articleId={item['articleId']}"
                        )
                        idx += 1
            else:
                print("无数据")
        else:
            print("服务器响应失败")
    else:
        print("请求失败")


def load_from_json(json_path: str):
    with open(json_path, "r", encoding="utf-8") as f:
        content = f.read()
        # if content.endswith(","):
        #     content = content[:-1] + "]"
        return content


def dumps_to_console(content: str):
    json_data = json.loads(content)
    for i in range(0, len(json_data)):
        item = json_data[i]
        if item["msg"].startswith("基本情况解析失败："):
            continue
        if not item['msg'].startswith("生成 item 时出现异常"):
            continue
        print(f"msg: {item['msg']}")
        print("article_info")
        article_info = item["article_info"]
        if "start_article(win)" in article_info:
            ids = article_info["start_article(win)"]
        else:
            ids = article_info["start_article(not win)"]

        for k, v in article_info.items():
            print(f"\t{k}: {v}")

        print("error: ", item["error"])
        print("content: ", json.dumps(item["content"], ensure_ascii=False, indent=4))
        print("Traceback (most recent call last):")
        for line in item["exc_info"]:
            print(
                line.replace(
                    "/home/ecs-user/project/", "D:\\Project\\Python\\"
                ).replace("/", "\\"),
                end="",
            )

        request_detail(article_id=ids)
        print(
            f"{i}------------------------------------------------------------------------------------------------\n"
        )
        input("enter to next: ")


if __name__ == "__main__":
    dumps_to_console(content=load_from_json(json_path="./../logs/parse_errors.json1"))
    # print(1 / 0)
