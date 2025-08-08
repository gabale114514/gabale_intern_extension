"""
热榜今日(rebang.today)网站爬虫测试脚本
"""

import sys
import os
from datetime import datetime
import json

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from rebang_scraper import get_scraper, scrape_platform, scrape_all_platforms
from database_manager import get_db_manager

def test_fetch_page():
    """测试页面获取"""
    print("=" * 50)
    print("测试页面获取")
    print("=" * 50)
    
    scraper = get_scraper()
    url = "https://rebang.today/?tab=toutiao"
    
    print(f"获取页面: {url}")
    html_content = scraper.fetch_page(url)
    
    if html_content:
        print(f"✅ 页面获取成功，内容长度: {len(html_content)} 字符")
        # 打印页面的前200个字符
        print(f"页面内容预览: {html_content[:200]}...")
    else:
        print("❌ 页面获取失败")
    
    print("页面获取测试完成\n")
    return html_content is not None

def test_parse_hot_topics(html_content=None):
    """测试热搜话题解析"""
    print("=" * 50)
    print("测试热搜话题解析")
    print("=" * 50)
    
    scraper = get_scraper()
    
    if not html_content:
        url = "https://rebang.today/?tab=toutiao"
        html_content = scraper.fetch_page(url)
        if not html_content:
            print("❌ 页面获取失败，无法测试解析")
            return False
    
    topics = scraper.parse_hot_topics(html_content, 'toutiao')
    
    if topics:
        print(f"✅ 成功解析 {len(topics)} 个热搜话题")
        # 打印前3个话题
        for i, topic in enumerate(topics[:3]):
            print(f"\n话题 #{i+1}:")
            print(f"  标题: {topic['title']}")
            print(f"  排名: {topic['rank']}")
            print(f"  热度: {topic['heat_value']}")
            print(f"  标签: {topic['tags']}")
            print(f"  分类: {topic['category']}")
            print(f"  链接: {topic['url']}")
    else:
        print("❌ 热搜话题解析失败")
    
    print("热搜话题解析测试完成\n")
    return len(topics) > 0

def test_scrape_platform():
    """测试平台采集"""
    print("=" * 50)
    print("测试平台采集")
    print("=" * 50)
    
    platform_code = 'toutiao'
    print(f"采集平台: {platform_code}")
    
    result = scrape_platform(platform_code)
    
    if result and 'topics' in result and result['topics']:
        print(f"✅ 平台采集成功")
        print(f"  状态: {result['status']}")
        print(f"  总数: {result['stats']['total_count']}")
        print(f"  成功: {result['stats']['success_count']}")
        print(f"  重复: {result['stats']['duplicate_count']}")
        print(f"  错误: {result['stats']['error_count']}")
        print(f"  耗时: {result['duration']:.2f} 秒")
        
        # 打印前3个话题
        print("\n采集到的话题:")
        for i, topic in enumerate(result['topics'][:3]):
            print(f"  #{i+1}: {topic['title']} (热度: {topic['heat_value']})")
    else:
        print("❌ 平台采集失败")
    
    print("平台采集测试完成\n")
    return result and 'topics' in result and len(result['topics']) > 0

def test_scrape_all_platforms():
    """测试所有平台采集"""
    print("=" * 50)
    print("测试所有平台采集")
    print("=" * 50)
    
    print("采集所有平台")
    
    results = scrape_all_platforms()
    
    if results:
        print(f"✅ 所有平台采集完成")
        
        # 统计总体结果
        total_topics = sum(result['stats']['total_count'] for result in results.values() if 'stats' in result)
        success_topics = sum(result['stats']['success_count'] for result in results.values() if 'stats' in result)
        duplicate_topics = sum(result['stats']['duplicate_count'] for result in results.values() if 'stats' in result)
        error_topics = sum(result['stats']['error_count'] for result in results.values() if 'stats' in result)
        
        print(f"  总数: {total_topics}")
        print(f"  成功: {success_topics}")
        print(f"  重复: {duplicate_topics}")
        print(f"  错误: {error_topics}")
        
        # 打印各平台结果
        print("\n各平台采集结果:")
        for platform, result in results.items():
            if 'stats' in result:
                print(f"  - {platform}: {result['status']}, 总数: {result['stats']['total_count']}, "
                     f"成功: {result['stats']['success_count']}, 重复: {result['stats']['duplicate_count']}, "
                     f"错误: {result['stats']['error_count']}")
            else:
                print(f"  - {platform}: {result['status']}, 错误: {result.get('error', '未知错误')}")
    else:
        print("❌ 所有平台采集失败")
    
    print("所有平台采集测试完成\n")
    return bool(results)

def main():
    """主测试函数"""
    print("热榜今日(rebang.today)网站爬虫 - 测试")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 连接数据库
    db = get_db_manager()
    connected = db.connect()
    print(f"数据库连接: {'✅ 成功' if connected else '❌ 失败'}")
    
    if not connected:
        print("❌ 数据库连接失败，无法继续测试")
        return
    
    try:
        # 运行各项测试
        html_content = None
        if test_fetch_page():
            html_content = get_scraper().fetch_page("https://rebang.today/?tab=toutiao")
        
        test_parse_hot_topics(html_content)
        test_scrape_platform()
        
        # 是否测试所有平台（可能耗时较长）
        test_all = input("是否测试所有平台采集？(y/n): ").lower() == 'y'
        if test_all:
            test_scrape_all_platforms()
        
    finally:
        # 关闭数据库连接
        db.disconnect()
        print("数据库连接已关闭")
    
    print("=" * 50)
    print("所有测试完成")
    print("=" * 50)

if __name__ == "__main__":
    main()