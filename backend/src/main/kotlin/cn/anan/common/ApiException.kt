package cn.anan.common

/**
 * Api自定义异常类
 * */
class ApiException(
    val code: Int,
    val msg: String
): RuntimeException(msg) {

    constructor(statusCode: StatusCode): this(statusCode.code, statusCode.msg)
}