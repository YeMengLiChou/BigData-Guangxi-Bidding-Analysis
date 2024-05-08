package cn.anan.db.vo


data class TransactionScaleItem(
    val idx: Int,
    val value: Double
)

// day为单位的数据
data class TransactionScaleDayItem(
    val day: Int,
    val month: Int,
    val value: Double
)


data class TransactionScaleYearItem(
    val year: Int,
    val days: List<TransactionScaleDayItem>,
    val months: List<TransactionScaleItem>,
    val quarters: List<TransactionScaleItem>
)

data class TransactionScaleData(
   val data: List<TransactionScaleYearItem>
)

