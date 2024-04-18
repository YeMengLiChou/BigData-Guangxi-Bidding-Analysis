class SwitchError(Exception):
    """
    切换到另一个结果公告进行搜索
    """

    def __init__(self, msg):
        super().__init__(msg)
