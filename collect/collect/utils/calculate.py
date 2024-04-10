from decimal import Decimal, getcontext


def decimal_subtract(a: str, b: str) -> str:
    """
    减法
    :param a:
    :param b:
    :return:
    """
    return str(Decimal(a) - Decimal(b))
