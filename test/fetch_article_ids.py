import json


def fetch_from_txt(path: str) -> list[tuple[str, bool, str]]:
    """
    从 txt 中读取所有的 ids
    :param path:
    :return:
    """
    ids = []
    with open(path, mode="r", encoding="utf-8") as f:
        while line := f.readline():
            if len(line) == 0 or line.isspace() or line.startswith("#"):
                continue
            first_space_idx, second_space_idx = line.find(" "), line.find(
                " ", line.find(" ") + 1
            )
            article_id = line[:first_space_idx]
            win = bool(line[first_space_idx + 1 : second_space_idx])
            reason = line[second_space_idx + 1 :].strip()
            ids.append((article_id, win, reason))
    return ids


def fetch_from_json(path: str, dst_path: str, append: bool = True):
    """
    从 parse_error.json 中读取所有出错的 ids
    :param append: 追加（不重复），False为直接覆盖
    :param path:
    :param dst_path:
    :return:
    """
    with open(path, mode="r", encoding="utf-8") as f:
        data = json.load(f)

    old_ids = fetch_from_txt(dst_path)
    new_ids = []
    for item in data:
        comment = item["msg"]
        article_info = item["article_info"]
        if "start_article(win)" in article_info:
            article_id = article_info["start_article(win)"]
            win = True
        else:
            article_id = article_info["start_article(not win)"]
            win = False
        value = (article_id, win, comment)
        if append:
            if value not in old_ids:
                new_ids.append(value)
        else:
            new_ids.append(value)

    with open(dst_path, mode="a" if append else "w", encoding="utf-8") as f:
        for item in new_ids:
            f.write(f"{item[0]} {item[1]} {item[2]}\n")


def dumps_txt_to_py(path: str, dst_path: str):
    """
    将 txt 的内容转化到 py 中
    :param path:
    :param dst_path:
    :return:
    """
    ids = fetch_from_txt(path)
    with open(dst_path, mode="w", encoding="utf-8") as f:
        f.write("ids = [\n")
        for item in ids:
            f.write(f'    ("{item[0]}", {item[1]}),  # {item[2]}\n')
        f.write("]\n")


if __name__ == "__main__":
    fetch_from_json(
        path="../logs/parse_errors.json",
        dst_path="./error_article_ids.txt",
        append=False,
    )
    dumps_txt_to_py(
        path="./error_article_ids.txt",
        dst_path="../collect/collect/spiders/error_article_ids.py",
    )
