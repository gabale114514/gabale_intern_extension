"""
工具接口测试文件
"""

import json
import sys
import os
from datetime import datetime

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from hot_topic_tool import process_hot_topic, process_hot_topics_batch, get_tool_info
from utils import clean_text, extract_tags, categorize_topic, validate_platform

def test_utils():
    """测试工具函数"""
    print("=" * 50)
    print("测试工具函数")
    print("=" * 50)
    
    # 测试文本清理
    test_text = "  这是一个测试文本  \n\n  包含多余的空格和换行  "
    cleaned = clean_text(test_text)
    print(f"文本清理测试: '{test_text}' -> '{cleaned}'")
    
    # 测试标签提取
    test_title = "这是一个热门话题🔥 新消息"
    tags = extract_tags(test_title)
    print(f"标签提取测试: '{test_title}' -> {tags}")
    
    # 测试话题分类
    test_titles = [
        "明星演唱会门票售罄",
        "AI技术最新突破",
        "股市大涨",
        "足球比赛结果"
    ]
    for title in test_titles:
        category = categorize_topic(title)
        print(f"话题分类测试: '{title}' -> {category}")
    
    # 测试平台验证
    test_platforms = ['weibo', 'zhihu', 'invalid_platform']
    for platform in test_platforms:
        is_valid = validate_platform(platform)
        print(f"平台验证测试: '{platform}' -> {is_valid}")
    
    print("工具函数测试完成\n")

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
    
    result = process_hot_topics_batch(test_data_list)
    print("✅ 批量话题处理结果:")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    print("批量话题处理测试完成\n")

def test_tool_info():
    """测试工具信息获取"""
    print("=" * 50)
    print("测试工具信息获取")
    print("=" * 50)
    
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
    
    result = process_hot_topic(invalid_data)
    print(f"空标题测试: {result is None}")
    
    # 测试无效排名
    invalid_rank_data = {
        'platform': 'weibo',
        'title': '测试标题',
        'rank': 0  # 无效排名
    }
    
    result = process_hot_topic(invalid_rank_data)
    print(f"无效排名测试: {result is None}")
    
    # 测试无效热度值
    invalid_heat_data = {
        'platform': 'weibo',
        'title': '测试标题',
        'rank': 1,
        'heat_value': -100  # 负数热度值
    }
    
    result = process_hot_topic(invalid_heat_data)
    print(f"无效热度值测试: {result is None}")
    
    print("错误处理测试完成\n")

def main():
    """主测试函数"""
    print("热搜话题处理工具 - 测试")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 运行各项测试
    test_utils()
    test_single_topic()
    test_batch_topics()
    test_tool_info()
    test_error_handling()
    
    print("=" * 50)
    print("所有测试完成")
    print("=" * 50)

if __name__ == "__main__":
    main()
