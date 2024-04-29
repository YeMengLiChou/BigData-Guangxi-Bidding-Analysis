"""
过滤掉不需要再次爬取的公告，在一开始的时候load进redis中
"""

filtered_ids = [
    "WVEaLTxHvaFk829mJatpPg==",
    "vO7fxAlkywh/eHWfSQI6hw==",
    "/2JMSjxMgMotWErogH9qCw==",  # 结果公告和采购公告的标项数量不匹配
    "SsAggK/18SqEKdBMVr63Zg==",  # 和上面相同的公告
    "Bux3LPIkySQ0N7M13F4RWQ==",  # 联系方式中同时出现“采购人”和“征集人”
    "74P+dQs89O9UQN8dDNUfMQ==",  # 该结果公告与采购公告的标项数量不匹配
    "2JmL/7gvUeJtiH3pQNWs+w==",  # 该结果公告与采购公告的标项数量不匹配
    "KLvWEWIdoa+Bxbd+qf+gPw==",  # 该结果公告与采购公告的标项数量不匹配
    "YGYkyqF1wsG9pBh9USC67A==",  # 该结果公告中标项过大，无法解析到
    "xK73WqCzkwBWZMfZm4l2xw==",  # 没有任何标项信息，在附件中无法解析
    "wok1any9uLOWaR7mUi4OcA==",  # 没有任何标项信息，在附件中无法解析
    "zsF6kDE+BB6FYSYw+k/R/A==",  # 没有任何标项信息，在附件中无法解析
    "9Vd13nS1mNs/FD37mUgEnw==",  # 资格审查公告，无标项信息.
    "Uj3s+af6mnQD1d5//Bf4sw==",  # 资格审查公告，无标项信息.
    "riqzZfQUeInYSzETCVoKMw==",  # 资格审查公告，无标项信息.
    "VdZhBUDBZOuLS5HCfii5nQ==",  # 资格审查公告，无标项信息.
]
