package cn.anan.db.table

import cn.anan.common.UNKNOWN_VALUE
import org.ktorm.dsl.QueryRowSet
import org.ktorm.schema.BaseTable
import org.ktorm.schema.int
import org.ktorm.schema.varchar

data class SupplierAddress(
    val supplier: String,
    val address: String,
    val id: Int,
)


object SupplierAddressTable: BaseTable<SupplierAddress>("supplier_address") {
    val supplier = varchar("supplier")
    val address = varchar("address")
    val id = int("id").primaryKey()

    override fun doCreateEntity(row: QueryRowSet, withReferences: Boolean): SupplierAddress {
        return SupplierAddress(
            supplier = row[supplier] ?: "",
            address = row[address] ?: "",
            id = row[id] ?: UNKNOWN_VALUE
        )
    }
}

