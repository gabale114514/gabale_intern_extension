"""
网页元素分析器 - 用于采集各平台热搜榜数据
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
from urllib.parse import urljoin
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

# 平台配置
PLATFORM_SCRAPERS = {
    'weibo': {
        'url': 'https://s.weibo.com/top/summary',
        'list_selector': 'tbody tr',
        'title_selector': 'td.td-02 a',
        'rank_selector': 'td.td-01',
        'tag_selector': 'td.td-03',
        'heat_selector': None,
        'link_selector': 'td.td-02 a',
        'link_prefix': 'https://s.weibo.com'
    },
    'zhihu': {
        'url': 'https://www.zhihu.com/hot',
        'list_selector': '.HotList-item',
        'title_selector': '.HotItem-title',
        'rank_selector': '.HotItem-index',
        'tag_selector': '.HotItem-label',
        'heat_selector': '.HotItem-metrics',
        'link_selector': '.HotItem-title a',
        'link_prefix': ''
    },
    'xiaohongshu': {
        'url': 'https://www.xiaohongshu.com/explore',
        'list_selector': '.explore-feed-flow-item',
        'title_selector': '.explore-feed-card-title',
        'rank_selector': None,
        'tag_selector': '.hot-tag',
        'heat_selector': '.interaction-info',
        'link_selector': 'a.explore-feed-card',
        'link_prefix': 'https://www.xiaohongshu.com'
    },
    'toutiao': {
        'url': 'https://www.toutiao.com/hot-event/hot-board/',
        'list_selector': '.hot-board-item',
        'title_selector': '.hot-board-item-title',
        'rank_selector': '.hot-board-item-index',
        'tag_selector': '.hot-board-item-label',
        'heat_selector': '.hot-board-item-num',
        'link_selector': '.hot-board-item-title a',
        'link_prefix': 'https://www.toutiao.com'
    },
    'baidu': {
        'url': 'https://top.baidu.com/board?tab=realtime',
        'list_selector': '.category-wrap_iQLoo',
        'title_selector': '.c-single-text-ellipsis',
        'rank_selector': '.index_1Ew5p',
        'tag_selector': '.hot-tag_1G080',
        'heat_selector': '.hot-index_1Bl1a',
        'link_selector': 'a.item-wrap_2oCLZ',
        'link_prefix': ''
    },
    'xueqiu': {
        'url': 'https://xueqiu.com/today',
        'list_selector': '.hot-article',
        'title_selector': '.hot-article-title',
        'rank_selector': '.hot-article-index',
        'tag_selector': '.hot-article-tag',
        'heat_selector': '.hot-article-read',
        'link_selector': '.hot-article-title a',
        'link_prefix': 'https://xueqiu.com'
    },
    'douyin': {
        'url': 'https://www.douyin.com/hot',
        'list_selector': '.rank-item',
        'title_selector': '.rank-title',
        'rank_selector': '.rank-index',
        'tag_selector': '.rank-tag',
        'heat_selector': '.rank-hot-value',
        'link_selector': '.rank-title a',
        'link_prefix': 'https://www.douyin.com'
    },
    'bilibili': {
        'url': 'https://www.bilibili.com/v/popular/rank/all',
        'list_selector': '.rank-item',
        'title_selector': '.title',
        'rank_selector': '.num',
        'tag_selector': '.badge',
        'heat_selector': '.data-box .view',
        'link_selector': 'a.title',
        'link_prefix': 'https://www.bilibili.com'
    }
}

class WebElementAnalyzer:
    """网页元素分析器，用于采集各平台热搜榜数据"""
    
    def __init__(self):
        """初始化分析器"""
        self.session = requests.Session()
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
            'Cache-Control': 'max-age=0'
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
    
    def parse_element_text(self, element, selector: str) -> Optional[str]:
        """
        解析元素文本
        
        Args:
            element: BeautifulSoup元素
            selector: CSS选择器
            
        Returns:
            元素文本，如果不存在则返回None
        """
        if not selector:
            return None
        
        selected = element.select_one(selector)
        if selected:
            return selected.get_text(strip=True)
        return None
    
    def parse_element_attr(self, element, selector: str, attr: str) -> Optional[str]:
        """
        解析元素属性
        
        Args:
            element: BeautifulSoup元素
            selector: CSS选择器
            attr: 属性名
            
        Returns:
            元素属性值，如果不存在则返回None
        """
        if not selector:
            return None
        
        selected = element.select_one(selector)
        if selected and selected.has_attr(attr):
            return selected[attr]
        return None
    
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
    
    def extract_rank(self, text: str) -> Optional[int]:
        """
        提取排名
        
        Args:
            text: 排名文本
            
        Returns:
            排名值，如果无法提取则返回None
        """
        if not text:
            return None
        
        # 提取数字
        numbers = re.findall(r'\d+', text)
        if not numbers:
            return None
        
        return int(numbers[0])
    
    def scrape_platform(self, platform_code: str) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
        """
        采集指定平台的热搜榜
        
        Args:
            platform_code: 平台代码
            
        Returns:
            (热搜话题列表, 统计信息)
        """
        if platform_code not in PLATFORM_SCRAPERS:
            logger.error(f"不支持的平台: {platform_code}")
            return [], {'total_count': 0, 'success_count': 0, 'error_count': 1, 'duplicate_count': 0}
        
        scraper_config = PLATFORM_SCRAPERS[platform_code]
        url = scraper_config['url']
        
        logger.info(f"开始采集平台 {platform_code} 的热搜榜: {url}")
        
        # 获取页面内容
        html_content = self.fetch_page(url)
        if not html_content:
            return [], {'total_count': 0, 'success_count': 0, 'error_count': 1, 'duplicate_count': 0}
        
        # 解析页面
        soup = BeautifulSoup(html_content, 'html.parser')
        items = soup.select(scraper_config['list_selector'])
        
        logger.info(f"找到 {len(items)} 个热搜话题")
        
        # 统计信息
        stats = {
            'total_count': len(items),
            'success_count': 0,
            'error_count': 0,
            'duplicate_count': 0
        }
        
        # 解析话题
        topics = []
        for index, item in enumerate(items):
            try:
                # 提取标题
                title = self.parse_element_text(item, scraper_config['title_selector'])
                if not title:
                    logger.warning(f"无法提取标题: {platform_code} #{index+1}")
                    stats['error_count'] += 1
                    continue
                
                # 清理标题
                title = clean_text(title)
                
                # 提取排名
                rank_text = self.parse_element_text(item, scraper_config['rank_selector'])
                rank = self.extract_rank(rank_text) if rank_text else (index + 1)
                
                # 提取链接
                link = self.parse_element_attr(item, scraper_config['link_selector'], 'href')
                if link and scraper_config['link_prefix']:
                    link = urljoin(scraper_config['link_prefix'], link)
                
                # 提取热度
                heat_text = self.parse_element_text(item, scraper_config['heat_selector'])
                heat_value = self.extract_heat_value(heat_text)
                
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
                    'tags': extract_tags(title)
                }
                
                topics.append(topic_data)
                stats['success_count'] += 1
                
            except Exception as e:
                logger.error(f"解析话题时发生错误: {platform_code} #{index+1}, 错误: {e}")
                logger.error(traceback.format_exc())
                stats['error_count'] += 1
        
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
            if platform_code not in PLATFORM_SCRAPERS:
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
_analyzer_instance = None

def get_analyzer() -> WebElementAnalyzer:
    """
    获取分析器实例（单例模式）
    
    Returns:
        分析器实例
    """
    global _analyzer_instance
    if _analyzer_instance is None:
        _analyzer_instance = WebElementAnalyzer()
    return _analyzer_instance

def scrape_platform(platform_code: str) -> Dict[str, Any]:
    """
    采集指定平台的热搜榜
    
    Args:
        platform_code: 平台代码
        
    Returns:
        采集结果
    """
    analyzer = get_analyzer()
    
    # 记录开始时间
    start_time = datetime.now()
    
    # 采集平台
    topics, scrape_stats = analyzer.scrape_platform(platform_code)
    
    # 保存话题
    save_stats = analyzer.save_topics(topics)
    
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
    analyzer = get_analyzer()
    return analyzer.scrape_all_platforms()

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