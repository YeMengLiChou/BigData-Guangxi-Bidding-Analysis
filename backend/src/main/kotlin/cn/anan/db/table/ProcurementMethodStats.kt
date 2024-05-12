package cn.anan.db.table

import org.ktorm.dsl.QueryRowSet
import org.ktorm.schema.BaseTable
import org.ktorm.schema.*

data class ProcurementMethodStats(
    val districtCode: Int,
    val procurementMethod: String,
    val year: Int,
    val month: Int,
    val day: Int,
    val quarter: Int,
    val count: Int,
    val totalAmount: Double,
    val id: Int
)


object ProcurementMethodStatsTable: BaseTable<ProcurementMethodStats>("procurement_stats") {
    val districtCode = int("district_code")
    val procurementMethod =varchar("procurement_method")
    val year = int("year")
    val month = int("month")
    val day = int("day")
    val quarter = int("quarter")
    val count = int("count")
    val totalAmount = double("total_amount")
    val id = int("id")
    override fun doCreateEntity(row: QueryRowSet, withReferences: Boolean): ProcurementMethodStats {
        return ProcurementMethodStats(
            districtCode = row[districtCode]!!,
            procurementMethod = row[procurementMethod] ?: "null",
            year = row[year]!!,
            month = row[month]!!,
            day = row[day]!!,
            quarter = row[quarter]!!,
            count = row[count]!!,
            totalAmount = row[totalAmount]!!,
            id = row[id]!!
        )
    }
}