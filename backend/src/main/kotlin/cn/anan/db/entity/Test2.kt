package cn.anan.db.entity

import org.ktorm.entity.Entity

interface Test2: Entity<Test2> {
    companion object: Entity.Factory<Test2>()


}