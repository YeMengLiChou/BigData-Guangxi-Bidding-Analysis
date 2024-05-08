package cn.anan.routes

import cn.anan.common.ApiResult
import cn.anan.common.transformApiParam
import cn.anan.db.entity.PageRequest
import cn.anan.service.SupplierService
import io.ktor.server.application.*
import io.ktor.server.response.*
import io.ktor.server.routing.*

fun Route.agencyApi() {
    route("/agency") {
        get {
            val pageReq = call.transformApiParam {
                PageRequest.createFromParameters(parameters)
            }
//            call.respond(
//                ApiResult.success(
//                    data =
//                )
//            )
        }
    }
}