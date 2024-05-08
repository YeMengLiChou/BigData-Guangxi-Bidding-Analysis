package cn.anan.routes

import cn.anan.common.ApiResult
import cn.anan.service.ProcurementMethodService
import io.ktor.server.application.*
import io.ktor.server.response.*
import io.ktor.server.routing.*

fun Route.procurementMethodApi() {
    route("method") {
        get("stats") {
            call.respond(
                ApiResult.success(
                    data = ProcurementMethodService.getProcurementMethodStats()
                )
            )
        }
    }
}