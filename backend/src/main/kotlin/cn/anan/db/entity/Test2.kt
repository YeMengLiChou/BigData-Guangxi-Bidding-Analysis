package cn.anan.db.entity

import org.ktorm.dsl.QueryRowSet
import org.ktorm.schema.BaseTable
import org.ktorm.schema.double
import org.ktorm.schema.int
import org.ktorm.schema.varchar


class Test2(
    val districtCode: String,
    val year: Int,
    val month: Int,
    val day: Int,
    val quarter: Int,
    val transactionVolume: Double
)


object Test2Table: BaseTable<Test2>("test2") {
    val districtCode = varchar("district_code")
    val year = int("year")
    val month = int("month")
    val day = int("day")
    val quarter = int("quarter")
    val transactionsVolume = double("transactions_volume")
    override fun doCreateEntity(row: QueryRowSet, withReferences: Boolean): Test2 = Test2(
        districtCode = row[districtCode] ?: "0",
        year = row[year] ?: 0,
        month = row[month] ?: 0,
        day = row[day] ?: 0,
        quarter = row[quarter] ?: 0,
        transactionVolume = row[transactionsVolume] ?: 0.0
    )
}

