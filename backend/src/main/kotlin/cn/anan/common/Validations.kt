package cn.anan.common

import cn.anan.db.table.DistrictCodeType
import cn.anan.db.entity.PageRequest

/**
 * 验证参数是否符合
 * */
class Validations {

    companion object {

        /**
         * 验证分页请求是否符合要求
         * */
        fun validatePage(pageSize: Int, pageNo: Int): Boolean {
            return !(pageNo < PAGE_MIN_NO || pageNo > PAGE_MAX_NO || pageSize < PAGE_MIN_SIZE || pageSize > PAGE_MAX_SIZE)
        }

        /**
         * 验证分页请求是否符合要求
         * */
        fun validatePage(page: PageRequest): Boolean {
            return validatePage(page.pageSize, page.pageNo)
        }

        /**
         * 检验地区代码是否符合
         * */
        fun validateDistrictCodeType(type: Short): Boolean {
            val types: List<Short> = listOf(
                DistrictCodeType.PROVINCIAL.type,
                DistrictCodeType.MUNICIPAL.type,
                DistrictCodeType.DISTRICT.type
            )
            return type in types
        }


    }

}
