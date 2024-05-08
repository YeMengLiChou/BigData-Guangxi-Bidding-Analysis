package cn.anan.common

import com.google.protobuf.Api

/**
 * Api自定义结果类
 */
data class ApiResult<T> (
    val code: Int,
    val msg: String,
    val data: T?,
) {
    companion object {
        /**
         * 成功响应
         * */
        fun <T> success(data: T): ApiResult<T> {
            return ApiResult(StatusCode.SUCCESS.code, StatusCode.SUCCESS.msg, data)
        }
        /**
         * 成功响应但是数据为空
         * */
        fun empty(): ApiResult<Nothing> {
            return ApiResult(StatusCode.SUCCESS.code, StatusCode.SUCCESS.msg, null)
        }

        /**
         * 响应失败
         * */
        fun failure(code: Int, msg: String): ApiResult<Nothing> {
            return ApiResult(code, msg, null)
        }
        /**
         * 响应失败
         * */
        fun <T>failure(code: StatusCode): ApiResult<T> {
            return ApiResult(code.code, code.msg, null)
        }
    }
}