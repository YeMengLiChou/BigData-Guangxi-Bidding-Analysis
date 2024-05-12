package cn.anan.routes

import cn.anan.common.ApiResult
import cn.anan.common.transformApiParam
import cn.anan.db.entity.PageRequest
import cn.anan.service.BiddingAnnouncementService
import io.ktor.server.application.*
import io.ktor.server.response.*
import io.ktor.server.routing.*


fun Route.biddingAnnouncementApi() {

    route("bidding") {
        /**
         * 分页查询公告信息
         * */
        get {
            val page = call.transformApiParam {
                PageRequest.createFromParameters(this.parameters)!!
            }
            val districtCode: Int = call.parameters["districtCode"]?.toInt() ?: 0
            val year: Int = call.parameters["year"]?.toInt() ?: 0
            val month: Int = call.parameters["month"]?.toInt() ?: 0
            val day: Int = call.parameters["day"]?.toInt() ?: 0
            val quarter: Int = call.parameters["quarter"]?.toInt() ?: 0

            call.respond(
                ApiResult.success(
                    data = BiddingAnnouncementService.fetchPageByTimeAndDistrictCode(
                        page,
                        districtCode,
                        year,
                        month,
                        day,
                        quarter
                    )
                )
            )
        }
        /**
         * 返回省级、市级、区级的成交量
         * */
        get("level") {
            call.respond(
                ApiResult.success(
                    data = BiddingAnnouncementService.fetchBiddingDistrictLevel()
                )
            )
        }
        /**
         * 返回各年份的公告数
         * */
        get("count") {
            call.respond(
                ApiResult.success(
                    data = BiddingAnnouncementService.fetchBiddingCountWithYears()
                )
            )
        }

    }
}