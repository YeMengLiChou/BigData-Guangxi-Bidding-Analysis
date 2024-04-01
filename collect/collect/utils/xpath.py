def first_element(src, express: str):
    """
    返回第一个元素，如果没有则返回None
    :param src:
    :param express:
    :return:
    """
    result = src.xpath(express)
    if len(result) > 0:
        return result[0]
    else:
        return None
