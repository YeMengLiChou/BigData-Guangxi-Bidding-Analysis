package cn.anan

import cn.anan.db.initDatabase
import cn.anan.plugins.*
import io.ktor.server.application.*
import io.ktor.server.engine.*
import io.ktor.server.netty.*

fun main() {
    initDatabase()

    embeddedServer(Netty, port = 8080, host = "0.0.0.0", watchPaths = listOf("classes", "resources"), module = Application::module)
        .start(wait = true)
}

fun Application.module() {
    configureCORS()
    configureSerialization()
    configureErrorHandle()
    configureSwagger()
    configureRouting()
}