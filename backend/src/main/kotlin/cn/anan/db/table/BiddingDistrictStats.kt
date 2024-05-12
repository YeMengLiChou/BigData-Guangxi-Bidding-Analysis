package cn.anan.db.table

import org.ktorm.dsl.QueryRowSet
import org.ktorm.schema.*

data class BiddingDistrictStats(
    val provincialCount: Int,
    val provincialAmount: Double,
    val municipalCount: Int,
    val municipalAmount: Double,
    val districtCount: Int,
    val districtAmount: Double,
    val id: Int
)



object BiddingDistrictStatsTable: BaseTable<BiddingDistrictStats>("bidding_district_stats") {
    val provincialAmount = double("provincial_amount")
    val provincialCount = int("provincial_count")
    val municipalCount = int("municipal_count")
    val municipalAmount = double("municipal_amount")
    val districtCount = int("district_count")
    val districtAmount = double("district_amount")
    val id = int("id").primaryKey()
    override fun doCreateEntity(row: QueryRowSet, withReferences: Boolean): BiddingDistrictStats {
        return BiddingDistrictStats(
            provincialAmount = row[provincialAmount]!!,
            provincialCount = row[provincialCount]!!,
            municipalCount = row[municipalCount]!!,
            municipalAmount = row[municipalAmount]!!,
            districtAmount = row[districtAmount]!!,
            districtCount = row[districtCount]!!,
            id = row[id]!!,
        )
    }
}