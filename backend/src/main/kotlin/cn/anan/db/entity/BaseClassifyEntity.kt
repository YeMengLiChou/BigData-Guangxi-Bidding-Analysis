package cn.anan.db.entity

import org.ktorm.dsl.QueryRowSet

open class BaseClassifyEntity(
    val year: Int,
    val month: Int,
    val day: Int,
    val quarter: Int,
    val districtCode: Int
)
