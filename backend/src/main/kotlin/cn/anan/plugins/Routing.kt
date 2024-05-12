package cn.anan.plugins

import cn.anan.routes.*
import io.ktor.server.application.*
import io.ktor.server.resources.Resources
import io.ktor.server.routing.*

fun Application.configureRouting() {
    install(Resources)
    routing {
        route("/api") {
            districtCodeApi()
            baseSituationApi()
            biddingAnnouncementApi()
            supplierApi()
            agencyApi()
            procurementMethodApi()
            transactionsStatsApi()
        }
    }
}
