package cn.anan.service

import cn.anan.common.ApiException
import cn.anan.common.Page
import cn.anan.common.StatusCode
import cn.anan.common.Validations
import cn.anan.db.database
import cn.anan.db.entity.PageRequest
import cn.anan.db.table.BiddingAnnouncement
import cn.anan.db.table.BiddingAnnouncements
import cn.anan.db.table.BiddingDistrictStats
import cn.anan.db.table.BiddingDistrictStatsTable
import org.ktorm.dsl.*
import java.util.*

object BiddingAnnouncementService {

    /**
     * 按照 [year]、[month]、[day]、[quarter] 时间以及 [districtCode] 来查询并分页数据
     * @param pageRequest
     * @param districtCode
     * @param year
     * @param month
     * @param day
     * @param quarter
     * @return Page<BiddingAnnouncement>
     * */
    fun fetchPageByTimeAndDistrictCode(
        pageRequest: PageRequest,
        districtCode: Int,
        year: Int,
        month: Int,
        day: Int,
        quarter: Int
    ): Page<BiddingAnnouncement> {
        if (!Validations.validatePage(pageRequest)) {
            throw ApiException(StatusCode.PARAMETER_ERROR)
        }

        val dateBegin: Calendar = Calendar.getInstance()
        val dateEnd: Calendar = Calendar.getInstance()
        dateBegin.clear()
        dateEnd.clear()
        if (year > 0) {
            if (month > 0) {
                if (day > 0) {
                    // 年-月-日
                    dateBegin.set(year, month - 1, day)
                    dateEnd.set(year, month - 1, day + 1)
                } else {
                    // 年-月
                    dateBegin.set(year, month - 1, 1)
                    dateEnd.set(year, month - 1, 1)
                }
            } else {
                if (quarter > 0) {
                    // 年-季度
                    dateBegin.set(year, quarter * 3 - 1, 1)
                    dateEnd.set(year, quarter * 3 + 2, 1)
                } else {
                    // 年
                    dateBegin.set(year, 0, 1)
                    dateEnd.set(year + 1, 0, 1)
                }
            }
        } else {
            // 时间设置为2022前，end不用管，默认为当前的时间
            dateBegin.set(2021, 0, 0)
            dateEnd.set(2025, 0, 0)
        }

        var condition = (dateBegin.time.time lte BiddingAnnouncements.scrapeTimestamp)
            .and(BiddingAnnouncements.scrapeTimestamp lt dateEnd.time.time)

        if (districtCode != 0) {
            condition = condition.and(BiddingAnnouncements.districtCode eq districtCode)
        }

        val totalCount = database
            .from(BiddingAnnouncements)
            .select(count(BiddingAnnouncements.id).aliased("count"))
            .where(condition)
            .map {
                it.getInt("count")
            }[0]

        val (offset, size) = pageRequest.getLimitOffset()
        val data = database
            .from(BiddingAnnouncements)
            .select()
            .limit(offset = offset, limit = size)
            .where(condition)
            .orderBy(BiddingAnnouncements.scrapeTimestamp.asc())
            .map {
                BiddingAnnouncements.createEntity(it)
            }
        return Page.success(totalCount, data)
    }


    /**
     * 获取省市区级的采购规模
     * */
    fun fetchBiddingDistrictLevel(): BiddingDistrictStats {
        val data = database
            .from(BiddingDistrictStatsTable)
            .select()
            .map {
                BiddingDistrictStatsTable.createEntity(it)
            }[0]
        return data
    }
}
