package cn.anan.db.vo

data class SupplierDetail(
    val name: String,
    val address: String,
    val catalogs: List<Item<Int>>,
    val transactionVolumes: List<Double>,
    val biddingCount: List<Int>
)
