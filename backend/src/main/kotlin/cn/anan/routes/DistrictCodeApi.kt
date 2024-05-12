package cn.anan.routes

import cn.anan.common.ApiResult
import cn.anan.common.transformApiParam
import cn.anan.db.table.DistrictCode
import cn.anan.service.DistrictCodeService
import io.ktor.server.application.*
import io.ktor.server.request.*
import io.ktor.server.response.*
import io.ktor.server.routing.*

/**
 * 地区代码相关的 api
 * */
fun Route.districtCodeApi() {
    route("/districtCode") {

        /**
         * 返回所有数据
         * */
        get("/all") {
            val data = DistrictCodeService.fetchAll()
            call.respond(ApiResult.success(data))
        }

        /**
         * 返回根据 type 返回的数据
         * */
        get("/classify") {
            val type = call.transformApiParam {
                parameters["type"]!!.toShort()
            }
            call.respond(
                ApiResult.success(
                    data = DistrictCodeService.fetchByType(type = type)
                )
            )
        }

        /**
         * 以树的形式返回数据
         * */
        get("/tree") {
            val code: Int = call.transformApiParam {
                parameters["code"]!!.toInt()
            }
            call.respond(
                ApiResult.success(
                    data = DistrictCodeService.fetchTreeByCode(code)
                )
            )
        }
        /**
         * 插入多条数据
         * */
        post("/adds") {
            val list: List<DistrictCode> = call.transformApiParam {
                receive<List<DistrictCode>>()
            }
            DistrictCodeService.insertOrUpdates(list)
            call.respond(ApiResult.success(null))
        }
        /**
         * 获取所有的市级城市数据
         * */
        get("/city") {
            call.respond(ApiResult.success(data  = DistrictCodeService.fetchCities()))
        }
    }


}