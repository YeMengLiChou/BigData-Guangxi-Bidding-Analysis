package cn.anan.common

data class Page<T>(
    val total: Int,
    val data: List<T>,
    val size: Int,
) {
    companion object {
        fun <T> success(total: Int, data: List<T>): Page<T> {
            return Page(total, data, data.size)
        }
        fun <T> failure(): Page<T> {
            return Page(total = 0, data = emptyList(), 0)
        }
    }
}