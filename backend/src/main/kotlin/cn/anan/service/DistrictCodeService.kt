package cn.anan.service

import cn.anan.common.ApiException
import cn.anan.common.StatusCode
import cn.anan.common.Validations
import cn.anan.db.database
import cn.anan.db.table.DistrictCode
import cn.anan.db.table.DistrictCodeTree
import cn.anan.db.table.DistrictCodeType
import cn.anan.db.table.DistrictCodes
import org.ktorm.dsl.*
import org.ktorm.support.mysql.insertOrUpdate
import java.util.*

object DistrictCodeService {

    /**
     * 插入多条 DistrictCode 实体
     * @param data
     * @return 数据库中受影响的条数
     * */
    fun insertOrUpdates(data: List<DistrictCode>): Int {
        if (data.isEmpty()) {
            return 0
        }
        var effectedRowCount = 0
        database.useTransaction {
            for (item in data) {
                effectedRowCount += database.insertOrUpdate(DistrictCodes) {
                    set(it.code, item.code)
                    set(it.type, item.type)
                    set(it.parentCode, item.parentCode)
                    set(it.name, item.name)
                    set(it.shortName, item.shortName)
                    set(it.fullName, item.fullName)

                    onDuplicateKey {
                        set(it.type, item.type)
                        set(it.parentCode, item.parentCode)
                        set(it.name, item.name)
                        set(it.shortName, item.shortName)
                        set(it.fullName, item.fullName)
                    }
                }
            }
        }
        return effectedRowCount
    }

    /**
     * 根据所给 [type] 查找数据
     * @param type 类型，只能在枚举类 [DistrictCodeType] 的值
     * @see DistrictCodeType
     * @return 返回查找到的数据
     * */
    fun fetchByType(type: Short): List<DistrictCode> {
        if (!Validations.validateDistrictCodeType(type)) {
            throw ApiException(StatusCode.PARAMETER_ERROR)
        }
        return database.from(DistrictCodes).select().where {
            DistrictCodes.type eq type
        }.map {
            DistrictCodes.createEntity(it)
        }
    }

    /**
     * 获取所有数据
     * @return List<DistrictCode>
     * */
    fun fetchAll(): List<DistrictCode> {
        return database.from(DistrictCodes).select().orderBy(DistrictCodes.code.asc()).map {
            DistrictCodes.createEntity(it)
        }
    }

    /**
     * 根据 [code] 获取树形结构
     * @param code 地区代码
     * @return 如果 [code] 存在则返回以 [code] 为根节点的树状结构，否则返回 null
     * */
    fun fetchTreeByCode(code: Int): DistrictCodeTree? {
        val parentList = database.from(DistrictCodes).select().where {
            DistrictCodes.code eq code
        }.map {
            DistrictCodes.createEntity(it)
        }
        if (parentList.isEmpty()) {
            return null
        }
        val root = DistrictCodeTree(parentList[0])
        val q: Queue<DistrictCodeTree> = LinkedList()
        q.offer(root)
        while (!q.isEmpty()) {
            val currentNode = q.poll()
            // 读取当前孩子
            val children = database.from(DistrictCodes).select().where {
                DistrictCodes.parentCode eq currentNode.code
            }.map {
                DistrictCodeTree(DistrictCodes.createEntity(it))
            }
            children.forEach {
                currentNode.children.add(it)
                q.offer(it)
            }
        }
        return root
    }

    fun fetchCities(): List<DistrictCode> {
        return database
            .from(DistrictCodes)
            .select()
            .where {
                ((DistrictCodes.code rem 100) eq 0)
            }
            .map { DistrictCodes.createEntity(it) }
    }
}