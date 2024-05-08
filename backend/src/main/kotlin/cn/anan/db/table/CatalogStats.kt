package cn.anan.db.table

import cn.anan.common.UNKNOWN_VALUE
import org.ktorm.dsl.QueryRowSet
import org.ktorm.schema.BaseTable
import org.ktorm.schema.int
import org.ktorm.schema.varchar

data class CatalogStats(
    val catalog: String,
    val count: Int,
    val id: Int,
)


object CatalogStatsTable: BaseTable<CatalogStats>("catalog_stats") {
    val catalogCol = varchar("catalog")
    val count = int("count")
    val id = int("id")
    override fun doCreateEntity(row: QueryRowSet, withReferences: Boolean): CatalogStats {
        return CatalogStats(
            catalog = row[catalogCol] ?: "",
            count = row[count]!!,
            id = row[id]!!
        )
    }
}