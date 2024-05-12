package cn.anan.service

import cn.anan.common.GUANGXI_STATS_DISTRICT_CODE
import cn.anan.db.database
import cn.anan.db.table.ProcurementMethodStatsTable
import cn.anan.db.vo.ProcurementMethodItem
import cn.anan.db.vo.ProcurementMethodYearData
import org.ktorm.dsl.*

object ProcurementMethodService {

    /**
     * 获取相关公告数以及交易数
     * */
    fun getProcurementMethodStats(): List<ProcurementMethodYearData> {
        // 统计每一年的个数和交易量
        val countResult = HashMap<Int, ProcurementMethodYearData>()
        database.from(ProcurementMethodStatsTable).select().where {
            (ProcurementMethodStatsTable.month eq 0)
                .and(ProcurementMethodStatsTable.quarter eq 0)
                .and(ProcurementMethodStatsTable.districtCode eq GUANGXI_STATS_DISTRICT_CODE)
        }.map {
            ProcurementMethodStatsTable.createEntity(it)
        }.forEach {
            if (!countResult.containsKey(it.year)) {
                countResult[it.year] = ProcurementMethodYearData(year = it.year, value = mutableListOf())
            }
            val name = if (it.procurementMethod == "null") {
                "其他-未知"
            } else {
                it.procurementMethod
            }
            countResult[it.year]?.value?.add(ProcurementMethodItem(name = name, count = it.count, amount = it.totalAmount))
        }
        return countResult.values.toList()
    }
}