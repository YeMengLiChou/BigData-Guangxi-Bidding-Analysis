package cn.anan.db.tables

import org.ktorm.dsl.from
import org.ktorm.dsl.select
import org.ktorm.schema.Table
import org.ktorm.schema.double
import org.ktorm.schema.int
import org.ktorm.schema.varchar

object Test2Table: Table<Nothing>("test2") {
    val districtCode = varchar("district_code")
    val year = int("year")
    val month = int("month")
    val day = int("day")
    val quarter = int("quarter")
    val transactionsVolume = double("transactions_volume")
}

