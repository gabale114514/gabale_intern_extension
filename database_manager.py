"""
数据库管理模块 - 处理数据库连接和操作
"""

import logging
import mysql.connector
from mysql.connector import Error
from typing import List, Dict, Any, Optional, Tuple, Union
from datetime import datetime
import json

from database_config import DATABASE_CONFIG

# 配置日志
logger = logging.getLogger(__name__)

class DatabaseManager:
    """数据库管理类，处理与MySQL数据库的交互"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化数据库管理器
        
        Args:
            config: 数据库配置，如果为None则使用默认配置
        """
        self.config = config or DATABASE_CONFIG
        self.connection = None
        self.cursor = None
    
    def connect(self) -> bool:
        """
        连接到数据库
        
        Returns:
            连接是否成功
        """
        try:
            self.connection = mysql.connector.connect(
                host=self.config['host'],
                port=self.config['port'],
                user=self.config['user'],
                password=self.config['password'],
                database=self.config['database'],
                charset=self.config['charset']
            )
            
            if self.connection.is_connected():
                self.cursor = self.connection.cursor(dictionary=True)
                logger.info(f"已连接到MySQL数据库: {self.config['host']}:{self.config['port']}/{self.config['database']}")
                return True
            
        except Error as e:
            logger.error(f"连接数据库时发生错误: {e}")
        
        return False
    
    def disconnect(self) -> None:
        """关闭数据库连接"""
        if self.connection and self.connection.is_connected():
            if self.cursor:
                self.cursor.close()
            self.connection.close()
            logger.info("数据库连接已关闭")
    
    def execute_query(self, query: str, params: Tuple = None) -> List[Dict[str, Any]]:
        """
        执行查询语句
        
        Args:
            query: SQL查询语句
            params: 查询参数
            
        Returns:
            查询结果列表
        """
        result = []
        
        try:
            if not self.connection or not self.connection.is_connected():
                self.connect()
            
            self.cursor.execute(query, params or ())
            result = self.cursor.fetchall()
            
        except Error as e:
            logger.error(f"执行查询时发生错误: {e}")
            logger.error(f"查询: {query}")
            logger.error(f"参数: {params}")
        
        return result
    
    def execute_update(self, query: str, params: Tuple = None) -> int:
        """
        执行更新语句
        
        Args:
            query: SQL更新语句
            params: 更新参数
            
        Returns:
            受影响的行数
        """
        affected_rows = 0
        
        try:
            if not self.connection or not self.connection.is_connected():
                self.connect()
            
            self.cursor.execute(query, params or ())
            self.connection.commit()
            affected_rows = self.cursor.rowcount
            
        except Error as e:
            logger.error(f"执行更新时发生错误: {e}")
            logger.error(f"查询: {query}")
            logger.error(f"参数: {params}")
            if self.connection:
                self.connection.rollback()
        
        return affected_rows
    
    def execute_many(self, query: str, params_list: List[Tuple]) -> int:
        """
        批量执行SQL语句
        
        Args:
            query: SQL语句
            params_list: 参数列表
            
        Returns:
            受影响的行数
        """
        affected_rows = 0
        
        try:
            if not self.connection or not self.connection.is_connected():
                self.connect()
            
            self.cursor.executemany(query, params_list)
            self.connection.commit()
            affected_rows = self.cursor.rowcount
            
        except Error as e:
            logger.error(f"批量执行SQL时发生错误: {e}")
            logger.error(f"查询: {query}")
            logger.error(f"参数数量: {len(params_list)}")
            if self.connection:
                self.connection.rollback()
        
        return affected_rows
    
    def get_last_insert_id(self) -> int:
        """
        获取最后插入的ID
        
        Returns:
            最后插入的ID
        """
        return self.cursor.lastrowid if self.cursor else 0

    # 平台相关方法
    
    def get_all_platforms(self) -> List[Dict[str, Any]]:
        """
        获取所有平台
        
        Returns:
            平台列表
        """
        query = "SELECT * FROM platforms ORDER BY id"
        return self.execute_query(query)
    
    def get_platform_by_code(self, code: str) -> Optional[Dict[str, Any]]:
        """
        根据代码获取平台
        
        Args:
            code: 平台代码
            
        Returns:
            平台信息，如果不存在则返回None
        """
        query = "SELECT * FROM platforms WHERE code = %s"
        result = self.execute_query(query, (code,))
        return result[0] if result else None
    
    def get_enabled_platforms(self) -> List[Dict[str, Any]]:
        """
        获取所有启用的平台
        
        Returns:
            启用的平台列表
        """
        query = "SELECT * FROM platforms WHERE enabled = TRUE ORDER BY id"
        return self.execute_query(query)
    
    # 热搜话题相关方法
    
    def insert_hot_topic(self, topic_data: Dict[str, Any]) -> int:
        """
        插入热搜话题
        
        Args:
            topic_data: 话题数据
            
        Returns:
            插入的话题ID，如果失败则返回0
        """
        # 检查平台ID
        platform_id = topic_data.get('platform_id')
        if not platform_id and 'platform' in topic_data:
            platform = self.get_platform_by_code(topic_data['platform'])
            if platform:
                platform_id = platform['id']
        
        if not platform_id:
            logger.error(f"插入话题失败: 无效的平台ID或代码 - {topic_data}")
            return 0
        
        # 准备数据
        query = """
        INSERT INTO hot_topics 
        (platform_id, title, `rank`, heat_value, url, hash_id, category, first_seen_at, last_seen_at) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        params = (
            platform_id,
            topic_data['title'],
            topic_data['rank'],
            topic_data.get('heat_value'),
            topic_data.get('url'),
            topic_data['hash_id'],
            topic_data.get('category'),
            topic_data.get('first_seen_at', datetime.now()),
            topic_data.get('last_seen_at', datetime.now())
        )
        
        # 执行插入
        affected_rows = self.execute_update(query, params)
        if affected_rows > 0:
            topic_id = self.get_last_insert_id()
            
            # 插入标签
            if 'tags' in topic_data and topic_data['tags']:
                self.insert_topic_tags(topic_id, topic_data['tags'])
            
            return topic_id
        
        return 0
    
    def update_hot_topic(self, topic_id: int, topic_data: Dict[str, Any]) -> bool:
        """
        更新热搜话题
        
        Args:
            topic_id: 话题ID
            topic_data: 话题数据
            
        Returns:
            更新是否成功
        """
        # 准备更新字段
        update_fields = []
        params = []
        
        if '`rank`' in topic_data:
            update_fields.append("`rank` = %s")
            params.append(topic_data['`rank`'])
        
        if 'heat_value' in topic_data:
            update_fields.append("heat_value = %s")
            params.append(topic_data['heat_value'])
        
        if 'url' in topic_data:
            update_fields.append("url = %s")
            params.append(topic_data['url'])
        
        if 'category' in topic_data:
            update_fields.append("category = %s")
            params.append(topic_data['category'])
        
        if not update_fields:
            logger.warning(f"更新话题失败: 没有提供更新字段 - {topic_data}")
            return False
        
        # 构建查询
        query = f"UPDATE hot_topics SET {', '.join(update_fields)} WHERE id = %s"
        params.append(topic_id)
        
        # 执行更新
        affected_rows = self.execute_update(query, tuple(params))
        
        # 更新标签
        if 'tags' in topic_data and topic_data['tags']:
            # 删除旧标签
            self.delete_topic_tags(topic_id)
            # 插入新标签
            self.insert_topic_tags(topic_id, topic_data['tags'])
        
        return affected_rows > 0
    
    def get_hot_topic_by_hash(self, hash_id: str) -> Optional[Dict[str, Any]]:
        """
        根据哈希ID获取热搜话题
        
        Args:
            hash_id: 哈希ID
            
        Returns:
            话题信息，如果不存在则返回None
        """
        query = """
        SELECT t.*, p.code as platform_code, p.name as platform_name 
        FROM hot_topics t
        JOIN platforms p ON t.platform_id = p.id
        WHERE t.hash_id = %s
        """
        result = self.execute_query(query, (hash_id,))
        
        if result:
            topic = result[0]
            # 获取标签
            topic['tags'] = self.get_topic_tags(topic['id'])
            return topic
        
        return None
    
    def get_hot_topics_by_platform(self, platform_code: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        获取指定平台的热搜话题
        
        Args:
            platform_code: 平台代码
            limit: 返回数量限制
            
        Returns:
            话题列表
        """
        query = """
        SELECT t.*, p.code as platform_code, p.name as platform_name 
        FROM hot_topics t
        JOIN platforms p ON t.platform_id = p.id
        WHERE p.code = %s
        ORDER BY t.`rank`
        LIMIT %s
        """
        topics = self.execute_query(query, (platform_code, limit))
        
        # 获取每个话题的标签
        for topic in topics:
            topic['tags'] = self.get_topic_tags(topic['id'])
        
        return topics
    
    def get_latest_hot_topics(self, hours: int = 24, limit: int = 100) -> List[Dict[str, Any]]:
        """
        获取最近的热搜话题
        
        Args:
            hours: 最近小时数
            limit: 返回数量限制
            
        Returns:
            话题列表
        """
        query = """
        SELECT t.*, p.code as platform_code, p.name as platform_name 
        FROM hot_topics t
        JOIN platforms p ON t.platform_id = p.id
        WHERE t.last_seen_at >= DATE_SUB(NOW(), INTERVAL %s HOUR)
        ORDER BY t.last_seen_at DESC, t.`rank`
        LIMIT %s
        """
        topics = self.execute_query(query, (hours, limit))
        
        # 获取每个话题的标签
        for topic in topics:
            topic['tags'] = self.get_topic_tags(topic['id'])
        
        return topics
    
    def search_hot_topics(self, keyword: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        搜索热搜话题
        
        Args:
            keyword: 关键词
            limit: 返回数量限制
            
        Returns:
            话题列表
        """
        query = """
        SELECT t.*, p.code as platform_code, p.name as platform_name 
        FROM hot_topics t
        JOIN platforms p ON t.platform_id = p.id
        WHERE t.title LIKE %s
        ORDER BY t.last_seen_at DESC
        LIMIT %s
        """
        topics = self.execute_query(query, (f"%{keyword}%", limit))
        
        # 获取每个话题的标签
        for topic in topics:
            topic['tags'] = self.get_topic_tags(topic['id'])
        
        return topics
    
    # 话题标签相关方法
    
    def insert_topic_tags(self, topic_id: int, tags: List[str]) -> int:
        """
        插入话题标签
        
        Args:
            topic_id: 话题ID
            tags: 标签列表
            
        Returns:
            插入的标签数量
        """
        if not tags:
            return 0
        
        query = "INSERT INTO topic_tags (topic_id, tag_name) VALUES (%s, %s)"
        params_list = [(topic_id, tag) for tag in tags]
        
        return self.execute_many(query, params_list)
    
    def delete_topic_tags(self, topic_id: int) -> int:
        """
        删除话题标签
        
        Args:
            topic_id: 话题ID
            
        Returns:
            删除的标签数量
        """
        query = "DELETE FROM topic_tags WHERE topic_id = %s"
        return self.execute_update(query, (topic_id,))
    
    def get_topic_tags(self, topic_id: int) -> List[str]:
        """
        获取话题标签
        
        Args:
            topic_id: 话题ID
            
        Returns:
            标签列表
        """
        query = "SELECT tag_name FROM topic_tags WHERE topic_id = %s"
        result = self.execute_query(query, (topic_id,))
        return [row['tag_name'] for row in result]
    
    # 采集记录相关方法
    
    def insert_collection_log(self, log_data: Dict[str, Any]) -> int:
        """
        插入采集记录
        
        Args:
            log_data: 记录数据
            
        Returns:
            插入的记录ID，如果失败则返回0
        """
        # 检查平台ID
        platform_id = log_data.get('platform_id')
        if not platform_id and 'platform' in log_data:
            platform = self.get_platform_by_code(log_data['platform'])
            if platform:
                platform_id = platform['id']
        
        if not platform_id:
            logger.error(f"插入采集记录失败: 无效的平台ID或代码 - {log_data}")
            return 0
        
        # 准备数据
        query = """
        INSERT INTO collection_logs 
        (platform_id, status, total_count, success_count, error_count, duplicate_count, error_message, start_time, end_time) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        params = (
            platform_id,
            log_data['status'],
            log_data.get('total_count', 0),
            log_data.get('success_count', 0),
            log_data.get('error_count', 0),
            log_data.get('duplicate_count', 0),
            log_data.get('error_message'),
            log_data['start_time'],
            log_data['end_time']
        )
        
        # 执行插入
        affected_rows = self.execute_update(query, params)
        if affected_rows > 0:
            return self.get_last_insert_id()
        
        return 0
    
    def get_collection_logs(self, platform_code: str = None, limit: int = 20) -> List[Dict[str, Any]]:
        """
        获取采集记录
        
        Args:
            platform_code: 平台代码，如果为None则获取所有平台
            limit: 返回数量限制
            
        Returns:
            记录列表
        """
        if platform_code:
            query = """
            SELECT l.*, p.code as platform_code, p.name as platform_name 
            FROM collection_logs l
            JOIN platforms p ON l.platform_id = p.id
            WHERE p.code = %s
            ORDER BY l.created_at DESC
            LIMIT %s
            """
            return self.execute_query(query, (platform_code, limit))
        else:
            query = """
            SELECT l.*, p.code as platform_code, p.name as platform_name 
            FROM collection_logs l
            JOIN platforms p ON l.platform_id = p.id
            ORDER BY l.created_at DESC
            LIMIT %s
            """
            return self.execute_query(query, (limit,))
    
    # 统计相关方法
    
    def get_platform_statistics(self) -> List[Dict[str, Any]]:
        """
        获取各平台统计信息
        
        Returns:
            平台统计信息列表
        """
        query = """
        SELECT 
            p.id, p.code, p.name, p.icon,
            COUNT(t.id) as topic_count,
            MAX(t.last_seen_at) as last_update
        FROM platforms p
        LEFT JOIN hot_topics t ON p.id = t.platform_id
        GROUP BY p.id, p.code, p.name, p.icon
        ORDER BY p.id
        """
        return self.execute_query(query)
    
    def get_category_statistics(self) -> List[Dict[str, Any]]:
        """
        获取各分类统计信息
        
        Returns:
            分类统计信息列表
        """
        query = """
        SELECT 
            category,
            COUNT(*) as topic_count
        FROM hot_topics
        WHERE category IS NOT NULL
        GROUP BY category
        ORDER BY topic_count DESC
        """
        return self.execute_query(query)
    
    def get_tag_statistics(self) -> List[Dict[str, Any]]:
        """
        获取各标签统计信息
        
        Returns:
            标签统计信息列表
        """
        query = """
        SELECT 
            tag_name,
            COUNT(*) as topic_count
        FROM topic_tags
        GROUP BY tag_name
        ORDER BY topic_count DESC
        """
        return self.execute_query(query)
    
    def get_collection_statistics(self, days: int = 7) -> Dict[str, Any]:
        """
        获取采集统计信息
        
        Args:
            days: 统计天数
            
        Returns:
            采集统计信息
        """
        # 总采集次数
        query_total = """
        SELECT COUNT(*) as total_collections
        FROM collection_logs
        WHERE created_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
        """
        total_result = self.execute_query(query_total, (days,))
        total_collections = total_result[0]['total_collections'] if total_result else 0
        
        # 成功率
        query_success = """
        SELECT 
            COUNT(CASE WHEN status = 'success' THEN 1 END) as success_count,
            COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_count,
            COUNT(CASE WHEN status = 'partial' THEN 1 END) as partial_count
        FROM collection_logs
        WHERE created_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
        """
        success_result = self.execute_query(query_success, (days,))
        
        # 各平台采集次数
        query_platform = """
        SELECT 
            p.code, p.name,
            COUNT(l.id) as collection_count
        FROM collection_logs l
        JOIN platforms p ON l.platform_id = p.id
        WHERE l.created_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
        GROUP BY p.code, p.name
        ORDER BY collection_count DESC
        """
        platform_result = self.execute_query(query_platform, (days,))
        
        # 汇总统计
        return {
            'total_collections': total_collections,
            'success_count': success_result[0]['success_count'] if success_result else 0,
            'failed_count': success_result[0]['failed_count'] if success_result else 0,
            'partial_count': success_result[0]['partial_count'] if success_result else 0,
            'success_rate': (success_result[0]['success_count'] / total_collections * 100) if total_collections > 0 and success_result else 0,
            'platform_stats': platform_result
        }

# 单例模式
_db_instance = None

def get_db_manager() -> DatabaseManager:
    """
    获取数据库管理器实例（单例模式）
    
    Returns:
        数据库管理器实例
    """
    global _db_instance
    if _db_instance is None:
        _db_instance = DatabaseManager()
    return _db_instance

# 辅助函数

def save_hot_topic(topic_data: Dict[str, Any]) -> Union[int, bool]:
    """
    保存热搜话题（新增或更新）
    
    Args:
        topic_data: 话题数据
        
    Returns:
        如果是新增，返回话题ID；如果是更新，返回是否成功；如果失败，返回0或False
    """
    db = get_db_manager()
    
    # 检查是否存在
    existing_topic = None
    if 'hash_id' in topic_data:
        existing_topic = db.get_hot_topic_by_hash(topic_data['hash_id'])
    
    if existing_topic:
        # 更新现有话题
        return db.update_hot_topic(existing_topic['id'], topic_data)
    else:
        # 插入新话题
        return db.insert_hot_topic(topic_data)

def save_collection_log(platform: str, status: str, stats: Dict[str, int], 
                       start_time: datetime, end_time: datetime, 
                       error_message: str = None) -> int:
    """
    保存采集记录
    
    Args:
        platform: 平台代码
        status: 状态（'success', 'failed', 'partial'）
        stats: 统计信息（包含total_count, success_count, error_count, duplicate_count）
        start_time: 开始时间
        end_time: 结束时间
        error_message: 错误信息
        
    Returns:
        记录ID，如果失败则返回0
    """
    db = get_db_manager()
    
    log_data = {
        'platform': platform,
        'status': status,
        'total_count': stats.get('total_count', 0),
        'success_count': stats.get('success_count', 0),
        'error_count': stats.get('error_count', 0),
        'duplicate_count': stats.get('duplicate_count', 0),
        'error_message': error_message,
        'start_time': start_time,
        'end_time': end_time
    }
    
    return db.insert_collection_log(log_data)

def get_platform_hot_topics(platform_code: str, limit: int = 50) -> List[Dict[str, Any]]:
    """
    获取指定平台的热搜话题
    
    Args:
        platform_code: 平台代码
        limit: 返回数量限制
        
    Returns:
        话题列表
    """
    db = get_db_manager()
    return db.get_hot_topics_by_platform(platform_code, limit)

def get_all_platform_hot_topics(limit_per_platform: int = 20) -> Dict[str, List[Dict[str, Any]]]:
    """
    获取所有平台的热搜话题
    
    Args:
        limit_per_platform: 每个平台返回的话题数量限制
        
    Returns:
        按平台分组的话题字典
    """
    db = get_db_manager()
    platforms = db.get_enabled_platforms()
    
    result = {}
    for platform in platforms:
        topics = db.get_hot_topics_by_platform(platform['code'], limit_per_platform)
        result[platform['code']] = topics
    
    return result

def search_topics(keyword: str, limit: int = 50) -> List[Dict[str, Any]]:
    """
    搜索热搜话题
    
    Args:
        keyword: 关键词
        limit: 返回数量限制
        
    Returns:
        话题列表
    """
    db = get_db_manager()
    return db.search_hot_topics(keyword, limit)

def get_statistics() -> Dict[str, Any]:
    """
    获取统计信息
    
    Returns:
        统计信息字典
    """
    db = get_db_manager()
    
    return {
        'platforms': db.get_platform_statistics(),
        'categories': db.get_category_statistics(),
        'tags': db.get_tag_statistics(),
        'collections': db.get_collection_statistics(7)
    }

# 测试连接
if __name__ == "__main__":
    db = get_db_manager()
    if db.connect():
        print("数据库连接成功！")
        platforms = db.get_all_platforms()
        print(f"平台数量: {len(platforms)}")
        for platform in platforms:
            print(f"- {platform['name']} ({platform['code']})")
        db.disconnect()
    else:
        print("数据库连接失败！")