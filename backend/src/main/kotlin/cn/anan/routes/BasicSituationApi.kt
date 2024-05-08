package cn.anan.routes

import cn.anan.common.ApiResult
import cn.anan.service.BasicSituationService
import io.ktor.server.application.*
import io.ktor.server.response.*
import io.ktor.server.routing.*


fun Route.baseSituationApi() {

    route("/base") {
        /**
         * 获取总体基本情况：
         * */
        get {
            call.respond(
                ApiResult.success(
                    data = BasicSituationService.getBasicSituation()
                )
            )
        }

        /**
         * 获取采购规模
         * */
        get("/scale") {
            call.respond(
                ApiResult.success(
                    data = BasicSituationService.getScaleWithYearsAndMonths()
                )
            )
        }
    }

}