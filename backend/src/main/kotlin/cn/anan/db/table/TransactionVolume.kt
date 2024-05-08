package cn.anan.db.table

import cn.anan.common.UNKNOWN_VALUE
import org.ktorm.dsl.QueryRowSet
import org.ktorm.schema.BaseTable
import org.ktorm.schema.double
import org.ktorm.schema.int


/**
 *
 * 交易量实体
 * */
data class TransactionVolume(
    val year: Int,
    val month: Int,
    val day: Int,
    val quarter: Int,
    val id: Int,
    val transactionVolume: Double,
    val districtCode: Int,
)


/**
 * 交易量对应 transactions_volumes 的表结构
 * */
object TransactionVolumeTable: BaseTable<TransactionVolume>("transactions_volumes") {
    val year = int("year")
    val day  =int("day")
    val month = int("month")
    val quarter = int("quarter")
    val districtCode = int("district_code")
    val transactionVolume = double("transactions_volume")
    val id = int("id").primaryKey()

    override fun doCreateEntity(row: QueryRowSet, withReferences: Boolean): TransactionVolume {
        return TransactionVolume(
            districtCode = row[districtCode] ?: UNKNOWN_VALUE,
            year = row[year] ?: UNKNOWN_VALUE,
            month = row[month] ?: UNKNOWN_VALUE,
            day = row[day] ?: UNKNOWN_VALUE,
            quarter = row[quarter] ?: UNKNOWN_VALUE,
            transactionVolume = row[transactionVolume] ?: UNKNOWN_VALUE.toDouble(),
            id = row[id] ?: UNKNOWN_VALUE
        )
    }
}