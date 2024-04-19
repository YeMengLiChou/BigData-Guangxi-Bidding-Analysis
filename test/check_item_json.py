import json

import constant.constants


def check_item_json(json_data: list):
    """
    测试 item 的数据是否存在缺漏
    :param json_data:
    :return:
    """
    keys = [item for item in dir(constant.constants) if item.startswith("KEY_")]
    project_keys = set(getattr(constant.constants, item) for item in keys if item.startswith("KEY_PROJECT_"))
    bid_item_keys = set(getattr(constant.constants, item) for item in keys if item.startswith("KEY_BID_ITEM_"))

    index = 0
    for item in json_data:
        ok = True
        dis = project_keys - item.keys()
        if len(dis) != 0:
            print(f"{item} \n 缺乏的 key {dis}\n")
            ok = False
        bid_items = item.get(constant.constants.KEY_PROJECT_BID_ITEMS, None)
        if not bid_items:
            print(f"{item} \n 缺少 bid_items")
            ok = False
        else:
            for bid_item in bid_items:
                bid_dis = bid_item_keys - bid_item.keys()
                if len(bid_dis) != 0:
                    print(f"{bid_item} \n 缺乏的 key {bid_dis}\n")
                    ok = False

        index += 1
        if not ok:
            print(f"{index} not ok {item[constant.constants.KEY_PROJECT_RESULT_ARTICLE_ID]}\n")

        government_purchase = item['is_government_purchase']
        if government_purchase:
            print("has")


def print_values(json_data: list):
    keys = [item for item in dir(constant.constants) if item.startswith("KEY_")]
    project_keys = set(getattr(constant.constants, item) for item in keys if item.startswith("KEY_PROJECT_"))
    bid_item_keys = set(getattr(constant.constants, item) for item in keys if item.startswith("KEY_BID_ITEM_"))

    for key in project_keys:
        print(f"---------{key}-------------")
        for item in json_data:
            print(f"{item[key]}")
        print()


if __name__ == '__main__':
    with open("../logs/item_debug.json", encoding="utf-8") as f:
        # check_item_json(json.load(f))
        data = json.load(f)
        # check_item_json(data)
        print_values(data)