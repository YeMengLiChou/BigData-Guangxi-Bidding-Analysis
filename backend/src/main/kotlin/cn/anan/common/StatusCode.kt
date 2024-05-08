package cn.anan.common

/***
 * 自定义状态码
 */
enum class StatusCode(val code: Int, val msg: String) {

    SUCCESS(200, "success"),

    PARAMETER_ERROR(1000, "参数异常"),

    REQUEST_BODY_ERROR(1001, "请求体错误"),

    NO_DATA(1002, "无此数据")
}