package cn.anan.routes

import cn.anan.common.ApiResult
import cn.anan.common.transformApiParam
import cn.anan.service.TransactionsVolumeService
import com.google.protobuf.Api
import io.ktor.server.application.*
import io.ktor.server.response.*
import io.ktor.server.routing.*

fun Route.transactionsStatsApi() {

    route("/transaction") {
        /**
         * 返回所有市区的数据总数据
         * */
        get("/all") {
            call.respond(
                ApiResult.success(
                    data = TransactionsVolumeService.fetchTransactionVolumesWithAllCities()
                )
            )
        }

        get {
            val districtCode = call.transformApiParam {
                parameters["districtCode"]!!.toInt()
            }
            call.respond(
                ApiResult.success(
                    data = TransactionsVolumeService.fetchTransactionVolumesByDistrictCode(districtCode)
                )
            )
        }

        get("/growth") {
            call.respond(
                ApiResult.success(
                    data = TransactionsVolumeService.fetchAllCitiesTransactionGrowth()
                )
            )
        }
    }


}