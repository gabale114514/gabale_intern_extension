import logging
import requests
from requests.exceptions import RequestException
import time
import json
import re
import random
from datetime import datetime
from urllib.parse import urljoin, urlparse, parse_qs
from typing import List, Dict, Any, Optional, Tuple
import os

from config import PLATFORM_CONFIG
from utils import clean_text, generate_hash
from database_manager import save_hot_topic, get_db_manager
from bs4 import BeautifulSoup
import requests
os.makedirs('debug/full_responses', exist_ok=True)

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('hot_topic_tool.log', encoding='utf-8'),
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

# 平台配置：按平台定制API路径、解析规则（核心重构点）
PLATFORM_CONFIG_DETAILED = {
    'weibo': {
        'api_url': 'https://api.rebang.today/v1/items?tab=weibo&sub_tab=search&version=2',
        'data_path': ['data', 'list'],  # 正确路径（已修正）
        'list_type': 'string',  # 关键修复：list是JSON字符串，需解码
        'field_mapping': {  # 关键修复：字段映射完全匹配实际响应
            'title': 'title',  # 标题字段正确
            'heat': 'heat_num',  # 热度字段是heat_num（数值型）
            'url': 'www_url',  # 链接字段是www_url（完整URL）
            'tag': 'label_name'  # 标签字段是label_name（如“新”“热”）
        }
    },
    'zhihu': {
        'api_url': 'https://api.rebang.today/v1/items?tab=zhihu&date_type=now&page=1&version=1',
        'data_path': ['data', 'list'],  # 正确路径：data.list
        'list_type': 'string',  # 关键修复：list是JSON字符串，需解码
        'field_mapping': {  # 关键修复：字段映射完全匹配实际响应
            'title': 'title',  # 标题字段正确
            'heat': 'heat_str',  # 热度字段是heat_str（带单位字符串）
            'url': 'www_url',  # 链接字段是www_url（完整URL）
            'tag': 'label_str'  # 标签字段是label_str（如“新”）
        }
    },
    'douyin': {  # 基于用户提供的示例配置
        'api_url': 'https://api.rebang.today/v1/items?tab=douyin&date_type=now&page=1&version=1',
        'data_path': ['data', 'list'],  # 数据在response.data.list
        'list_type': 'string',  # list是JSON字符串，需解码
        'field_mapping': {
            'title': 'title',
            'heat': 'heat_str',
            'url': 'aweme_id',  # 抖音用aweme_id作为视频ID
            'tag': 'describe'  # 用describe作为辅助标签
        }
    },
    'toutiao': {
        'api_url': 'https://api.rebang.today/v1/items?tab=toutiao&date_type=now&page=1&version=1',
        'data_path': ['data', 'list'],  # 正确路径：data.list
        'list_type': 'string',  # 关键修复：list是JSON字符串，需解码
        'field_mapping': {  # 关键修复：字段映射完全匹配实际响应
            'title': 'title',  # 标题字段正确
            'heat': 'hot_value',  # 热度字段是hot_value（数值型字符串）
            'url': 'www_url',  # 链接字段是www_url（完整URL）
            'tag': 'label'  # 标签字段是label（如“new”“hot”）
        }
    },
    # 其他平台配置类似，根据实际响应补充
    'baidu': {
        'api_url': 'https://api.rebang.today/v1/items?tab=baidu-tieba&sub_tab=topic&page=1&version=1',
        'data_path': ['data', 'list'],  # 正确路径：data.list
        'list_type': 'string',  # 关键修复：list是JSON字符串，需解码
        'field_mapping': {  # 关键修复：字段映射完全匹配实际响应
            'title': 'name',  # 标题字段是name（而非title）
            'heat': 'discuss_num',  # 热度字段是discuss_num（讨论数）
            'url': 'id',  # 链接可基于id构建（如https://tieba.baidu.com/topic/{id}）
            'tag': 'topic_tag'  # 标签标识是topic_tag（数值型）
        }
    },
    'bilibili': {
        'api_url': 'https://api.rebang.today/v1/items?tab=bilibili&sub_tab=popular&date_type=now&page=1&version=1',
        'data_path': ['data', 'list'],  # 正确路径：data.list
        'list_type': 'string',  # 关键修复：list是JSON字符串，需解码
        'field_mapping': {  # 关键修复：字段映射完全匹配实际响应
            'title': 'title',  # 标题字段正确
            'heat': 'view',  # 热度字段是view（播放量）
            'url': 'bvid',  # 链接标识是bvid（需构建完整URL）
            'tag': 'owner_name'  # 标签可用发布者名称（或留空）
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
        'data_path': ['data', 'list'],  # 关键修复：数据路径为data.list（原data.items错误）
        'list_type': 'string',  # 关键修复：list是JSON字符串，需解码
        'field_mapping': {  # 关键修复：字段映射完全匹配实际响应
            'title': 'title',  # 标题字段正确
            'heat': 'reason',  # 热度字段是reason（含阅读量）
            'url': 'www_url',  # 链接字段是www_url（完整URL）
            'tag': 'desc'  # 标签用描述字段（可选）
        }
    }
}


def safe_get(data, key, default=None):
    """安全获取数据（支持嵌套字典/列表）"""
    if isinstance(data, dict):
        return data.get(key, default)
    elif isinstance(data, list) and isinstance(key, int) and 0 <= key < len(data):
        return data[key]
    return default


def parse_json_string(s: str) -> Optional[List[Dict]]:
    """将JSON字符串解析为数组（处理可能的格式错误）"""
    try:
        return json.loads(s)
    except json.JSONDecodeError as e:
        logger.warning(f"JSON字符串解析失败: {e}, 原始字符串: {s[:100]}")
        return None


class RebangScraper:
    def __init__(self):
        self.session = requests.Session()
        self.base_url = "https://rebang.today"
        self.update_headers()
        self.platform_valid_api = {}  # 存储验证过的API

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
        """根据平台配置解析API数据（核心重构点）"""
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
                "timestamp": datetime.now().isoformat(),
            }
            # 标题（必须字段，缺失则跳过）
            title = clean_text(safe_get(item, field_map['title'], ""))
            if not title:
                continue
            topic['title'] = title
            # 热度（处理heat_str中的数字+单位）
            heat_str = safe_get(item, field_map['heat'], "")
            topic['heat'] = self.extract_heat_value(heat_str)
            # 链接（拼接完整URL）
            url_id = safe_get(item, field_map['url'], "")
            if url_id:
                # 不同平台链接格式不同，这里简化处理
                topic['url'] = f"https://rebang.today/item/{url_id}" if url_id else ""
            # 标签
            topic['tag'] = clean_text(safe_get(item, field_map['tag'], ""))
            # 生成唯一ID
            topic['hash_id'] = generate_hash(f"{title}_{platform_code}_{idx}")
            topics.append(topic)

        logger.info(f"平台 {platform_code} 解析出 {len(topics)} 个有效话题")
        return topics

    def extract_heat_value(self, heat_str: Any) -> Optional[int]:
        """适配数值型热度（如微博heat_num）和字符串型热度"""
        if isinstance(heat_str, int):
            return heat_str  # 微博直接返回整数，无需处理
        if not heat_str or not isinstance(heat_str, str):
            return None
        # 原字符串型热度解析逻辑（保留，适配其他平台）
        match = re.search(r'(\d+\.?\d*)\s*([万亿]?)', heat_str)
        if not match:
            return None
        value = float(match.group(1))
        unit = match.group(2)
        if unit == '万':
            value *= 10000
        elif unit == '亿':
            value *= 100000000
        return int(value)

    def scrape_platform_via_web(self, platform_code: str) -> List[Dict]:
        """优化网页解析（作为API备份）"""
        config = self.get_platform_config(platform_code)
        if not config:
            return []
        tab = platform_code  # 简化tab映射
        url = f"{self.base_url}/?tab={tab}"
        try:
            html = self.fetch_page(url)
            if not html:
                return []
            # 尝试解析网页中的JSON数据（现代网站常用）
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')
            # 查找内嵌JSON（如<script id="__NEXT_DATA__">）
            script = soup.find('script', id='__NEXT_DATA__')
            if script:
                try:
                    web_json = json.loads(script.text)
                    # 网页数据路径可能与API不同，简化处理
                    web_items = safe_get(web_json, ['props', 'pageProps', 'data', 'list'])
                    if isinstance(web_items, list):
                        return self._parse_web_items(web_items, platform_code)
                except json.JSONDecodeError as e:
                    logger.warning(f"平台 {platform_code} 网页JSON解析失败: {e}")
            # 传统HTML解析（按平台定制选择器）
            return self._parse_web_html(soup, platform_code)
        except Exception as e:
            logger.error(f"平台 {platform_code} 网页解析失败: {e}")
            return []

    def _parse_web_items(self, items: List[Dict], platform_code: str) -> List[Dict]:
        """解析网页中的JSON数据项"""
        topics = []
        for idx, item in enumerate(items, 1):
            title = clean_text(safe_get(item, 'title', ""))
            if not title:
                continue
            topics.append({
                "platform": platform_code,
                "title": title,
                "rank": idx,
                "heat": self.extract_heat_value(safe_get(item, 'heat_str', "")),
                "timestamp": datetime.now().isoformat(),
                "hash_id": generate_hash(f"{title}_{platform_code}_{idx}")
            })
        return topics

    def _parse_web_html(self, soup: BeautifulSoup, platform_code: str) -> List[Dict]:
        """解析网页HTML标签（按平台定制选择器）"""
        # 不同平台网页结构不同，这里以抖音为例
        selectors = {
            'douyin': '.hot-item',
            'weibo': '.weibo-item',
            'zhihu': '.zhihu-topic'
        }
        selector = selectors.get(platform_code, '.hot-item')
        items = soup.select(selector)
        topics = []
        for idx, item in enumerate(items, 1):
            title_elem = item.select_one('.title')
            if not title_elem:
                continue
            title = clean_text(title_elem.text)
            heat_elem = item.select_one('.heat')
            heat_str = heat_elem.text if heat_elem else ""
            topics.append({
                "platform": platform_code,
                "title": title,
                "rank": idx,
                "heat": self.extract_heat_value(heat_str),
                "hash_id": generate_hash(f"{title}_{platform_code}_{idx}")
            })
        return topics

    def fetch_page(self, url: str, max_retries: int = 3) -> Optional[str]:
        """获取网页内容"""
        retries = 0
        while retries < max_retries:
            try:
                self.update_headers()
                response = self.session.get(url, timeout=10)
                response.raise_for_status()
                return response.text
            except RequestException as e:
                logger.warning(f"网页 {url} 获取失败 ({retries+1}/{max_retries}): {e}")
                retries += 1
                time.sleep(2 * retries)
        return None

    def scrape_platform(self, platform_code: str) -> Tuple[List[Dict], Dict[str, int]]:
        """采集单个平台（优先API，失败则网页解析）"""
        logger.info(f"开始采集平台 {platform_code}")
        # 1. API采集
        api_data = self.fetch_api_data(platform_code)
        topics = self.parse_api_data(api_data, platform_code) if api_data else []
        # 2. 若API失败，尝试网页解析
        if not topics:
            logger.info(f"平台 {platform_code} API解析失败，尝试网页解析")
            topics = self.scrape_platform_via_web(platform_code)
        # 统计
        stats = {
            'total_count': len(topics),
            'success_count': len(topics),
            'error_count': 0
        }
        return topics, stats

    def save_topics(self, topics: List[Dict]) -> Dict[str, int]:
        """保存话题到数据库（保持原逻辑，增加错误日志）"""
        stats = {'total_count': len(topics), 'success_count': 0, 'error_count': 0, 'duplicate_count': 0}
        for topic in topics:
            try:
                result = save_hot_topic(topic)
                if result:
                    stats['success_count'] += 1
                else:
                    stats['duplicate_count'] += 1
            except Exception as e:
                logger.error(f"保存话题失败: {topic['title']}, 错误: {e}")
                stats['error_count'] += 1
        return stats

    def scrape_all_platforms(self) -> Dict[str, Dict]:
        """采集所有平台"""
        results = {}
        for platform_code in PLATFORM_CONFIG_DETAILED.keys():
            if not PLATFORM_CONFIG.get(platform_code, {}).get('enabled', True):
                logger.info(f"平台 {platform_code} 已禁用，跳过")
                continue
            try:
                start_time = datetime.now()
                topics, scrape_stats = self.scrape_platform(platform_code)
                save_stats = self.save_topics(topics)
                end_time = datetime.now()
                results[platform_code] = {
                    'status': 'success' if save_stats['success_count'] > 0 else 'failed',
                    'stats': save_stats,
                    'duration': (end_time - start_time).total_seconds()
                }
                logger.info(f"平台 {platform_code} 完成: 成功保存 {save_stats['success_count']} 条")
                time.sleep(random.uniform(2, 5))  # 反爬延迟
            except Exception as e:
                logger.error(f"平台 {platform_code} 采集异常: {e}")
                results[platform_code] = {'status': 'error', 'error': str(e)}
        return results


# 单例与入口
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
            print(f"- {platform}: {res['status']}, 成功保存: {res['stats']['success_count'] if 'stats' in res else 0}")
    finally:
        db.disconnect()