package cn.anan.db.table

import org.ktorm.dsl.QueryRowSet
import org.ktorm.schema.*

/**
 * 成交公告的信息实体
 * */
data class BiddingAnnouncement(
    val title: String?,
    val purchaseTitle: String?,
    val projectName: String?,
    val projectCode: String?,
    val resultSourceArticleId: String?,
    val purchaseSourceArticleId: String?,
    val scrapeTimestamp: Long,
    val districtCode: Int,
    val districtName: String?,
    val author: String?,
    val catalog: String?,
    val procurementMethod: String?,
    val bidOpeningTime: Long?,
    val isWinBid: Boolean,
    val resultArticleIds: String,
    val resultPublishDates: String,
    val purchaseArticleIds: String,
    val purchasePublishDates: String,
    val totalBudget: Double,
    val totalAmount: Double,
    val bidItems: String,
    val purchaser: String,
    val purchasingAgency: String,
    val reviewExperts: String,
    val purchaseRepresentatives: String,
    val isTermination: Boolean,
    val terminationReason: String?,
    val tenderDuration: Long,
    val id: Int,
)


/**
 * 数据库中 bidding_announcement 对应的表结构
 * */
object BiddingAnnouncements: BaseTable<BiddingAnnouncement>("bidding_announcement") {
    val resultSourceArticleId = varchar("result_source_article_id")
    val purchaseSourceArticleId = varchar("purchase_source_article_id")
    val title = varchar("title")
    val purchaseTitle = varchar("purchase_title")
    val scrapeTimestamp = long("scrape_timestamp")
    val projectName = varchar("project_name")
    val projectCode = varchar("project_code")
    val districtCode = int("district_code")
    val districtName = varchar("district_name")
    val author = varchar("author")
    val catalogCol = varchar("catalog")
    val procurementMethod = varchar("procurement_method")
    val bidOpeningTime = long("bid_opening_time")
    val isWinBId = short("is_win_bid")
    val resultArticleIds = varchar("result_article_id")
    val resultPublishDates = varchar("result_publish_date")
    val purchaseArticleIds = varchar("purchase_article_id")
    val purchasePublishDates = varchar("purchase_publish_date")
    val bidItems = varchar("bid_items")
    val totalBudget = double("total_budget")
    val totalAmount = double("total_amount")
    val tenderDuration = long("tender_duration")
    val purchaser = varchar("purchase")
    val purchasingAgency = varchar("purchasing_agency")
    val reviewExperts = varchar("review_expert")
    val purchaseRepresentatives = varchar("purchase_representative")
    val isTermination = short("is_termination")
    val terminationReason = varchar("termination_reason")
    val id = int("id").primaryKey()

    private const val EMPTY_JSON_ARRAY = "[]"

    override fun doCreateEntity(row: QueryRowSet, withReferences: Boolean): BiddingAnnouncement {
        return BiddingAnnouncement(
            resultSourceArticleId = row[resultSourceArticleId],
            purchaseSourceArticleId = row[purchaseSourceArticleId],
            title = row[title],
            purchaseTitle = row[purchaseTitle],
            scrapeTimestamp = row[scrapeTimestamp] ?: -1,
            projectCode = row[projectCode],
            projectName = row[projectName],
            districtCode = row[districtCode] ?: -1,
            districtName = row[districtName],
            author = row[author],
            catalog = row[catalogCol],
            procurementMethod = row[procurementMethod],
            bidOpeningTime = row[bidOpeningTime],
            isWinBid = row[isWinBId]?.equals(1.toShort()) ?: false,
            resultArticleIds = row[resultArticleIds] ?: EMPTY_JSON_ARRAY,
            resultPublishDates = row[resultPublishDates] ?: EMPTY_JSON_ARRAY,
            purchaseArticleIds = row[purchaseArticleIds] ?: EMPTY_JSON_ARRAY,
            purchasePublishDates = row[purchasePublishDates] ?: EMPTY_JSON_ARRAY,
            bidItems = row[bidItems]?: EMPTY_JSON_ARRAY,
            totalBudget = row[totalBudget] ?: -1.0,
            totalAmount = row[totalAmount] ?: -1.0,
            tenderDuration = row[tenderDuration] ?: 0L,
            purchaser = row[purchaser] ?: "",
            purchasingAgency = row[purchasingAgency] ?: "",
            reviewExperts = row[reviewExperts] ?: EMPTY_JSON_ARRAY,
            purchaseRepresentatives = row[purchaseRepresentatives] ?: EMPTY_JSON_ARRAY,
            isTermination =  row[isTermination]?.equals(1.toShort()) ?: false,
            terminationReason = row[terminationReason],
            id = row[id] ?: -1
        )
    }
}