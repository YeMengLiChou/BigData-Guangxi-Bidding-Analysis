package cn.anan.service

import cn.anan.common.GUANGXI_STATS_DISTRICT_CODE
import cn.anan.db.database
import cn.anan.db.table.BiddingAnnouncements
import cn.anan.db.table.BiddingStatsTable
import cn.anan.db.table.SupplierAddressTable
import cn.anan.db.table.TransactionVolumeTable
import cn.anan.db.vo.*
import org.ktorm.dsl.*

object BasicSituationService {

    /**
     * 获取基本的数据
     * */
    fun getBasicSituation(): BaseInfo {
        // 数据总条数
        val totalCount = database
            .from(BiddingAnnouncements)
            .select(count(BiddingAnnouncements.id).aliased("count"))
            .map { it.getInt("count") }[0]

        // 成交个数
        val winCount = database
            .from(BiddingStatsTable)
            .select(sum(BiddingStatsTable.winCount).aliased("sum"))
            .where {
                (BiddingStatsTable.month eq 0)
                    .and(BiddingStatsTable.quarter eq 0)
                    .and(BiddingStatsTable.districtCode eq GUANGXI_STATS_DISTRICT_CODE)
            }.map { it.getInt("sum") }[0]

        // 最新数据
        val latestTimestamp = database
            .from(BiddingAnnouncements)
            .select(max(BiddingAnnouncements.scrapeTimestamp).aliased("latest"))
            .map { it.getLong("latest") }[0]

        // 总成交量
        val totalTransactionVolume = database
            .from(TransactionVolumeTable)
            .select(sum(TransactionVolumeTable.transactionVolume).aliased("sum"))
            .where {
                (TransactionVolumeTable.month eq 0)
                    .and(TransactionVolumeTable.day eq 0)
                    .and(TransactionVolumeTable.quarter eq 0)
                    .and(TransactionVolumeTable.districtCode eq GUANGXI_STATS_DISTRICT_CODE)
            }
            .map { it.getDouble("sum") }[0]


        // 过去季度的成交公告数量
        val totalCountData = database
            .from(BiddingStatsTable)
            .select()
            .where {
                (BiddingStatsTable.quarter neq 0)
                    .and(BiddingStatsTable.districtCode eq GUANGXI_STATS_DISTRICT_CODE)
            }.map { BiddingStatsTable.createEntity(it) }
            .sortedWith(Comparator { a, b ->
                if (a.year == b.year) return@Comparator a.quarter - b.quarter
                else return@Comparator a.year - b.year
            }).map {
                it.winCount + it.loseCount + it.terminateCount
            }


        // 过去每个季度的成交量
        val transactionVolumeData = database
            .from(TransactionVolumeTable)
            .select()
            .where {
                // 提取出全省每个季度的记录
                (TransactionVolumeTable.quarter neq 0)
                    .and(TransactionVolumeTable.districtCode eq GUANGXI_STATS_DISTRICT_CODE)
            }
            .map { TransactionVolumeTable.createEntity(it) }
            // 排序，从小到大
            .sortedWith(Comparator { a, b ->
                if (a.year == b.year) return@Comparator a.quarter - b.quarter
                else return@Comparator a.year - b.year
            }).map {
                it.transactionVolume
            }

        // 过去季度的成交公告数量
        val winCountData = database
            .from(BiddingStatsTable)
            .select()
            .where {
                (BiddingStatsTable.quarter neq 0)
                    .and(BiddingStatsTable.districtCode eq GUANGXI_STATS_DISTRICT_CODE)
            }.map { BiddingStatsTable.createEntity(it) }
            .sortedWith(Comparator { a, b ->
                if (a.year == b.year) return@Comparator a.quarter - b.quarter
                else return@Comparator a.year - b.year
            }).map {
                it.winCount
            }

        // 供应商的数量
        val supplierCount = database
            .from(SupplierAddressTable)
            .select(count().aliased("count"))
            .map { it.getInt("count") }[0]

        return BaseInfo(
            announcementCount = totalCount,
            transactionsCount = winCount,
            transactionsVolume = totalTransactionVolume,
            latestTimestamp = latestTimestamp,
            transactionsVolumeData = transactionVolumeData,
            transactionsCountData = winCountData,
            announcementCountData = totalCountData,
            supplierCount = supplierCount
        )

        // 供应商个数
        // 采购人个数
        // 代理机构个数
    }


    /**
     * 返回所有年的总交易量
     * */
    fun getScaleWithYearsAndMonths(): TransactionScaleData {
        val data = (2022 .. 2024).map { year ->
            val daysData = mutableListOf<TransactionScaleDayItem>()
            val monthsData = mutableListOf<TransactionScaleItem>()
            val quartersData = mutableListOf<TransactionScaleItem>()
            database
                .from(TransactionVolumeTable)
                .select()
                .where {
                    (TransactionVolumeTable.year eq year)
                        .and(TransactionVolumeTable.districtCode eq GUANGXI_STATS_DISTRICT_CODE)
                }
                .map { TransactionVolumeTable.createEntity(it) }
                .forEach {
                    if (it.day != 0) {
                        daysData.add(TransactionScaleDayItem(day = it.day, month = it.month, value = it.transactionVolume))
                    } else if (it.month != 0) {
                        monthsData.add(TransactionScaleItem(idx = it.month, value = it.transactionVolume))
                    } else if (it.quarter != 0) {
                        quartersData.add(TransactionScaleItem(idx = it.quarter, value = it.transactionVolume))
                    }
                }

            daysData.sortWith(Comparator {a, b ->
                if (a.month == b.month) return@Comparator a.day - b.day
                else return@Comparator a.month - b.month
            })
            monthsData.sortedWith(Comparator.comparingInt {a -> a.idx})
            quartersData.sortedWith(Comparator.comparingInt {a -> a.idx})

            TransactionScaleYearItem(
                year = year,
                days = daysData,
                months = monthsData,
                quarters = quartersData
            )
        }


        return TransactionScaleData(data)
    }

}