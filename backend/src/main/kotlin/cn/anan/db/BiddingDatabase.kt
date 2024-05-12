package cn.anan.db

import org.ktorm.database.Database
import java.sql.Connection
import java.sql.DriverManager
import kotlin.concurrent.thread


private val conn = DriverManager.getConnection(
    "jdbc:mysql://localhost:3306/bidding",
    "root",
    "suweikai"
)


/**
 * 数据库连接
 * */
val database = Database.connect {
    object : Connection by conn {
        override fun close() {
            // 重写该方法，保持数据库的连接，并不关闭
        }
    }
}

/**
 * 初始化数据库，将会在进程退出时释放资源
 * */
fun initDatabase() {
    // 在进程退出时关闭该 connection
    Runtime.getRuntime().addShutdownHook(
        thread(start = false) {
            conn.close()
        }
    )
}