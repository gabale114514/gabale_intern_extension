"""
工具接口测试文件 - 扩展版
"""

import json
import sys
import os
import re
import hashlib
from datetime import datetime
from typing import List, Dict, Any, Optional

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 假设导入的模块及函数存在
from logs.hot_topic_tool import process_hot_topic, process_hot_topics_batch, get_tool_info
from main.scraper.utils import (
    clean_text, extract_tags, generate_hash, categorize_topic,
    calculate_similarity, is_duplicate_topic, validate_platform,
    validate_rank, validate_heat_value, format_datetime, safe_json_loads,
    get_platform_icon, get_platform_name, safe_parse_datetime, process_tags
)

def test_text_processing_utils():
    """测试文本处理相关工具函数"""
    print("=" * 50)
    print("测试文本处理工具函数")
    print("=" * 50)
    
    # 测试clean_text函数
    test_texts = [
        "  这是一个测试文本  \n\n  包含多余的空格和换行  ",
        None,
        12345,
        "这是一个超长文本，" * 20,  # 测试长度限制
        "文本中包含特殊字符：!@#$%^&*()_+{}[]|\\:;\"'<>,.?/"
    ]
    for idx, text in enumerate(test_texts):
        cleaned = clean_text(text)
        print(f"clean_text测试 {idx+1}: '{text}' -> '{cleaned}' (长度: {len(cleaned)})")
    
    # 测试calculate_similarity函数
    text_pairs = [
        ("这是一个测试文本", "这是一个测试文本"),
        ("这是一个测试文本", "这是另一个不同的文本"),
        ("微博热搜", "微博热搜榜"),
        ("", "测试文本")
    ]
    for idx, (text1, text2) in enumerate(text_pairs):
        similarity = calculate_similarity(text1, text2)
        print(f"文本相似度测试 {idx+1}: '{text1}' 与 '{text2}' -> {similarity:.2f}")
    
    print("文本处理工具函数测试完成\n")

def test_tag_and_category_utils():
    """测试标签和分类相关工具函数"""
    print("=" * 50)
    print("测试标签和分类工具函数")
    print("=" * 50)
    
    # 测试extract_tags函数
    test_titles = [
        "这是一个热门话题🔥 新消息",
        "科技新闻：AI技术取得重大突破",
        "体育赛事：足球比赛结果公布",
        "娱乐八卦：明星结婚喜讯"
    ]
    for idx, title in enumerate(test_titles):
        tags = extract_tags(title)
        print(f"标签提取测试 {idx+1}: '{title}' -> {tags}")
    
    # 测试process_tags函数
    test_tag_lists = [
        ["超长标签" * 20, "正常标签", ""],  # 包含超长标签和空标签
        "单个标签字符串",  # 非列表输入
        None,  # 空值
        ["标签1", "标签2", "标签3", "标签4", "标签5", "标签6"]  # 测试数量限制
    ]
    for idx, tags in enumerate(test_tag_lists):
        processed = process_tags(tags, max_length=10)
        print(f"标签处理测试 {idx+1}: {tags} -> {processed}")
    
    # 测试categorize_topic函数
    test_titles = [
        "明星演唱会门票售罄",
        "AI技术最新突破",
        "股市大涨",
        "足球比赛结果",
        "未知分类测试"
    ]
    for idx, title in enumerate(test_titles):
        category = categorize_topic(title)
        print(f"话题分类测试 {idx+1}: '{title}' -> {category}")
    
    print("标签和分类工具函数测试完成\n")

def test_validation_utils():
    """测试数据验证相关工具函数"""
    print("=" * 50)
    print("测试数据验证工具函数")
    print("=" * 50)
    
    # 测试validate_platform函数
    test_platforms = ['weibo', 'zhihu', 'douyin', 'invalid_platform', '']
    for idx, platform in enumerate(test_platforms):
        is_valid = validate_platform(platform)
        print(f"平台验证测试 {idx+1}: '{platform}' -> {is_valid}")
    
    # 测试validate_rank函数
    test_ranks = [1, 50, 1000, 0, 1001, "10", None]
    for idx, rank in enumerate(test_ranks):
        is_valid = validate_rank(rank)
        print(f"排名验证测试 {idx+1}: {rank} -> {is_valid}")
    
    # 测试validate_heat_value函数
    test_heat_values = [1000, 0, None, -100, "1000", 123.45]
    for idx, heat in enumerate(test_heat_values):
        is_valid = validate_heat_value(heat)
        print(f"热度值验证测试 {idx+1}: {heat} -> {is_valid}")
    
    print("数据验证工具函数测试完成\n")

def test_datetime_utils():
    """测试日期时间相关工具函数"""
    print("=" * 50)
    print("测试日期时间工具函数")
    print("=" * 50)
    
    # 测试format_datetime函数
    test_dates = [
        datetime(2023, 1, 1, 12, 0, 0),
        datetime(2023, 12, 31, 23, 59, 59)
    ]
    for idx, dt in enumerate(test_dates):
        formatted = format_datetime(dt)
        print(f"日期格式化测试 {idx+1}: {dt} -> {formatted}")
    
    # 测试safe_parse_datetime函数
    test_date_strings = [
        "2023-01-01T12:00:00",
        "2023-01-01 12:00:00",
        "2023-01-01",
        "invalid_date",
        datetime(2023, 1, 1),  # 已为datetime对象
        123456789,  # 无效类型
        None
    ]
    for idx, date_val in enumerate(test_date_strings):
        parsed = safe_parse_datetime(date_val)
        print(f"日期解析测试 {idx+1}: {date_val} -> {parsed} (类型: {type(parsed)})")
    
    print("日期时间工具函数测试完成\n")

def test_other_utils():
    """测试其他工具函数"""
    print("=" * 50)
    print("测试其他工具函数")
    print("=" * 50)
    
    # 测试generate_hash函数
    test_contents = [
        "测试哈希生成",
        "测试哈希生成",  # 相同内容
        "不同的测试内容"
    ]
    for idx, content in enumerate(test_contents):
        hash_val = generate_hash(content)
        print(f"哈希生成测试 {idx+1}: '{content}' -> {hash_val}")
    
    # 测试safe_json_loads函数
    test_json_strings = [
        '{"name": "测试", "value": 123}',
        'invalid_json',
        None,
        12345
    ]
    for idx, json_str in enumerate(test_json_strings):
        result = safe_json_loads(json_str, default={})
        print(f"JSON解析测试 {idx+1}: {json_str} -> {result} (类型: {type(result)})")
    
    # 测试get_platform_icon和get_platform_name函数
    test_platforms = ['weibo', 'zhihu', 'invalid_platform']
    for idx, platform in enumerate(test_platforms):
        icon = get_platform_icon(platform)
        name = get_platform_name(platform)
        print(f"平台信息测试 {idx+1}: '{platform}' -> 名称: {name}, 图标: {icon}")
    
    # 测试is_duplicate_topic函数
    test_topic_pairs = [
        (
            {'title': '这是一个热门话题'},
            {'title': '这是一个热门话题'}
        ),
        (
            {'title': '这是一个热门话题'},
            {'title': '这是另一个话题'}
        ),
        (
            {'title': 'AI技术突破'},
            {'title': 'AI技术最新突破'}
        )
    ]
    for idx, (topic1, topic2) in enumerate(test_topic_pairs):
        is_duplicate = is_duplicate_topic(topic1, topic2)
        print(f"话题重复检测测试 {idx+1}: '{topic1['title']}' 与 '{topic2['title']}' -> {is_duplicate}")
    
    print("其他工具函数测试完成\n")

def test_single_topic():
    """测试单个话题处理"""
    print("=" * 50)
    print("测试单个话题处理")
    print("=" * 50)
    
    # 测试数据
    test_data = {
        'platform': 'weibo',
        'title': '这是一个热门话题🔥 新消息',
        'rank': 1,
        'heat_value': 10000,
        'url': 'https://example.com'
    }
    
    # 执行单个话题处理函数
    result = process_hot_topic(test_data)
    if result:
        print("✅ 单个话题处理成功:")
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("❌ 单个话题处理失败")
    
    print("单个话题处理测试完成\n")

def test_batch_topics():
    """测试批量话题处理"""
    print("=" * 50)
    print("测试批量话题处理")
    print("=" * 50)
    
    # 测试数据
    test_data_list = [
        {
            'platform': 'weibo',
            'title': '这是一个热门话题🔥 新消息',
            'rank': 1,
            'heat_value': 10000,
            'url': 'https://example.com'
        },
        {
            'platform': 'zhihu',
            'title': 'AI技术最新突破',
            'rank': 2,
            'heat_value': 8000
        },
        {
            'platform': 'toutiao',
            'title': '股市大涨，投资者信心增强',
            'rank': 3,
            'heat_value': 6000
        },
        {
            'platform': 'weibo',
            'title': '这是一个热门话题🔥 新消息',  # 重复数据
            'rank': 4,
            'heat_value': 5000
        },
        {
            'platform': 'invalid_platform',  # 无效平台
            'title': '无效平台测试',
            'rank': 5
        }
    ]
    
    # 执行批量话题处理函数
    result = process_hot_topics_batch(test_data_list)
    print("✅ 批量话题处理结果:")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    print("批量话题处理测试完成\n")

def test_tool_info():
    """测试工具信息获取"""
    print("=" * 50)
    print("测试工具信息获取")
    print("=" * 50)
    
    # 执行工具信息获取函数
    info = get_tool_info()
    print("✅ 工具信息:")
    print(json.dumps(info, ensure_ascii=False, indent=2))
    
    print("工具信息测试完成\n")

def test_error_handling():
    """测试错误处理"""
    print("=" * 50)
    print("测试错误处理")
    print("=" * 50)
    
    # 测试缺少必需字段
    invalid_data = {
        'platform': 'weibo',
        'title': '',  # 空标题
        'rank': 1
    }
    
    # 执行单个话题处理函数（空标题测试）
    result = process_hot_topic(invalid_data)
    print(f"空标题测试: {result is None}")
    
    # 测试无效排名
    invalid_rank_data = {
        'platform': 'weibo',
        'title': '测试标题',
        'rank': 0  # 无效排名
    }
    
    # 执行单个话题处理函数（无效排名测试）
    result = process_hot_topic(invalid_rank_data)
    print(f"无效排名测试: {result is None}")
    
    # 测试无效热度值
    invalid_heat_data = {
        'platform': 'weibo',
        'title': '测试标题',
        'rank': 1,
        'heat_value': -100  # 负数热度值
    }
    
    # 执行单个话题处理函数（无效热度值测试）
    result = process_hot_topic(invalid_heat_data)
    print(f"无效热度值测试: {result is None}")
    
    print("错误处理测试完成\n")

def main():
    """主测试函数 - 执行所有测试"""
    print("热搜话题处理工具 - 全面测试")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 运行各项测试
    test_text_processing_utils()      # 测试文本处理相关函数
    test_tag_and_category_utils()     # 测试标签和分类相关函数
    test_validation_utils()           # 测试数据验证相关函数
    test_datetime_utils()             # 测试日期时间相关函数
    test_other_utils()                # 测试其他工具函数
    test_single_topic()               # 测试单个话题处理
    test_batch_topics()               # 测试批量话题处理
    test_tool_info()                  # 测试工具信息获取
    test_error_handling()             # 测试错误处理
    
    print("=" * 50)
    print("所有测试完成")
    print("=" * 50)

if __name__ == "__main__":
    main()