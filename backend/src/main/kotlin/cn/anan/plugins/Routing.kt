package cn.anan.plugins

import cn.anan.common.ApiException
import cn.anan.common.ApiResult
import io.ktor.resources.*
import io.ktor.server.application.*
import io.ktor.server.resources.*
import io.ktor.server.resources.Resources
import io.ktor.server.response.*
import io.ktor.server.routing.*
import kotlinx.serialization.Serializable

fun Application.configureRouting() {
    install(Resources)
    routing {
        get("/test") {
            throw ApiException(code=404, msg = "Not Found")
        }
        get("/test/1") {
            call.respondText("abc")
        }
    }
}
