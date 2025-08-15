import mysql.connector
from config.database_config import DATABASE_CONFIG
from mysql.connector import Error
def enable_all_platforms(db_path, enable):
    """
    启用全部平台
    """
    try:
        # 连接MySQL数据库
        connection = mysql.connector.connect(**DATABASE_CONFIG)
        if connection.is_connected():
            cursor = connection.cursor()
            
            # 执行更新，启用所有平台
            cursor.execute(f"UPDATE platforms SET enabled = {enable} ")
            connection.commit()  # 提交事务
            print(f"成功启用所有平台，影响行数: {cursor.rowcount}")
            
    except Error as e:
        print(f"操作失败: {e}")
    finally:
        # 关闭连接
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()
            print("数据库连接已关闭")

if __name__ == "__main__":
    enable_all_platforms('gabale.db',0)