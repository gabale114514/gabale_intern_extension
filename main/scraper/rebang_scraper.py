import os
import logging
import requests
from requests.exceptions import RequestException
import time
import json
import re
import random
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlparse, parse_qs, urlencode
from typing import List, Dict, Any, Optional, Tuple
# 假设其他导入保持不变
from main.database.database_manager import mark_inactive_topics, save_hot_topic, save_collection_log, get_db_manager
from main.scraper.utils import parse_json_string, process_tags, safe_get, safe_parse_datetime, clean_text, generate_hash


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


# 平台配置（核心改造：拆分base_url和default_params，支持动态参数）
PLATFORM_CONFIG = {
    'weibo': {
        'base_url': 'https://api.rebang.today/v1/items',  # 基础路径（固定不变）
        'default_params': {  # 默认参数（可被动态参数覆盖）
            'tab': 'weibo',
            'sub_tab': 'search',  # 可改为'ent'/'news'等
            'version': '2'
        },
        'data_path': ['data', 'list'],  # 数据列表在JSON中的路径
        'list_type': 'string',  # 数据列表类型（string需解码为数组）
        'field_mapping': {  # 字段映射（平台字段->统一字段）
            'title': 'title',
            'heat': 'heat_num',
            'url': 'www_url',
            'tag': 'label_name'
        }
    },
    'zhihu': {
        'base_url': 'https://api.rebang.today/v1/items',
        'default_params': {
            'tab': 'zhihu',
            'date_type': 'now',
            'page': '1',
            'version': '1'
        },
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
        'base_url': 'https://api.rebang.today/v1/items',
        'default_params': {
            'tab': 'douyin',
            'date_type': 'now',
            'page': '1',
            'version': '1'
        },
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
        'base_url': 'https://api.rebang.today/v1/items',
        'default_params': {
            'tab': 'toutiao',
            'date_type': 'now',
            'page': '1',
            'version': '1'
        },
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
    'base_url': 'https://api.rebang.today/v1/items',
    'default_params': {
            'tab': 'baidu',
            'sub_tab': 'realtime',
            'page': '1',
            'version': '1'
        },
    'data_path': ['data', 'list'],
    'list_type': 'string',
    'field_mapping': {
        'title': 'word',
        'heat': 'hot_score',
        'url': 'query',
        'tag': 'hot_tag'
    }
    },
    'bilibili': {
        'base_url': 'https://api.rebang.today/v1/items',
    'default_params': {
            'tab': 'bilibili',
            'sub_tab': 'popular',
            'date_type': 'now',
            'page': '1',
            'version': '1'
        },
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
        'base_url': 'https://api.rebang.today/v1/items',
    'default_params': {
            'tab': 'xiaohongshu',
            'sub_tab': 'hot-search',
            'page': '1',
            'version': '1'
        },
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
        'base_url': 'https://api.rebang.today/v1/items',
    'default_params': {
            'tab': 'xueqiu',
            'sub_tab': 'topic',
            'page': '1',
            'version': '1'
        },
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
            'hash_id_threshold': 0,
            'title_similarity_threshold': 0.85,
            'time_window_minutes': 30
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
        return PLATFORM_CONFIG.get(platform_code)

    def _is_duplicate_topic(self, topic: Dict[str, Any]) -> Tuple[bool, Optional[int]]:
        """判断话题是否重复（逻辑不变）"""
        existing_by_hash = self.db.get_hot_topic_by_hash(topic['hash_id'])
        if existing_by_hash:
            last_seen = safe_parse_datetime(existing_by_hash['last_seen_at'])
            if last_seen and (datetime.now() - last_seen < timedelta(minutes=self.deduplication_config['time_window_minutes'])):
                return True, existing_by_hash['id']
        
        time_threshold = datetime.now() - timedelta(minutes=self.deduplication_config['time_window_minutes'])
        similar_topics = self.db.execute_query("""
            SELECT id, title FROM hot_topics 
            WHERE platform_id = (SELECT id FROM platforms WHERE code = %s)
            AND last_seen_at >= %s
            AND is_active = TRUE
        """, (topic['platform'], time_threshold))
        
        for existing in similar_topics:
            similarity = self._title_similarity(topic['title'], existing['title'])
            if similarity >= self.deduplication_config['title_similarity_threshold']:
                return True, existing['id']
                
        return False, None

    def _title_similarity(self, title1: str, title2: str) -> float:
        """计算标题相似度（逻辑不变）"""
        words1 = set(re.findall(r'\w+', title1.lower()))
        words2 = set(re.findall(r'\w+', title2.lower()))
        if not words1 or not words2:
            return 0.0
        return len(words1 & words2) / len(words1 | words2)

    def fetch_api_data(self, platform_code: str, category: str, extra_params: Optional[Dict] = None, max_retries: int = 2) -> Optional[Dict]:
        """
        获取API数据（新增category参数，用于标记分类）
        :param category: 当前爬取的分类（如'ent'/'search'/'news'）
        """
        config = self.get_platform_config(platform_code)
        if not config:
            logger.error(f"平台 {platform_code} 无配置，跳过")
            return None

        # 合并参数：默认参数 + 分类参数 + 动态参数 + 时间戳
        params = config['default_params'].copy()
        # 核心：用category覆盖分类参数（如sub_tab=category）
        # 假设所有分类通过'sub_tab'参数区分，若平台参数不同可在config中配置映射
        params['sub_tab'] = category  
        if extra_params:
            params.update(extra_params)
        params['t'] = int(time.time() * 1000)

        retries = 0
        while retries <= max_retries:
            try:
                self.update_headers()
                response = self.session.get(config['base_url'], params=params, timeout=10)
                response.raise_for_status()
                
                # 调试文件增加分类标记
                timestamp = int(time.time())
                debug_file = f"debug/full_responses/api_{platform_code}_{category}_{timestamp}.txt"
                with open(debug_file, 'w', encoding='utf-8') as f:
                    f.write(f"URL: {response.url}\n{response.text}")
                
                return response.json()
            except (RequestException, json.JSONDecodeError) as e:
                logger.warning(f"平台 {platform_code} 分类 {category} 请求失败 ({retries+1}/{max_retries+1}): {e}")
                retries += 1
                time.sleep(1 * retries)
        return None

    def parse_api_data(self, api_data: Dict, platform_code: str, category: str) -> List[Dict]:
        """
        解析API数据（新增category参数，为话题添加分类标记）
        :param category: 当前爬取的分类（如'ent'/'search'/'news'）
        """
        config = self.get_platform_config(platform_code)
        if not config:
            return []

        topics = []
        current_data = api_data
        for key in config['data_path']:
            current_data = safe_get(current_data, key)
            if current_data is None:
                logger.warning(f"平台 {platform_code} 分类 {category} 未找到数据路径")
                return []

        items = parse_json_string(current_data) if config['list_type'] == 'string' else current_data
        if not isinstance(items, list):
            logger.warning(f"平台 {platform_code} 分类 {category} 数据格式错误")
            return []
        logger.info(f"平台 {platform_code} 分类 {category} 找到 {len(items)} 条原始数据")

        field_map = config['field_mapping']
        for idx, item in enumerate(items, 1):
            if not isinstance(item, dict):
                continue
            title = clean_text(safe_get(item, field_map['title'], ""))
            if not title:
                continue
            # 核心：添加category字段标记分类，hash_id包含分类（避免不同分类的相同标题被视为重复）
            topic = {
                "platform": platform_code,
                "category": category,  # 新增：分类标记
                "rank": idx,
                "timestamp": datetime.now().isoformat(),
                "title": title,
                "heat_value": self.extract_heat_value(safe_get(item, field_map['heat'], "")),
                "url": f"https://rebang.today/item/{safe_get(item, field_map['url'], '')}" if safe_get(item, field_map['url'], '') else "",
                "tags": process_tags(clean_text(safe_get(item, field_map['tag'], ""))),
                # hash_id包含分类，确保不同分类的相同标题不被判定为重复
                "hash_id": generate_hash(f"{title}_{platform_code}_{category}")
            }
            topics.append(topic)

        logger.info(f"平台 {platform_code} 分类 {category} 解析出 {len(topics)} 个有效话题")
        return topics

    def extract_heat_value(self, heat_str: Any) -> Optional[int]:
        """提取热度值（逻辑不变）"""
        if isinstance(heat_str, int):
            return heat_str
        if not heat_str or not isinstance(heat_str, str):
            return None
        match = re.search(r'(\d+\.?\d*)\s*([w万亿]?)', heat_str)
        if not match:
            return None
        value = float(match.group(1))
        unit = match.group(2)
        if unit in ('万', 'w'):
            value *= 10000
        elif unit == '亿':
            value *= 100000000
        return int(value)

    def save_topics(self, topics: List[Dict]) -> Dict[str, int]:
        """保存话题（逻辑不变）"""
        stats = {'total_count': len(topics), 'success_count': 0, 'error_count': 0, 'duplicate_count': 0}
        for topic in topics:
            try:
                is_duplicate, existing_id = self._is_duplicate_topic(topic)
                if is_duplicate and existing_id:
                    update_data = {
                        'rank': topic['rank'],
                        'heat_value': topic['heat_value'],
                        'last_seen_at': datetime.now().isoformat(),
                        'is_active': True
                    }
                    if 'tags' in topic and topic['tags']:
                        update_data['tags'] = process_tags(topic['tags'])
                    if self.db.update_hot_topic(existing_id, update_data):
                        stats['success_count'] += 1
                    stats['duplicate_count'] += 1
                else:
                    topic_data = {**topic,
                        'first_seen_at': datetime.now().isoformat(),
                        'last_seen_at': datetime.now().isoformat(),
                        'tags': process_tags(topic.get('tags', []))
                    }
                    if save_hot_topic(topic_data):
                        stats['success_count'] += 1
                    else:
                        stats['error_count'] += 1
            except Exception as e:
                logger.error(f"保存话题失败: {topic['title']}, 错误: {e}")
                stats['error_count'] += 1
        return stats
    def scrape_platform_category(self, platform_code: str, category: str, extra_params: Optional[Dict] = None) -> Tuple[List[Dict], Dict[str, int]]:
        """
        爬取单个平台的单个分类（新增方法，用于隔离单个分类的爬取逻辑）
        """
        logger.info(f"开始采集平台 {platform_code} 分类 {category}")
        if not self.db.connection or not self.db.connection.is_connected():
            self.db.connect()

        # 调用带分类参数的fetch和parse方法
        api_data = self.fetch_api_data(platform_code, category, extra_params=extra_params)
        topics = self.parse_api_data(api_data, platform_code, category) if api_data else []

        if topics:
            # 去重和标记失效时，需同时考虑平台和分类（避免影响其他分类）
            current_hashes = [t['hash_id'] for t in topics]
            mark_inactive_topics(platform_code, current_hashes, category=category)  # 需修改该方法支持category
            save_stats = self.save_topics(topics)
        else:
            save_stats = {'total_count': 0, 'success_count': 0, 'error_count': 0, 'duplicate_count': 0}

        return topics, {
            'total_count': len(topics),
            'success_count': save_stats['success_count'],
            'error_count': save_stats['error_count'],
            'duplicate_count': save_stats['duplicate_count']
        }

    def scrape_platform(self, platform_code: str, categories: List[str], extra_params: Optional[Dict] = None) -> Dict[str, Dict]:
        """
        爬取单个平台的多个分类（修改原方法，支持分类列表）
        :param categories: 分类列表，如['ent', 'search', 'news']
        """
        category_results = {}
        for category in categories:
            try:
                start_time = datetime.now()
                topics, stats = self.scrape_platform_category(platform_code, category, extra_params=extra_params)
                end_time = datetime.now()

                status = 'success' if stats['success_count'] == stats['total_count'] else \
                        'partial' if stats['success_count'] > 0 else 'failed'

                # 按分类保存日志
                save_collection_log(
                    platform=platform_code,
                    category=category,  # 日志增加分类
                    status=status,
                    stats=stats,
                    start_time=start_time.isoformat(),
                    end_time=end_time.isoformat()
                )

                category_results[category] = {
                    'status': status,
                    'stats': stats,
                    'duration': (end_time - start_time).total_seconds()
                }
                logger.info(f"平台 {platform_code} 分类 {category} 完成: 成功 {stats['success_count']} 条")
                time.sleep(random.uniform(1, 3))  # 分类间加延迟，反爬
            except Exception as e:
                logger.error(f"平台 {platform_code} 分类 {category} 异常: {e}")
                category_results[category] = {'status': 'error', 'error': str(e)}
        return category_results

    def scrape_all_platforms(self, platform_categories: Dict[str, List[str]], platform_extra_params: Optional[Dict[str, Dict]] = None) -> Dict[str, Dict]:
        """
        爬取所有平台的多个分类（修改原方法，支持平台-分类映射）
        :param platform_categories: 平台-分类列表的映射，如{'weibo': ['ent', 'search', 'news']}
        """
        results = {}
        platform_extra_params = platform_extra_params or {}
        if not self.db.connection or not self.db.connection.is_connected():
            self.db.connect()

        enabled_platforms = self.db.get_enabled_platforms()
        enabled_codes = {p['code'] for p in enabled_platforms}
        
        for platform_code, categories in platform_categories.items():
            if platform_code not in enabled_codes:
                logger.info(f"平台 {platform_code} 已禁用，跳过所有分类")
                continue
                
            try:
                # 为平台的所有分类执行爬取
                extra_params = platform_extra_params.get(platform_code, {})
                platform_result = self.scrape_platform(platform_code, categories, extra_params=extra_params)
                results[platform_code] = platform_result
            except Exception as e:
                logger.error(f"平台 {platform_code} 整体异常: {e}")
                results[platform_code] = {'status': 'error', 'error': str(e)}
                
        return results


# 单例和调度逻辑（不变）
_scraper_instance = None

def get_scraper() -> RebangScraper:
    global _scraper_instance
    if not _scraper_instance:
        _scraper_instance = RebangScraper()
    return _scraper_instance

def run_scheduled_scraping(platform_categories: Dict[str, List[str]], 
                        platform_extra_params: Optional[Dict[str, Dict]] = None):
    logger.info("开始定时采集所有平台")
    scraper = get_scraper()
    # 传入platform_categories参数
    results = scraper.scrape_all_platforms(
        platform_categories=platform_categories,
        platform_extra_params=platform_extra_params
    )
    total_success = 0
    for platform_results in results.values():
        if isinstance(platform_results, dict):
            for category_result in platform_results.values():
                if 'stats' in category_result:
                    total_success += category_result['stats']['success_count']
    logger.info(f"定时采集完成，总成功数: {total_success}")
    return results


# 示例调用
if __name__ == "__main__":
    print(f"热榜今日爬虫 - 开始采集 ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
    db = get_db_manager()
    if not db.connect():
        print("数据库连接失败")
        exit(1)
    try:
        # 1. 定义需要爬取的平台和分类
        platform_categories = {
            'weibo': ['ent', 'search', 'news'],  # 微博需要爬取的分类
            'zhihu': ['hot'],  # 知乎需要爬取的分类
            'douyin': ['hot'],
            'toutiao': ['hot'],
            'baidu': ['realtime'],
            'bilibili': ['popular'],
            'xiaohongshu': ['hot-search'],
            'xueqiu': ['topic']
        }
        
        # 2. 定义平台的额外参数（可选）
        custom_params = {
            'weibo': {'version': '2'},  # 微博的额外参数
            'zhihu': {'page': '1'},  # 知乎的额外参数
            'douyin': {'page': '1'},
            'toutiao': {'page': '1'},
            'baidu': {'page': '1'},
            'bilibili': {'page': '1'},
            'xiaohongshu': {'page': '1'},
            'xueqiu': {'page': '1'}
        }
        
        # 3. 执行爬取，传入两个参数
        results = run_scheduled_scraping(
            platform_categories=platform_categories,
            platform_extra_params=custom_params
        )
        
        # 4. 打印结果
        print("\n采集结果:")
        for platform, category_results in results.items():
            print(f"\n平台 {platform}:")
            for category, res in category_results.items():
                if 'stats' in res:
                    print(f"  分类 {category}: {res['status']}, "
                          f"成功保存: {res['stats']['success_count']}, "
                          f"重复: {res['stats']['duplicate_count']}, "
                          f"错误: {res['stats']['error_count']}")
                else:
                    print(f"  分类 {category}: {res['status']}, 错误: {res['error']}")
    finally:
        db.disconnect()