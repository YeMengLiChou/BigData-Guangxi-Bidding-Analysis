package cn.anan.db.vo

/**
 * 单个item：
 * @param name 采购方法的名称
 * @param count 对应的值
 * */
data class ProcurementMethodItem(
    val name: String,
    val count: Int,
    val amount: Double,
)

/**
 * 年数据
 * */
data class ProcurementMethodYearData(
    val year: Int,
    val value: MutableList<ProcurementMethodItem>
)

