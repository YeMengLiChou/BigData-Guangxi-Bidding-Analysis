package cn.anan.db.vo




data class TransactionVolumeDistrictItem(
    val districtCode: Int,
    val districtName: String,
    val volume: Double,
)


data class TransactionVolumeDistrictYear(
    val year: Int,
    val data: List<TransactionVolumeDistrictItem>
)