"""
热榜今日(rebang.today)网站爬虫 - 用于采集各平台热搜榜数据
"""

import logging
import requests
from requests.exceptions import RequestException
import time
from datetime import datetime
import random
import hashlib
import json
from typing import List, Dict, Any, Optional, Tuple
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse, parse_qs
import traceback

from config import PLATFORM_CONFIG
from utils import clean_text, extract_tags, categorize_topic, generate_hash
from database_manager import save_hot_topic, save_collection_log, get_db_manager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('hot_topic_tool.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 请求头
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36'
]

# 平台映射（rebang.today平台标识 -> 我们系统中的平台代码）
PLATFORM_MAPPING = {
    'weibo': 'weibo',
    'zhihu': 'zhihu',
    'toutiao': 'toutiao',
    'baidu': 'baidu',
    'douyin': 'douyin',
    'bilibili': 'bilibili',
    'xhs': 'xiaohongshu',  # 小红书
    'xueqiu': 'xueqiu'     # 雪球
}

# 反向映射（用于URL参数）
REVERSE_PLATFORM_MAPPING = {v: k for k, v in PLATFORM_MAPPING.items()}

class RebangScraper:
    """热榜今日网站爬虫，用于采集各平台热搜榜数据"""
    
    def __init__(self):
        """初始化爬虫"""
        self.session = requests.Session()
        self.base_url = "https://rebang.today"
        self.update_headers()
    
    def update_headers(self) -> None:
        """更新请求头"""
        user_agent = random.choice(USER_AGENTS)
        self.session.headers.update({
            'User-Agent': user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
            'Referer': self.base_url
        })
    
    def fetch_page(self, url: str, max_retries: int = 3, timeout: int = 10) -> Optional[str]:
        """
        获取页面内容
        
        Args:
            url: 页面URL
            max_retries: 最大重试次数
            timeout: 超时时间（秒）
            
        Returns:
            页面内容，如果失败则返回None
        """
        retries = 0
        while retries < max_retries:
            try:
                self.update_headers()
                response = self.session.get(url, timeout=timeout)
                response.raise_for_status()
                return response.text
            except RequestException as e:
                logger.warning(f"获取页面失败 ({retries+1}/{max_retries}): {url}, 错误: {e}")
                retries += 1
                time.sleep(2 * retries)  # 指数退避
        
        logger.error(f"获取页面失败，已达到最大重试次数: {url}")
        return None
    
    def get_platform_url(self, platform_code: str) -> str:
        """
        获取平台对应的URL
        
        Args:
            platform_code: 平台代码
            
        Returns:
            平台URL
        """
        if platform_code not in REVERSE_PLATFORM_MAPPING:
            return f"{self.base_url}/"
        
        rebang_platform = REVERSE_PLATFORM_MAPPING[platform_code]
        return f"{self.base_url}/?tab={rebang_platform}"
    
    def extract_platform_from_url(self, url: str) -> Optional[str]:
        """
        从URL中提取平台代码
        
        Args:
            url: 页面URL
            
        Returns:
            平台代码，如果无法提取则返回None
        """
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        
        if 'tab' in query_params and query_params['tab']:
            tab = query_params['tab'][0]
            return PLATFORM_MAPPING.get(tab)
        
        return None
    
    def parse_hot_topics(self, html_content: str, platform_code: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        解析热搜话题
        
        Args:
            html_content: 页面HTML内容
            platform_code: 平台代码，如果为None则尝试从页面中提取
            
        Returns:
            热搜话题列表
        """
        if not html_content:
            return []
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 尝试从页面中提取当前平台
        if not platform_code:
            # 查找当前激活的标签
            active_tab = soup.select_one('.tab-item.active')
            if active_tab:
                tab_text = active_tab.get_text(strip=True).lower()
                for rebang_platform, our_platform in PLATFORM_MAPPING.items():
                    if rebang_platform in tab_text:
                        platform_code = our_platform
                        break
        
        if not platform_code:
            logger.warning("无法确定当前平台，使用默认平台 'toutiao'")
            platform_code = 'toutiao'
        
        logger.info(f"开始解析平台 {platform_code} 的热搜榜")
        
        # 查找热搜列表
        topics_list = []
        
        # 查找热搜项
        hot_items = soup.select('.hot-list .item')
        
        for index, item in enumerate(hot_items):
            try:
                # 提取排名
                rank_elem = item.select_one('.index')
                rank = int(rank_elem.get_text(strip=True)) if rank_elem else (index + 1)
                
                # 提取标题
                title_elem = item.select_one('.title')
                if not title_elem:
                    continue
                
                title = clean_text(title_elem.get_text(strip=True))
                
                # 提取链接
                link = None
                link_elem = title_elem.parent
                if link_elem and link_elem.name == 'a' and link_elem.has_attr('href'):
                    link = urljoin(self.base_url, link_elem['href'])
                
                # 提取热度
                heat_elem = item.select_one('.hot')
                heat_text = heat_elem.get_text(strip=True) if heat_elem else None
                heat_value = self.extract_heat_value(heat_text)
                
                # 提取标签
                tag_elem = item.select_one('.tag')
                tag_text = tag_elem.get_text(strip=True) if tag_elem else None
                tags = [tag_text] if tag_text else []
                
                # 从标题中提取更多标签
                title_tags = extract_tags(title)
                tags.extend(title_tags)
                tags = list(set(tags))  # 去重
                
                # 生成哈希ID
                hash_id = generate_hash(f"{platform_code}_{title}")
                
                # 创建话题数据
                topic_data = {
                    'platform': platform_code,
                    'title': title,
                    'rank': rank,
                    'url': link,
                    'heat_value': heat_value,
                    'hash_id': hash_id,
                    'category': categorize_topic(title),
                    'tags': tags
                }
                
                topics_list.append(topic_data)
                
            except Exception as e:
                logger.error(f"解析话题时发生错误: {platform_code} #{index+1}, 错误: {e}")
                logger.error(traceback.format_exc())
        
        logger.info(f"成功解析 {len(topics_list)} 个热搜话题")
        return topics_list
    
    def extract_heat_value(self, text: str) -> Optional[int]:
        """
        提取热度值
        
        Args:
            text: 热度文本
            
        Returns:
            热度值，如果无法提取则返回None
        """
        if not text:
            return None
        
        # 提取数字
        numbers = re.findall(r'\d+\.?\d*', text)
        if not numbers:
            return None
        
        # 获取第一个数字
        value = float(numbers[0])
        
        # 处理单位
        if '万' in text:
            value *= 10000
        elif '亿' in text:
            value *= 100000000
        
        return int(value)
    
    def scrape_platform(self, platform_code: str) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
        """
        采集指定平台的热搜榜
        
        Args:
            platform_code: 平台代码
            
        Returns:
            (热搜话题列表, 统计信息)
        """
        if platform_code not in REVERSE_PLATFORM_MAPPING:
            logger.error(f"不支持的平台: {platform_code}")
            return [], {'total_count': 0, 'success_count': 0, 'error_count': 1, 'duplicate_count': 0}
        
        url = self.get_platform_url(platform_code)
        
        logger.info(f"开始采集平台 {platform_code} 的热搜榜: {url}")
        
        # 获取页面内容
        html_content = self.fetch_page(url)
        if not html_content:
            return [], {'total_count': 0, 'success_count': 0, 'error_count': 1, 'duplicate_count': 0}
        
        # 解析热搜话题
        topics = self.parse_hot_topics(html_content, platform_code)
        
        # 统计信息
        stats = {
            'total_count': len(topics),
            'success_count': len(topics),
            'error_count': 0,
            'duplicate_count': 0
        }
        
        return topics, stats
    
    def save_topics(self, topics: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        保存热搜话题到数据库
        
        Args:
            topics: 话题列表
            
        Returns:
            统计信息
        """
        stats = {
            'total_count': len(topics),
            'success_count': 0,
            'error_count': 0,
            'duplicate_count': 0
        }
        
        for topic in topics:
            try:
                result = save_hot_topic(topic)
                if isinstance(result, int) and result > 0:
                    # 新增话题
                    stats['success_count'] += 1
                elif isinstance(result, bool) and result:
                    # 更新话题
                    stats['duplicate_count'] += 1
                else:
                    # 保存失败
                    stats['error_count'] += 1
            except Exception as e:
                logger.error(f"保存话题时发生错误: {topic['title']}, 错误: {e}")
                logger.error(traceback.format_exc())
                stats['error_count'] += 1
        
        return stats
    
    def scrape_all_platforms(self) -> Dict[str, Dict[str, Any]]:
        """
        采集所有平台的热搜榜
        
        Returns:
            按平台分组的统计信息
        """
        results = {}
        
        for platform_code in PLATFORM_CONFIG:
            if platform_code not in REVERSE_PLATFORM_MAPPING:
                continue
            
            if not PLATFORM_CONFIG[platform_code]['enabled']:
                logger.info(f"平台 {platform_code} 已禁用，跳过采集")
                continue
            
            try:
                # 记录开始时间
                start_time = datetime.now()
                
                # 采集平台
                topics, scrape_stats = self.scrape_platform(platform_code)
                
                # 保存话题
                save_stats = self.save_topics(topics)
                
                # 记录结束时间
                end_time = datetime.now()
                
                # 合并统计信息
                stats = {
                    'total_count': scrape_stats['total_count'],
                    'success_count': save_stats['success_count'],
                    'error_count': scrape_stats['error_count'] + save_stats['error_count'],
                    'duplicate_count': save_stats['duplicate_count']
                }
                
                # 确定采集状态
                if stats['error_count'] == 0:
                    status = 'success'
                elif stats['success_count'] == 0:
                    status = 'failed'
                else:
                    status = 'partial'
                
                # 保存采集记录
                save_collection_log(
                    platform=platform_code,
                    status=status,
                    stats=stats,
                    start_time=start_time,
                    end_time=end_time
                )
                
                # 记录结果
                results[platform_code] = {
                    'status': status,
                    'stats': stats,
                    'start_time': start_time.isoformat(),
                    'end_time': end_time.isoformat(),
                    'duration': (end_time - start_time).total_seconds()
                }
                
                logger.info(f"平台 {platform_code} 采集完成: {status}, 总数: {stats['total_count']}, "
                           f"成功: {stats['success_count']}, 重复: {stats['duplicate_count']}, "
                           f"错误: {stats['error_count']}")
                
                # 随机延迟，避免请求过于频繁
                time.sleep(random.uniform(1, 3))
                
            except Exception as e:
                logger.error(f"采集平台 {platform_code} 时发生错误: {e}")
                logger.error(traceback.format_exc())
                
                # 记录失败结果
                results[platform_code] = {
                    'status': 'failed',
                    'error': str(e)
                }
        
        return results

# 单例模式
_scraper_instance = None

def get_scraper() -> RebangScraper:
    """
    获取爬虫实例（单例模式）
    
    Returns:
        爬虫实例
    """
    global _scraper_instance
    if _scraper_instance is None:
        _scraper_instance = RebangScraper()
    return _scraper_instance

def scrape_platform(platform_code: str) -> Dict[str, Any]:
    """
    采集指定平台的热搜榜
    
    Args:
        platform_code: 平台代码
        
    Returns:
        采集结果
    """
    scraper = get_scraper()
    
    # 记录开始时间
    start_time = datetime.now()
    
    # 采集平台
    topics, scrape_stats = scraper.scrape_platform(platform_code)
    
    # 保存话题
    save_stats = scraper.save_topics(topics)
    
    # 记录结束时间
    end_time = datetime.now()
    
    # 合并统计信息
    stats = {
        'total_count': scrape_stats['total_count'],
        'success_count': save_stats['success_count'],
        'error_count': scrape_stats['error_count'] + save_stats['error_count'],
        'duplicate_count': save_stats['duplicate_count']
    }
    
    # 确定采集状态
    if stats['error_count'] == 0:
        status = 'success'
    elif stats['success_count'] == 0:
        status = 'failed'
    else:
        status = 'partial'
    
    # 保存采集记录
    save_collection_log(
        platform=platform_code,
        status=status,
        stats=stats,
        start_time=start_time,
        end_time=end_time
    )
    
    return {
        'status': status,
        'stats': stats,
        'topics': topics,
        'start_time': start_time.isoformat(),
        'end_time': end_time.isoformat(),
        'duration': (end_time - start_time).total_seconds()
    }

def scrape_all_platforms() -> Dict[str, Dict[str, Any]]:
    """
    采集所有平台的热搜榜
    
    Returns:
        按平台分组的采集结果
    """
    scraper = get_scraper()
    return scraper.scrape_all_platforms()

def run_scheduled_scraping():
    """
    运行定时采集
    """
    logger.info("开始定时采集所有平台热搜榜")
    results = scrape_all_platforms()
    
    # 统计总体结果
    total_topics = sum(result['stats']['total_count'] for result in results.values() if 'stats' in result)
    success_topics = sum(result['stats']['success_count'] for result in results.values() if 'stats' in result)
    duplicate_topics = sum(result['stats']['duplicate_count'] for result in results.values() if 'stats' in result)
    error_topics = sum(result['stats']['error_count'] for result in results.values() if 'stats' in result)
    
    logger.info(f"定时采集完成: 总数: {total_topics}, 成功: {success_topics}, "
               f"重复: {duplicate_topics}, 错误: {error_topics}")
    
    return results

if __name__ == "__main__":
    """
    直接运行此脚本时，执行采集
    """
    print("热榜今日(rebang.today)网站爬虫 - 开始采集")
    print(f"采集时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 连接数据库
    db = get_db_manager()
    if not db.connect():
        print("❌ 数据库连接失败，无法继续")
        exit(1)
    
    try:
        # 采集所有平台
        results = run_scheduled_scraping()
        
        # 显示结果
        print("\n采集结果:")
        for platform, result in results.items():
            if 'stats' in result:
                print(f"- {platform}: {result['status']}, 总数: {result['stats']['total_count']}, "
                     f"成功: {result['stats']['success_count']}, 重复: {result['stats']['duplicate_count']}, "
                     f"错误: {result['stats']['error_count']}")
            else:
                print(f"- {platform}: {result['status']}, 错误: {result.get('error', '未知错误')}")
        
        print("\n✅ 采集完成")
        
    finally:
        # 关闭数据库连接
        db.disconnect()