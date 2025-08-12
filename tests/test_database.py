"""
数据库测试文件 - 测试数据库连接和操作
"""

import sys
import os
import json
from datetime import datetime
import hashlib
import random

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main.database.database_manager import DatabaseManager, get_db_manager, save_hot_topic, save_collection_log
from config.database_config import DATABASE_CONFIG

def test_connection():
    """测试数据库连接"""
    print("=" * 50)
    print("测试数据库连接")
    print("=" * 50)
    
    # 创建数据库管理器实例
    db = DatabaseManager()
    
    # 测试连接
    connected = db.connect()
    print(f"数据库连接测试: {'✅ 成功' if connected else '❌ 失败'}")
    
    if connected:
        # 显示连接信息
        print(f"已连接到: {db.config['host']}:{db.config['port']}/{db.config['database']}")
        
        # 关闭连接
        db.disconnect()
        print("数据库连接已关闭")
    
    print("数据库连接测试完成\n")
    return connected

def test_platform_operations():
    """测试平台相关操作"""
    print("=" * 50)
    print("测试平台相关操作")
    print("=" * 50)
    
    # 获取数据库管理器
    db = get_db_manager()
    db.connect()
    
    # 测试获取所有平台
    platforms = db.get_all_platforms()
    print(f"获取所有平台: {'✅ 成功' if platforms is not None else '❌ 失败'}")
    print(f"平台数量: {len(platforms)}")
    
    if platforms:
        # 显示平台信息
        for platform in platforms[:3]:  # 只显示前3个
            print(f"- {platform['name']} ({platform['code']})")
        
        # 测试根据代码获取平台
        test_platform_code = platforms[0]['code']
        platform = db.get_platform_by_code(test_platform_code)
        print(f"根据代码获取平台 '{test_platform_code}': {'✅ 成功' if platform else '❌ 失败'}")
        
        # 测试获取启用的平台
        enabled_platforms = db.get_enabled_platforms()
        print(f"获取启用的平台: {'✅ 成功' if enabled_platforms is not None else '❌ 失败'}")
        print(f"启用的平台数量: {len(enabled_platforms)}")
    
    # 关闭连接
    db.disconnect()
    print("平台相关操作测试完成\n")

def test_hot_topic_operations():
    """测试热搜话题相关操作"""
    print("=" * 50)
    print("测试热搜话题相关操作")
    print("=" * 50)
    
    # 获取数据库管理器
    db = get_db_manager()
    db.connect()
    
    # 获取一个平台用于测试
    platforms = db.get_all_platforms()
    if not platforms:
        print("❌ 无法获取平台信息，跳过热搜话题测试")
        db.disconnect()
        return
    
    test_platform = platforms[0]
    
    # 创建测试话题数据
    test_title = f"测试话题 {datetime.now().strftime('%Y%m%d%H%M%S')}"
    test_hash = hashlib.md5(test_title.encode()).hexdigest()
    
    test_topic = {
        'platform_id': test_platform['id'],
        'title': test_title,
        'rank': random.randint(1, 50),
        'heat_value': random.randint(1000, 10000),
        'url': f"https://example.com/topic/{test_hash}",
        'hash_id': test_hash,
        'category': '测试',
        'tags': ['测试', '临时']
    }
    
    # 测试插入话题
    topic_id = db.insert_hot_topic(test_topic)
    print(f"插入热搜话题: {'✅ 成功' if topic_id > 0 else '❌ 失败'}")
    
    if topic_id > 0:
        print(f"插入的话题ID: {topic_id}")
        
        # 测试根据哈希获取话题
        topic = db.get_hot_topic_by_hash(test_hash)
        print(f"根据哈希获取话题: {'✅ 成功' if topic else '❌ 失败'}")
        
        if topic:
            print(f"话题标题: {topic['title']}")
            print(f"话题标签: {topic['tags']}")
            
            # 测试更新话题
            update_data = {
                'rank': random.randint(1, 50),
                'heat_value': random.randint(1000, 10000),
                'tags': ['测试', '临时', '已更新']
            }
            
            updated = db.update_hot_topic(topic_id, update_data)
            print(f"更新热搜话题: {'✅ 成功' if updated else '❌ 失败'}")
            
            # 验证更新
            if updated:
                updated_topic = db.get_hot_topic_by_hash(test_hash)
                print(f"更新后的标签: {updated_topic['tags']}")
        
        # 测试获取平台话题
        platform_topics = db.get_hot_topics_by_platform(test_platform['code'], 10)
        print(f"获取平台话题: {'✅ 成功' if platform_topics is not None else '❌ 失败'}")
        print(f"平台话题数量: {len(platform_topics)}")
        
        # 测试获取最近话题
        recent_topics = db.get_latest_hot_topics(24, 10)
        print(f"获取最近话题: {'✅ 成功' if recent_topics is not None else '❌ 失败'}")
        print(f"最近话题数量: {len(recent_topics)}")
        
        # 测试搜索话题
        search_keyword = "测试"
        search_results = db.search_hot_topics(search_keyword, 10)
        print(f"搜索话题 '{search_keyword}': {'✅ 成功' if search_results is not None else '❌ 失败'}")
        print(f"搜索结果数量: {len(search_results)}")
    
    # 关闭连接
    db.disconnect()
    print("热搜话题相关操作测试完成\n")

def test_collection_log_operations():
    """测试采集记录相关操作"""
    print("=" * 50)
    print("测试采集记录相关操作")
    print("=" * 50)
    
    # 获取数据库管理器
    db = get_db_manager()
    db.connect()
    
    # 获取一个平台用于测试
    platforms = db.get_all_platforms()
    if not platforms:
        print("❌ 无法获取平台信息，跳过采集记录测试")
        db.disconnect()
        return
    
    test_platform = platforms[0]
    
    # 创建测试采集记录
    now = datetime.now()
    test_log = {
        'platform_id': test_platform['id'],
        'status': 'success',
        'total_count': 50,
        'success_count': 45,
        'error_count': 2,
        'duplicate_count': 3,
        'error_message': None,
        'start_time': now,
        'end_time': now
    }
    
    # 测试插入采集记录
    log_id = db.insert_collection_log(test_log)
    print(f"插入采集记录: {'✅ 成功' if log_id > 0 else '❌ 失败'}")
    
    if log_id > 0:
        print(f"插入的记录ID: {log_id}")
        
        # 测试获取采集记录
        logs = db.get_collection_logs(test_platform['code'], 10)
        print(f"获取采集记录: {'✅ 成功' if logs is not None else '❌ 失败'}")
        print(f"采集记录数量: {len(logs)}")
        
        # 测试获取所有采集记录
        all_logs = db.get_collection_logs(limit=10)
        print(f"获取所有采集记录: {'✅ 成功' if all_logs is not None else '❌ 失败'}")
        print(f"所有采集记录数量: {len(all_logs)}")
    
    # 关闭连接
    db.disconnect()
    print("采集记录相关操作测试完成\n")

def test_statistics_operations():
    """测试统计相关操作"""
    print("=" * 50)
    print("测试统计相关操作")
    print("=" * 50)
    
    # 获取数据库管理器
    db = get_db_manager()
    db.connect()
    
    # 测试获取平台统计
    platform_stats = db.get_platform_statistics()
    print(f"获取平台统计: {'✅ 成功' if platform_stats is not None else '❌ 失败'}")
    if platform_stats:
        print(f"平台统计数量: {len(platform_stats)}")
    
    # 测试获取分类统计
    category_stats = db.get_category_statistics()
    print(f"获取分类统计: {'✅ 成功' if category_stats is not None else '❌ 失败'}")
    if category_stats:
        print(f"分类统计数量: {len(category_stats)}")
    
    # 测试获取标签统计
    tag_stats = db.get_tag_statistics()
    print(f"获取标签统计: {'✅ 成功' if tag_stats is not None else '❌ 失败'}")
    if tag_stats:
        print(f"标签统计数量: {len(tag_stats)}")
    
    # 测试获取采集统计
    collection_stats = db.get_collection_statistics(7)
    print(f"获取采集统计: {'✅ 成功' if collection_stats is not None else '❌ 失败'}")
    if collection_stats:
        print(f"总采集次数: {collection_stats['total_collections']}")
        print(f"成功率: {collection_stats['success_rate']:.2f}%")
    
    # 关闭连接
    db.disconnect()
    print("统计相关操作测试完成\n")

def test_helper_functions():
    """测试辅助函数"""
    print("=" * 50)
    print("测试辅助函数")
    print("=" * 50)
    
    # 获取数据库管理器
    db = get_db_manager()
    db.connect()
    
    # 获取一个平台用于测试
    platforms = db.get_all_platforms()
    if not platforms:
        print("❌ 无法获取平台信息，跳过辅助函数测试")
        db.disconnect()
        return
    
    test_platform = platforms[0]
    
    # 测试保存热搜话题
    test_title = f"辅助函数测试话题 {datetime.now().strftime('%Y%m%d%H%M%S')}"
    test_hash = hashlib.md5(test_title.encode()).hexdigest()
    
    test_topic = {
        'platform': test_platform['code'],
        'title': test_title,
        'rank': random.randint(1, 50),
        'heat_value': random.randint(1000, 10000),
        'url': f"https://example.com/topic/{test_hash}",
        'hash_id': test_hash,
        'category': '测试',
        'tags': ['辅助函数', '测试']
    }
    
    result = save_hot_topic(test_topic)
    print(f"保存热搜话题: {'✅ 成功' if result else '❌ 失败'}")
    
    # 测试保存采集记录
    now = datetime.now()
    stats = {
        'total_count': 30,
        'success_count': 28,
        'error_count': 1,
        'duplicate_count': 1
    }
    
    log_id = save_collection_log(
        platform=test_platform['code'],
        status='success',
        stats=stats,
        start_time=now,
        end_time=now,
        error_message=None
    )
    
    print(f"保存采集记录: {'✅ 成功' if log_id > 0 else '❌ 失败'}")
    
    # 关闭连接
    db.disconnect()
    print("辅助函数测试完成\n")

def main():
    """主测试函数"""
    print("热搜话题数据库 - 测试")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"数据库配置: {DATABASE_CONFIG['host']}:{DATABASE_CONFIG['port']}/{DATABASE_CONFIG['database']}")
    print()
    
    # 首先测试连接
    connected = test_connection()
    
    if connected:
        # 如果连接成功，运行其他测试
        test_platform_operations()
        test_hot_topic_operations()
        test_collection_log_operations()
        test_statistics_operations()
        test_helper_functions()
    else:
        print("❌ 数据库连接失败，跳过其他测试")
    
    print("=" * 50)
    print("所有数据库测试完成")
    print("=" * 50)

if __name__ == "__main__":
    main()