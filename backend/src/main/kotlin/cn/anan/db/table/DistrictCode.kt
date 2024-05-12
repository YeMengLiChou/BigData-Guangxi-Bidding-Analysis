package cn.anan.db.table

import org.ktorm.dsl.QueryRowSet
import org.ktorm.schema.BaseTable
import org.ktorm.schema.int
import org.ktorm.schema.short
import org.ktorm.schema.varchar

/**
 * 地区代码实体
 * */
data class DistrictCode(
    val code: Int,
    val name: String,
    val fullName: String,
    val shortName: String,
    val parentCode: Int,
    val type: Short
)

/**
 * 地区代码实体(树)
 * */
data class DistrictCodeTree(
    val code: Int,
    val name: String,
    val fullName: String,
    val shortName: String,
    val parentCode: Int,
    val type: Short,
    val children: MutableList<DistrictCodeTree>
) {
    constructor(dc: DistrictCode) : this(
        dc.code,
        dc.name,
        dc.fullName,
        dc.shortName,
        dc.parentCode,
        dc.type,
        mutableListOf()
    )
}


/**
 * 地区代码对应的数据表结构
 * */
object DistrictCodes: BaseTable<DistrictCode>("district_code") {

    val code = int("code").primaryKey()
    val name = varchar("name")
    val fullName = varchar("full_name")
    val shortName = varchar("short_name")
    val parentCode = int("parent_code")
    val type = short("type")

    override fun doCreateEntity(row: QueryRowSet, withReferences: Boolean): DistrictCode {
        return DistrictCode(
            code = row[code]!!,
            name = row[name]!!,
            fullName = row[fullName]!!,
            shortName = row[shortName]!!,
            parentCode = row[parentCode] ?: -1,
            type = row[type]!!
        )
    }
}


/**
 * 枚举地区类型
 * */
enum class DistrictCodeType(val type: Short) {
    /**
     * 省级
     * */
    PROVINCIAL(1),

    /**
     * 市级
     * */
    MUNICIPAL(2),

    /**
     * 区级
     * */
    DISTRICT(3)
}
