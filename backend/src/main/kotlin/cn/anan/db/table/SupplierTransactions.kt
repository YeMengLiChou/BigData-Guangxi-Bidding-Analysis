package cn.anan.db.table

import cn.anan.common.UNKNOWN_VALUE
import org.ktorm.dsl.QueryRowSet
import org.ktorm.schema.*

data class SupplierTransactions(
    val districtCode: Int,
    val supplier: String,
    val year: Int,
    val month: Int,
    val day: Int,
    val quarter: Int,
    val transactionsVolume: Double,
    val biddingCount: Int,
    val id: Int
)


object SupplierTransactionsTable: BaseTable<SupplierTransactions>("supplier_transactions") {
    val districtCode = int("district_code")
    val supplier = varchar("supplier")
    val year = int("year")
    val month = int("month")
    val day = int("day")
    val quarter = int("quarter")
    val transactionsVolume = double("transactions_volume")
    val biddingCount = int("bidding_count")
    val id = int("id")

    override fun doCreateEntity(row: QueryRowSet, withReferences: Boolean): SupplierTransactions {
        return SupplierTransactions (
            districtCode = row[BiddingStatsTable.districtCode]!!,
            supplier = row[supplier]!!,
            year = row[BiddingStatsTable.year]!!,
            month = row[BiddingStatsTable.month]!!,
            day = row[BiddingStatsTable.day]!!,
            quarter = row[BiddingStatsTable.quarter]!!,
            transactionsVolume = row[transactionsVolume]!!,
            biddingCount =  row[biddingCount]!!,
            id = row[id]!!
        )
    }
}