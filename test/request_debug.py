import json
import time
import urllib.parse

import requests


def request_detail(article_id: str):
    article_id = urllib.parse.unquote(article_id)
    article_id = urllib.parse.quote(article_id)
    res = requests.get(f"http://www.ccgp-guangxi.gov.cn/portal/detail?articleId={article_id}&parentId"
                       f"=66485&timestamp={int(time.time() * 1000)}", timeout=10)
    if res.status_code == 200:
        json_data = json.loads(res.text)
        if json_data['success']:
            data = json_data['result']['data']
            if data:
                print(f"current_article_id: {data['articleId']}")
                other_announcement = data['announcementLinkDtoList']
                print("other_announcements: ")
                idx = 1
                for item in other_announcement:
                    if item['isExist']:
                        print(
                            f"\t{idx}.{item['typeName']}: {item['articleId']} {'(current)' if item['isCurrent'] else ''}",
                            end='')
                        print(
                            f"http://www.ccgp-guangxi.gov.cn/site/detail?parentId=66485&articleId={item['articleId']}")
                        idx += 1
            else:
                print("无数据")
        else:
            print("服务器响应失败")
    else:
        print("请求失败")


if __name__ == '__main__':
    request_detail("9Nl264NBe3kToCeHa1bpog==")
