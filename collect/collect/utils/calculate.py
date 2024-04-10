from decimal import Decimal, getcontext


# ============ 金额解析/计算 ==============

def decimal_subtract(a: str, b: str) -> str:
    """
    减法
    :param a:
    :param b:
    :return:
    """
    return str(Decimal(a) - Decimal(b))


def try_float(string: str):
    try:
        return float(string)
    except ValueError:
        return None


def startswith_digital(string: str) -> bool:
    """
    检查是否以数字开头
    :param string:
    :return:
    """
    if len(string) == 0:
        return False
    return string[0].isdigit()


def parse_string_with_unit(string: str) -> float:
    """
    解析带单位的字符串
    :param string:
    :return:
    """
    has_dot = False
    integer, decimal = 0, 0
    idx = 0.1
    for i in string:
        if i.isdigit():
            if has_dot:
                decimal += int(i) * idx
                idx /= 10
            else:
                integer = integer * 10 + int(i)
            has_dot = False
        elif i == '.':
            if has_dot:
                raise ValueError(f'{string} has double dots')
            has_dot = True
        else:
            break
    return integer + decimal


def parse_unit(string: str) -> float:
    """
    解析单位
    :param string:
    :return:
    """
    if '%' in string:
        return 0
    if "亿" in string:
        return 1_0000_0000
    if "万" in string:
        return 1_0000
    return 1


if __name__ == '__main__':
    pass
