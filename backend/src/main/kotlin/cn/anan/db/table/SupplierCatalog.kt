package cn.anan.db.table

import cn.anan.common.UNKNOWN_VALUE
import org.ktorm.dsl.QueryRowSet
import org.ktorm.schema.BaseTable
import org.ktorm.schema.int
import org.ktorm.schema.varchar

data class SupplierCatalog(
    val supplier: String,
    val catalog: String,
    val count: Int,
    val id: Int
)


object SupplierCatalogTable: BaseTable<SupplierCatalog>("supplier_catalogs") {
    val supplier = varchar("supplier")
    val catalogCol = varchar("catalog")
    val count = int("count")
    val id = int("id")

    override fun doCreateEntity(row: QueryRowSet, withReferences: Boolean): SupplierCatalog {
        return SupplierCatalog(
            supplier = row[supplier]?:"",
            catalog = row[catalogCol] ?: "",
            count = row[count] ?: UNKNOWN_VALUE,
            id = row[id] ?: UNKNOWN_VALUE
        )
    }
}