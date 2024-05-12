package cn.anan.db.vo

import cn.anan.db.table.BiddingDistrictStats

/**
 * 一年的各级成交金额量
 * */
data class BiddingDistrictYearStats(
    val year: Int,
    val stats: BiddingDistrictStats
)
