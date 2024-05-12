package cn.anan.db.table

import cn.anan.common.UNKNOWN_VALUE
import org.ktorm.dsl.QueryRowSet
import org.ktorm.schema.BaseTable
import org.ktorm.schema.int

data class BiddingStats(
    val districtCode: Int,
    val year: Int,
    val month: Int,
    val day: Int,
    val quarter: Int,
    val winCount: Int,
    val loseCount: Int,
    val terminateCount: Int,
    val id: Int
)



object BiddingStatsTable: BaseTable<BiddingStats>("bidding_stats") {
    val districtCode = int("district_code")
    val year = int("year")
    val month = int("month")
    val day = int("day")
    val quarter = int("quarter")
    val winCount = int("win_count")
    val loseCount = int("lose_count")
    val terminateCount = int("terminate_count")
    val id = int("id")

    override fun doCreateEntity(row: QueryRowSet, withReferences: Boolean): BiddingStats {
        return BiddingStats(
            districtCode = row[districtCode]!!,
            year = row[year]!!,
            month = row[month]!!,
            day = row[day]!!,
            quarter = row[quarter]!!,
            winCount =  row[winCount]!!,
            loseCount = row[loseCount]!!,
            terminateCount = row[terminateCount]!!,
            id = row[id]!!
        )
    }
}