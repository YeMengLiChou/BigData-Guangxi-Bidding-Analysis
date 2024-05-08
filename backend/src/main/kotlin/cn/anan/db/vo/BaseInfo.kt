package cn.anan.db.vo

data class BaseInfo(
    val announcementCount: Int,
    val transactionsVolume: Double,
    val transactionsCount: Int,
    val latestTimestamp: Long,
    val supplierCount: Int,
    val announcementCountData: List<Int>,
    val transactionsCountData: List<Int>,
    val transactionsVolumeData: List<Double>
)

// 第一部分：全部的公告数
// 第二部分：成交公告数
// 第三部分：成交总金额
// 第四部分：供应商个数