package cn.anan.db.entity

import io.ktor.http.*

/**
 * 分页请求体(pageNo) 从1开始
 * */
data class PageRequest(
    val pageSize: Int,
    val pageNo: Int
) {

    companion object {
        fun createFromParameters(parameters: Parameters): PageRequest? {
            val pageSize: String = parameters["pageSize"] ?: return null
            val pageNo: String = parameters["pageNo"] ?: return null
            return PageRequest(
                pageSize = pageSize.toInt(),
                pageNo = pageNo.toInt()
            )
        }
    }

    fun getLimitOffset(): Pair<Int, Int> {
        return Pair((pageNo - 1) * pageSize, pageSize)
    }
}

