import json


def log_json(
    logger: callable,
    data: dict,
):
    """
    输出 json 格式数据
    :param data:
    :param logger:
    :return:
    """
    logger(json.dumps(data, indent=4, ensure_ascii=False))