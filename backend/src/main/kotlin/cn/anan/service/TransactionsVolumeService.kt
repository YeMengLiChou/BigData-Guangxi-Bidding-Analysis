package cn.anan.service

import cn.anan.common.GUANGXI_DISTRICT_CODE
import cn.anan.common.GUANGXI_STATS_DISTRICT_CODE
import cn.anan.db.database
import cn.anan.db.table.*
import cn.anan.db.vo.DistrictTransactionGrowthItem
import cn.anan.db.vo.TransactionGrowthItem
import cn.anan.db.vo.TransactionVolumeDistrictItem
import cn.anan.db.vo.TransactionVolumeDistrictYear
import org.ktorm.dsl.*
import org.ktorm.logging.detectLoggerImplementation
import java.util.*

object TransactionsVolumeService {
    val logger = detectLoggerImplementation()

    /**
     * 获取指定的 [districtCode] 以及其子级的数据
     * */
    private fun getDistrictCodes(districtCode: Int? = null): Map<Int, DistrictCode> {
        val districtCodeData = HashMap<Int, DistrictCode>()

        database
            .from(DistrictCodes)
            .select()
            .whereWithConditions {
                districtCode?.let { code ->
                    it.add((DistrictCodes.code eq code).or(DistrictCodes.parentCode eq code))
                }
            }
            .map { DistrictCodes.createEntity(it) }
            .forEach {
                districtCodeData[it.code] = it
            }
        return districtCodeData
    }

    /**
     * 获取所有市级地区的成交总量
     * */
    fun fetchTransactionVolumesWithAllCities(): List<TransactionVolumeDistrictYear> {
        val districtCodeData = getDistrictCodes()
        val data = database
            .from(TransactionVolumeTable)
            .select()
            .where {
                (TransactionVolumeTable.districtCode neq GUANGXI_STATS_DISTRICT_CODE)
                    .and(TransactionVolumeTable.districtCode neq GUANGXI_DISTRICT_CODE)
                    .and(TransactionVolumeTable.year neq 0)
                    .and(TransactionVolumeTable.month eq 0)
                    .and(TransactionVolumeTable.quarter eq 0)
            }
            .map { TransactionVolumeTable.createEntity(it) }
            // 用 year 分类
            .groupBy { it.year }
            // 对于每个 year 对应的交易量转换为vo
            .map {
                // 市级区域对应其总值
                val cityData = HashMap<Int, Double>()
                it.value.forEach { transactionItem ->
                    // 当前 item 的地区
                    val districtCode = districtCodeData[transactionItem.districtCode]!!
                    // 如果是区级，将数据加到其父级上（市级）
                    if (districtCode.type == DistrictCodeType.DISTRICT.type) {
                        cityData.compute(districtCode.parentCode) { _, v ->
                            return@compute v?.plus(transactionItem.transactionVolume)
                                ?: transactionItem.transactionVolume
                        }
                    } else {
                        cityData.compute(transactionItem.districtCode) { _, v ->
                            return@compute v?.plus(transactionItem.transactionVolume)
                                ?: transactionItem.transactionVolume
                        }
                    }
                }
                // 把 99 结尾的加到 00部分
                val keys = cityData.keys.toList()
                keys.forEach { key ->
                    if (key % 100 == 99) {
                        val preVal = cityData.remove(key)!!
                        cityData.compute(key - 99) { _, v ->
                            return@compute v?.plus(preVal) ?: preVal
                        }
                    }
                }

                // 转换为 vo
                TransactionVolumeDistrictYear(
                    year = it.key,
                    // 将cityData转换为列表，key为地区代码，value为交易量
                    data = cityData.map { item ->
                        TransactionVolumeDistrictItem(
                            districtCode = item.key,
                            districtName = districtCodeData[item.key]!!.name,
                            volume = item.value
                        )
                    }
                )
            }.toMutableList()
        val totalData = HashMap<Int, Double>()
        data.forEach { item ->
            item.data.forEach {
                if (totalData[it.districtCode] == null) {
                    totalData[it.districtCode] = 0.0
                }
                totalData[it.districtCode] = totalData[it.districtCode]!! + it.volume
            }
        }
        data.add(
            TransactionVolumeDistrictYear(year = 10000, data = totalData.map {
                TransactionVolumeDistrictItem(
                    districtCode = it.key,
                    districtName = districtCodeData[it.key]!!.name.removeSuffix("本级"),
                    volume = it.value
                )
            })
        )
        return data
    }

    /**
     * 获取某个城市下面地区的所有城市
     * */
    fun fetchTransactionVolumesByDistrictCode(districtCode: Int): Any {
        val childrenDistrictCode = getDistrictCodes(districtCode)
        val data = database
            .from(TransactionVolumeTable)
            .select()
            .where {
                (TransactionVolumeTable.districtCode neq GUANGXI_STATS_DISTRICT_CODE)
                    .and(TransactionVolumeTable.year neq 0)
                    .and(TransactionVolumeTable.month eq 0)
                    .and(TransactionVolumeTable.quarter eq 0)
                    .and(TransactionVolumeTable.districtCode.inList(childrenDistrictCode.values.map { it.code }))
            }
            .map { TransactionVolumeTable.createEntity(it) }
            // 用 year 分类
            .groupBy { it.year }
            // 对于每个 year 对应的交易量转换为vo
            .map {
                TransactionVolumeDistrictYear(
                    year = it.key,
                    // 将cityData转换为列表，key为地区代码，value为交易量
                    data = it.value.map { item ->
                        TransactionVolumeDistrictItem(
                            districtCode = item.districtCode,
                            districtName = childrenDistrictCode[item.districtCode]!!.name.removeSuffix("本级"),
                            volume = item.transactionVolume
                        )
                    }
                )
            }.toMutableList()
        // 统计总体数据
        val totalData = HashMap<Int, Double>()
        data.forEach { item ->
            item.data.forEach {
                if (totalData[it.districtCode] == null) {
                    totalData[it.districtCode] = 0.0
                }
                totalData[it.districtCode] = totalData[it.districtCode]!! + it.volume
            }
        }
        data.add(
            TransactionVolumeDistrictYear(year = 10000, data = totalData.map {
                TransactionVolumeDistrictItem(
                    districtCode = it.key,
                    districtName = childrenDistrictCode[it.key]!!.name.removeSuffix("本级"),
                    volume = it.value
                )
            })
        )
        return data
    }

    /***
     * 获取所有市级地区的增长情况
     * */
    fun fetchAllCitiesTransactionGrowth(): List<DistrictTransactionGrowthItem> {
        val districtCode = getDistrictCodes()
        val data = database
            .from(TransactionVolumeTable)
            .select()
            .where {
                (TransactionVolumeTable.month neq 0)
                    .and(TransactionVolumeTable.day eq 0)
                    .and(TransactionVolumeTable.districtCode neq GUANGXI_DISTRICT_CODE)
                    .and(TransactionVolumeTable.districtCode neq GUANGXI_STATS_DISTRICT_CODE)
            }
            .map { TransactionVolumeTable.createEntity(it) }
            // 按照地区分离
            .groupBy { it.districtCode }
            .toMutableMap()

        data.keys.toList().forEach {
            // 将 99 结尾算到 00 结尾的
            if (it % 100 == 99) {
                val preVal = data.remove(it)!!
                data.compute(it - 99) { _, v ->
                    return@compute v?.plus(preVal) ?: preVal
                }
            } else {
                // 把区级的算到市级的
                val currentDistrict = districtCode[it]!!
                if (currentDistrict.type == DistrictCodeType.DISTRICT.type) {
                    val preVal = data.remove(it)!!
                    val parentCode = if (currentDistrict.parentCode % 100 == 99) {
                        currentDistrict.parentCode - 99
                    } else {
                        currentDistrict.parentCode
                    }
                    data.compute(parentCode) { _, v ->
                        return@compute v?.plus(preVal) ?: preVal
                    }
                }
            }
        }
        // 一个地区对应着所有的月度数据
        return data.map { outerItem ->
            val calendar = Calendar.getInstance().apply { clear() }
            var preValue: TransactionGrowthItem? = null

            // value 是该地区的所有数据
            val growthItems = outerItem.value.groupBy {
                it.year * 100 + it.month // 将同一时间的归纳起来
            }.mapValues { item ->
                item.value.sumOf {
                    it.transactionVolume
                }
            }.map {
                val year = it.key / 100
                val month = it.key % 100
                TransactionVolume(
                    year = year,
                    month = month,
                    day = 0,
                    quarter = 0,
                    id = 0,
                    transactionVolume = it.value,
                    districtCode =  outerItem.key
                )
            }
            // 按时间顺序排
            .sortedWith(Comparator { a, b ->
                return@Comparator if (a.year == b.year) a.month - b.month else a.year - b.year
            })
            .map { volumeItem ->
                // 计算时间
                calendar.set(volumeItem.year, volumeItem.month, 1)
                // 转换为增长的部分
                TransactionGrowthItem(
                    timestamp = calendar.time.time,
                    value = preValue?.value?.plus(volumeItem.transactionVolume) ?: volumeItem.transactionVolume
                ).also {
                    preValue = it
                }
            }
            return@map DistrictTransactionGrowthItem(
                districtName = districtCode[outerItem.key]!!.name,
                districtCode = outerItem.key,
                data = growthItems
            )
        }


    }


}