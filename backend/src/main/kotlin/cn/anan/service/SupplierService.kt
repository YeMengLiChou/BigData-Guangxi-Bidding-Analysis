package cn.anan.service

import cn.anan.common.ApiException
import cn.anan.common.StatusCode
import cn.anan.common.Validations
import cn.anan.db.database
import cn.anan.db.entity.PageRequest
import cn.anan.db.table.SupplierAddressTable
import cn.anan.db.table.SupplierCatalogTable
import cn.anan.db.table.SupplierTransactionsTable
import cn.anan.db.vo.Item
import org.ktorm.dsl.*

object SupplierService {

    fun fetchSupplierNameList(pageRequest: PageRequest): List<String> {
        if (!Validations.validatePage(pageRequest)) {
            throw ApiException(StatusCode.PARAMETER_ERROR)
        }
        val (offset, size) = pageRequest.getLimitOffset()
        val data = database
            .from(SupplierAddressTable)
            .select()
            .limit(offset, size)
            .map { it[SupplierAddressTable.supplier]!! }
        return data
    }

    private fun getSupplierCatalog(name: String): List<Item<Int>> {
        val catalogsData = database
            .from(SupplierCatalogTable)
            .select()
            .where {
                SupplierCatalogTable.supplier eq name
            }
            .map { SupplierCatalogTable.createEntity(it) }
            .map { Item(name=it.catalog, value = it.count) }
        return catalogsData
    }

    private fun getSupplierTransactionVolume(name: String) {
        val transactionVolumeData = database
            .from(SupplierTransactionsTable)
            .select()
            .where {
                SupplierTransactionsTable.supplier eq name

            }
            .map { SupplierTransactionsTable.createEntity(it) }
            .map {  }
    }
    fun fetchSupplierDetail(id: Int) {
        val item = database
            .from(SupplierAddressTable)
            .select()
            .where {
                SupplierAddressTable.id eq id
            }
            .map { SupplierAddressTable.createEntity(it) }
            .firstOrNull()

        if (item == null) {
            throw ApiException(StatusCode.NO_DATA)
        }

        val name = item.supplier
        val catalogData = getSupplierCatalog(name)








    }

}