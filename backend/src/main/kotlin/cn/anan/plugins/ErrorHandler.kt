package cn.anan.plugins

import cn.anan.common.ApiException
import cn.anan.common.ApiResult
import io.ktor.http.*
import io.ktor.server.application.*
import io.ktor.server.plugins.statuspages.*
import io.ktor.server.response.*

/**
 * 全局异常处理
 * */
fun Application.configureErrorHandle() {

    install(StatusPages) {
        exception<ApiException> { call, cause ->
            call.respond(ApiResult.failure(cause.code, cause.msg))
        }

        status(HttpStatusCode.NotFound) { call, cause ->

        }
    }
}