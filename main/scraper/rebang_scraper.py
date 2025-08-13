import os
import logging
import requests
from requests.exceptions import RequestException
import time
import json
import re
import random
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlparse, parse_qs
from typing import List, Dict, Any, Optional, Tuple
from main.database.database_manager import mark_inactive_topics, save_hot_topic, save_collection_log, get_db_manager
# from config.platform_config import PLATFORM_CONFIG
from main.scraper.utils import clean_text, generate_hash
from bs4 import BeautifulSoup
from main.scraper.utils import parse_json_string, process_tags, safe_get, safe_parse_datetime
# 创建调试目录
os.makedirs('debug/full_responses', exist_ok=True)

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/hot_topic_tool.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 请求头
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:115.0) Gecko/20100101 Firefox/115.0'
]
# 平台配置
PLATFORM_CONFIG_DETAILED = {
    'weibo': {
        'api_url': 'https://api.rebang.today/v1/items?tab=weibo&sub_tab=search&version=2',
        'data_path': ['data', 'list'],
        'list_type': 'string',
        'field_mapping': {
            'title': 'title',
            'heat': 'heat_num',
            'url': 'www_url',
            'tag': 'label_name'
        }
    },
    'zhihu': {
        'api_url': 'https://api.rebang.today/v1/items?tab=zhihu&date_type=now&page=1&version=1',
        'data_path': ['data', 'list'],
        'list_type': 'string',
        'field_mapping': {
            'title': 'title',
            'heat': 'heat_str',
            'url': 'www_url',
            'tag': 'label_str'
        }
    },
    'douyin': {
        'api_url': 'https://api.rebang.today/v1/items?tab=douyin&date_type=now&page=1&version=1',
        'data_path': ['data', 'list'],
        'list_type': 'string',
        'field_mapping': {
            'title': 'title',
            'heat': 'heat_str',
            'url': 'aweme_id',
            'tag': 'describe'
        }
    },
    'toutiao': {
        'api_url': 'https://api.rebang.today/v1/items?tab=toutiao&date_type=now&page=1&version=1',
        'data_path': ['data', 'list'],
        'list_type': 'string',
        'field_mapping': {
            'title': 'title',
            'heat': 'hot_value',
            'url': 'www_url',
            'tag': 'label'
        }
    },
    'baidu': {
    'api_url': 'https://api.rebang.today/v1/items?tab=baidu-tieba&sub_tab=topic&page=1&version=1',
    'data_path': ['data', 'list'],
    'list_type': 'string',
    'field_mapping': {
        'title': 'name',
        'heat': 'discuss_num',
        'url': 'id',
        'tag': 'topic_tag'
    }
    },
    'bilibili': {
        'api_url': 'https://api.rebang.today/v1/items?tab=bilibili&sub_tab=popular&date_type=now&page=1&version=1',
        'data_path': ['data', 'list'],
        'list_type': 'string',
        'field_mapping': {
            'title': 'title',
            'heat': 'view',
            'url': 'bvid',
            'tag': 'owner_name'
        }
    },
    'xiaohongshu': {
        'api_url': 'https://api.rebang.today/v1/items?tab=xiaohongshu&sub_tab=hot-search&page=1&version=1',
        'data_path': ['data', 'list'],
        'list_type': 'string',
        'field_mapping': {
            'title': 'title',
            'heat': 'view_num',
            'url': 'www_url',
            'tag': 'tag'
        }
    },
    'xueqiu': {
        'api_url': 'https://api.rebang.today/v1/items?tab=xueqiu&sub_tab=topic&page=1&version=1',
        'data_path': ['data', 'list'],
        'list_type': 'string',
        'field_mapping': {
            'title': 'title',
            'heat': 'reason',
            'url': 'www_url',
            'tag': 'desc'
        }
    }
}

class RebangScraper:
    def __init__(self):
        self.session = requests.Session()
        self.base_url = "https://rebang.today"
        self.update_headers()
        self.platform_valid_api = {}  # 存储验证过的API
        self.db = get_db_manager()  # 数据库连接
        # 去重配置
        self.deduplication_config = {
            'hash_id_threshold': 0,  # hash_id完全匹配则视为重复
            'title_similarity_threshold': 0.85,  # 标题相似度阈值
            'time_window_minutes': 30  # 时间窗口内的重复判断
        }

    def update_headers(self):
        user_agent = random.choice(USER_AGENTS)
        self.session.headers.update({
            'User-Agent': user_agent,
            'Accept': 'application/json, text/plain, */*',
            'Referer': f'{self.base_url}/',
        })
    def get_platform_config(self, platform_code: str) -> Optional[Dict]:
        """获取平台专属配置"""
        return PLATFORM_CONFIG_DETAILED.get(platform_code)
    def _is_duplicate_topic(self, topic: Dict[str, Any]) -> Tuple[bool, Optional[int]]:
        """
        判断话题是否重复
        
        Args:
            topic: 待检查的话题数据
            
        Returns:
            Tuple[是否重复, 已存在的话题ID(如果重复)]
        """
        # 1. 首先检查hash_id是否存在（精确匹配）
        existing_by_hash = self.db.get_hot_topic_by_hash(topic['hash_id'])
        if existing_by_hash:
            # 使用改进的日期解析函数
            last_seen = safe_parse_datetime(existing_by_hash['last_seen_at'])
            
            if last_seen and (datetime.now() - last_seen < timedelta(minutes=self.deduplication_config['time_window_minutes'])):
                return True, existing_by_hash['id']
        
        # 2. 检查相似标题（模糊匹配）
        # 只检查相同平台、最近时间段的话题
        time_threshold = datetime.now() - timedelta(minutes=self.deduplication_config['time_window_minutes'])
        similar_topics = self.db.execute_query("""
            SELECT id, title FROM hot_topics 
            WHERE platform_id = (SELECT id FROM platforms WHERE code = %s)
            AND last_seen_at >= %s
            AND is_active = TRUE
        """, (topic['platform'], time_threshold))
        
        for existing in similar_topics:
            # 计算标题相似度
            similarity = self._title_similarity(topic['title'], existing['title'])
            if similarity >= self.deduplication_config['title_similarity_threshold']:
                return True, existing['id']
                
        return False, None
    def _title_similarity(self, title1: str, title2: str) -> float:
        """
        计算两个标题的相似度
        
        Args:
            title1: 第一个标题
            title2: 第二个标题
            
        Returns:
            相似度分数(0-1)
        """
        # 简单分词（按空格和标点）
        words1 = set(re.findall(r'\w+', title1.lower()))
        words2 = set(re.findall(r'\w+', title2.lower()))
        
        if not words1 or not words2:
            return 0.0
            
        # 计算Jaccard系数: 交集大小 / 并集大小
        return len(words1 & words2) / len(words1 | words2)
    def fetch_api_data(self, platform_code: str, max_retries: int = 2) -> Optional[Dict]:
        """获取并验证API数据（返回解析后的JSON）"""
        config = self.get_platform_config(platform_code)
        if not config:
            logger.error(f"平台 {platform_code} 无配置，跳过")
            return None

        api_url = config['api_url']
        parsed = urlparse(api_url)
        base_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        params = parse_qs(parsed.query)
        params['t'] = int(time.time() * 1000)  # 动态时间戳

        retries = 0
        while retries <= max_retries:
            try:
                self.update_headers()
                response = self.session.get(base_url, params=params, timeout=10)
                response.raise_for_status()
                # 保存原始响应用于调试
                timestamp = int(time.time())
                debug_file = f"debug/full_responses/api_{platform_code}_{timestamp}.txt"
                with open(debug_file, 'w', encoding='utf-8') as f:
                    f.write(f"URL: {response.url}\n{response.text}")
                # 解析为JSON
                return response.json()
            except (RequestException, json.JSONDecodeError) as e:
                logger.warning(f"平台 {platform_code} API请求/解析失败 ({retries+1}/{max_retries+1}): {e}")
                retries += 1
                time.sleep(1 * retries)
        return None
    def parse_api_data(self, api_data: Dict, platform_code: str) -> List[Dict]:
        """根据平台配置解析API数据"""
        config = self.get_platform_config(platform_code)
        if not config:
            return []

        topics = []
        # 1. 定位数据列表（按平台配置的data_path）
        current_data = api_data
        for key in config['data_path']:
            current_data = safe_get(current_data, key)
            if current_data is None:
                logger.warning(f"平台 {platform_code} 未找到数据路径: {'->'.join(config['data_path'])}")
                return []

        # 2. 处理list类型（字符串需解码为数组）
        items = None
        if config['list_type'] == 'string':
            # 如抖音的list是JSON字符串
            items = parse_json_string(current_data)
        else:
            # 直接是数组
            items = current_data if isinstance(current_data, list) else None

        if not isinstance(items, list):
            logger.warning(f"平台 {platform_code} 数据列表格式错误，不是数组: {type(items)}")
            return []
        logger.info(f"平台 {platform_code} 找到 {len(items)} 条原始数据")

        # 3. 提取字段（按平台字段映射）
        field_map = config['field_mapping']
        for idx, item in enumerate(items, 1):
            if not isinstance(item, dict):
                continue  # 跳过非字典项
            # 映射字段
            topic = {
                "platform": platform_code,
                "rank": idx,
                # 确保timestamp是正确的ISO格式字符串
                "timestamp": datetime.now().isoformat(),
            }
            # 标题（必须字段，缺失则跳过）
            title = clean_text(safe_get(item, field_map['title'], ""))
            if not title:
                continue
            topic['title'] = title
            # 热度（处理heat_str中的数字+单位）
            heat_str = safe_get(item, field_map['heat'], "")
            topic['heat_value'] = self.extract_heat_value(heat_str)  # 统一字段名为heat_value
            # 链接（拼接完整URL）
            url_id = safe_get(item, field_map['url'], "")
            if url_id:
                # 不同平台链接格式不同，这里简化处理
                topic['url'] = f"https://rebang.today/item/{url_id}" if url_id else ""
            # 标签
            topic['tags'] = process_tags(clean_text(safe_get(item, field_map['tag'], "")))
            # 生成唯一ID（优化hash生成逻辑）
            topic['hash_id'] = generate_hash(f"{title}_{platform_code}")  # 移除idx，避免排名变化导致hash变化
            topics.append(topic)

        logger.info(f"平台 {platform_code} 解析出 {len(topics)} 个有效话题")
        return topics
    def extract_heat_value(self, heat_str: Any) -> Optional[int]:
        """适配数值型热度（如微博heat_num）和字符串型热度"""
        if isinstance(heat_str, int):
            return heat_str
        if not heat_str or not isinstance(heat_str, str):
            return None
        # 原字符串型热度解析逻辑（保留，适配其他平台）
        match = re.search(r'(\d+\.?\d*)\s*([w万亿]?)', heat_str)
        if not match:
            return None
        value = float(match.group(1))
        unit = match.group(2)
        if unit == '万' or unit == 'w':
            value *= 10000
        elif unit == '亿':
            value *= 100000000
        return int(value)
    def save_topics(self, topics: List[Dict]) -> Dict[str, int]:
        """保存话题到数据库（强化去重逻辑）"""
        stats = {'total_count': len(topics), 'success_count': 0, 'error_count': 0, 'duplicate_count': 0}
        
        for topic in topics:
            try:
                # 第一步：检查是否重复
                is_duplicate, existing_id = self._is_duplicate_topic(topic)
                
                if is_duplicate and existing_id:
                    # 准备更新数据（主要是排名、热度和时间）
                    update_data = {
                        'rank': topic['rank'],
                        'heat_value': topic['heat_value'],
                        'last_seen_at': datetime.now().isoformat(),  # 存储ISO格式字符串
                        'is_active': True
                    }
                    # 如果有标签，添加到更新数据
                    if 'tags' in topic and topic['tags']:
                        update_data['tags'] = process_tags(topic['tags'])
                        
                    # 执行更新
                    if self.db.update_hot_topic(existing_id, update_data):
                        stats['success_count'] += 1
                    stats['duplicate_count'] += 1
                else:
                    # 新话题 - 插入
                    # 确保时间字段是ISO格式字符串
                    topic_data = {** topic,
                        'first_seen_at': datetime.now().isoformat(),
                        'last_seen_at': datetime.now().isoformat(),
                        'tags': process_tags(topic.get('tags', []))  # 确保标签经过处理
                    }
                    result = save_hot_topic(topic_data)
                    if result:
                        stats['success_count'] += 1
                    else:
                        stats['error_count'] += 1
                        
            except Exception as e:
                logger.error(f"保存话题失败: {topic['title']}, 错误: {e}")
                stats['error_count'] += 1
        
        return stats
    def scrape_platform(self, platform_code: str) -> Tuple[List[Dict], Dict[str, int]]:
            """采集单个平台（优先API，失败则网页解析）"""
            logger.info(f"开始采集平台 {platform_code}")
            
            # 确保数据库连接
            if not self.db.connection or not self.db.connection.is_connected():
                self.db.connect()
            
            # 1. 采集数据
            api_data = self.fetch_api_data(platform_code)
            topics = self.parse_api_data(api_data, platform_code) if api_data else []
            
            # # 2. 如果API失败，尝试网页解析
            # if not topics:
            #     logger.info(f"平台 {platform_code} API解析失败，尝试网页解析")
            #     topics = self.scrape_platform_via_web(platform_code)
            
            # 3. 处理采集结果
            if topics:
                # 获取当前所有hash_id用于标记失效话题
                current_hashes = [t['hash_id'] for t in topics]
                mark_inactive_topics(platform_code, current_hashes)
                
                # 保存话题并统计
                save_stats = self.save_topics(topics)
            else:
                save_stats = {
                    'total_count': 0,
                    'success_count': 0,
                    'error_count': 0,
                    'duplicate_count': 0
                }
            
            return topics, {
                'total_count': len(topics),
                'success_count': save_stats['success_count'],
                'error_count': save_stats['error_count']
            }
    def scrape_all_platforms(self) -> Dict[str, Dict]:
        """采集所有平台"""
        results = {}
        # 确保数据库连接
        if not self.db.connection or not self.db.connection.is_connected():
            self.db.connect()
        # 从数据库获取所有启用的平台
        enabled_platforms = self.db.get_enabled_platforms()  # 调用数据库层的方法
        enabled_codes = {p['code'] for p in enabled_platforms}  # 提取启用的平台code
        
        for platform_code in PLATFORM_CONFIG_DETAILED.keys():
            if platform_code not in enabled_codes:
                logger.info(f"平台 {platform_code} 已禁用，跳过")
                continue
                
            try:
                start_time = datetime.now()
                topics, scrape_stats = self.scrape_platform(platform_code)
                end_time = datetime.now()  # 修复之前的变量未定义错误
                
                # 确定采集状态
                if scrape_stats['success_count'] == scrape_stats['total_count']:
                    status = 'success'
                elif scrape_stats['success_count'] > 0:
                    status = 'partial'
                else:
                    status = 'failed'
                
                # 保存采集日志时使用ISO格式字符串
                save_collection_log(
                    platform=platform_code,
                    status=status,
                    stats={
                        'total_count': scrape_stats['total_count'],
                        'success_count': scrape_stats['success_count'],
                        'error_count': scrape_stats['error_count'],
                        'duplicate_count': scrape_stats['total_count'] - scrape_stats['success_count'] - scrape_stats['error_count']
                    },
                    start_time=start_time.isoformat(),
                    end_time=end_time.isoformat()
                )
                
                results[platform_code] = {
                    'status': status,
                    'stats': scrape_stats,
                    'duration': (end_time - start_time).total_seconds()
                }
                logger.info(f"平台 {platform_code} 完成: 成功保存 {scrape_stats['success_count']} 条，重复 {scrape_stats['total_count'] - scrape_stats['success_count'] - scrape_stats['error_count']} 条")
                time.sleep(random.uniform(2, 5))  # 反爬延迟
                
            except Exception as e:
                logger.error(f"平台 {platform_code} 采集异常: {e}")
                save_collection_log(
                    platform=platform_code,
                    status='failed',
                    stats={
                        'total_count': 0,
                        'success_count': 0,
                        'error_count': 1,
                        'duplicate_count': 0
                    },
                    start_time=datetime.now().isoformat(),
                    end_time=datetime.now().isoformat(),
                    error_message=str(e)
                )
                results[platform_code] = {'status': 'error', 'error': str(e)}
                
        return results

_scraper_instance = None

def get_scraper() -> RebangScraper:
    global _scraper_instance
    if not _scraper_instance:
        _scraper_instance = RebangScraper()
    return _scraper_instance

def run_scheduled_scraping():
    logger.info("开始定时采集所有平台")
    scraper = get_scraper()
    results = scraper.scrape_all_platforms()
    total_success = sum(r['stats']['success_count'] for r in results.values() if 'stats' in r)
    logger.info(f"定时采集完成，总成功数: {total_success}")
    return results

# 在爬虫主流程中使用
if __name__ == "__main__":
    print(f"热榜今日爬虫 - 开始采集 ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
    db = get_db_manager()
    if not db.connect():
        print("数据库连接失败")
        exit(1)
    try:
        results = run_scheduled_scraping()
        print("\n采集结果:")
        for platform, res in results.items():
            if 'stats' in res:
                print(f"- {platform}: {res['status']}, 成功保存: {res['stats']['success_count']}, 重复: {res['stats']['total_count'] - res['stats']['success_count'] - res['stats']['error_count']}")
            else:
                print(f"- {platform}: {res['status']}, 错误: {res['error']}")
            
    finally:
        db.disconnect()
    