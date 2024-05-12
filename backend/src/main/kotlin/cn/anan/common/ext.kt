package cn.anan.common


/**
 * 处理Api的参数，如果出现问题则会抛出 `ApiException(StatusCode.PARAMETER_ERROR)`
 * @throws ApiException 如果是 [NumberFormatException]、[NullPointerException] 则抛出
 * @throws Exception
 * */
inline fun <T, R> T.transformApiParam(block: T.() -> R): R {
    try {
        return block()
    } catch (e : Exception) {
        when (e) {
            is NumberFormatException, is NullPointerException  -> {
                throw ApiException(StatusCode.PARAMETER_ERROR)
            }
            else -> throw e
        }
    }
}