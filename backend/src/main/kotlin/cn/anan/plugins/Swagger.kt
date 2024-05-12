package cn.anan.plugins

import io.ktor.server.application.*
import io.ktor.server.plugins.openapi.*
import io.ktor.server.plugins.swagger.*
import io.ktor.server.routing.*

fun Application.configureSwagger() {

    routing {
        /**
         * SwaggerUI 页面
         * @author Anan
         * */
        swaggerUI("swagger", "openapi/documentation.yaml") {
            // configure
        }
        /**
         * OpenAPI 页面
         * @author Anan
         * */
        openAPI("openapi", "openapi/documentation.yaml") {
            // configure
        }
    }
}