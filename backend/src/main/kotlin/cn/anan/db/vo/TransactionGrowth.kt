package cn.anan.db.vo

data class TransactionGrowthItem(
    val timestamp: Long,
    val value: Double
)


data class DistrictTransactionGrowthItem(
    val districtName: String,
    val districtCode: Int,
    val data: List<TransactionGrowthItem>
)

