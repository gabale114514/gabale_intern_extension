"""
工具函数模块 - 数据处理和清洗
"""

import re
import hashlib
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
from config.platform_config import TAG_PATTERNS, CATEGORY_KEYWORDS, PROCESSING_CONFIG

logger = logging.getLogger(__name__)

def clean_text(text: Any) -> str:
    """
    清理文本内容（增强版）
    功能：
    1. 支持处理字符串、数值和None类型输入
    2. 移除多余空白和特殊字符
    3. 自动进行类型转换和长度限制
    
    参数：
    text: 可以是str/int/float/None等类型
    
    返回：
    处理后的字符串
    """
    # 处理空值和类型转换
    if text is None:
        return ""
    
    # 数值类型处理
    if isinstance(text, (int, float)):
        text = str(text)
    
    # 确保现在是字符串类型
    if not isinstance(text, str):
        return ""
    
    # 原始清理逻辑
    text = text.strip()
    text = re.sub(r'\s+', ' ', text)  # 合并连续空白
    text = re.sub(r'[^\w\s\u4e00-\u9fff\-\.\,\!\?\(\)\[\]【】]', '', text)  # 过滤特殊字符
    
    # 长度限制
    max_length = PROCESSING_CONFIG.get('max_title_length', 255)  # 默认值防止KeyError
    if len(text) > max_length:
        text = text[:max_length] + "..."
    
    return text

def extract_tags(text: str) -> List[str]:
    """
    从文本中提取标签
    """
    tags = []
    for tag_name, pattern in TAG_PATTERNS.items():
        if re.search(pattern, text, re.IGNORECASE):
            tags.append(tag_name)
    
    # 限制标签数量
    max_tags = PROCESSING_CONFIG['max_tags_count']
    return tags[:max_tags]

def generate_hash(content: str) -> str:
    """
    生成内容哈希值
    """
    return hashlib.md5(content.encode('utf-8')).hexdigest()

def categorize_topic(title: str) -> str:
    """
    对话题进行分类
    """
    if not PROCESSING_CONFIG['enable_auto_categorize']:
        return '其他'
    
    for category, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in title:
                return category
    
    return '其他'

def calculate_similarity(text1: str, text2: str) -> float:
    """
    计算两个文本的相似度（简单的Jaccard相似度）
    """
    if not text1 or not text2:
        return 0.0
    
    # 分词（简单的按字符分割）
    set1 = set(text1)
    set2 = set(text2)
    
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    
    return intersection / union if union > 0 else 0.0

def is_duplicate_topic(topic1: Dict[str, Any], topic2: Dict[str, Any]) -> bool:
    """
    判断两个话题是否重复
    """
    if not PROCESSING_CONFIG['enable_duplicate_check']:
        return False
    
    title1 = topic1.get('title', '')
    title2 = topic2.get('title', '')
    
    if not title1 or not title2:
        return False
    
    similarity = calculate_similarity(title1, title2)
    threshold = PROCESSING_CONFIG['similarity_threshold']
    
    return similarity >= threshold

def validate_platform(platform: str) -> bool:
    """
    验证平台是否有效
    """
    from config.platform_config import PLATFORM_CONFIG
    return platform in PLATFORM_CONFIG and PLATFORM_CONFIG[platform]['enabled']

def validate_rank(rank: int) -> bool:
    """
    验证排名是否有效
    """
    return isinstance(rank, int) and 1 <= rank <= 1000

def validate_heat_value(heat_value: Optional[int]) -> bool:
    """
    验证热度值是否有效
    """
    if heat_value is None:
        return True
    return isinstance(heat_value, int) and heat_value >= 0

def format_datetime(dt: datetime) -> str:
    """
    格式化日期时间
    """
    return dt.strftime('%Y-%m-%d %H:%M:%S')

def safe_json_loads(data: str, default: Any = None) -> Any:
    """
    安全的JSON解析
    """
    try:
        return json.loads(data)
    except (json.JSONDecodeError, TypeError):
        logger.warning(f"JSON解析失败: {data}")
        return default

def get_platform_icon(platform: str) -> str:
    """
    获取平台图标
    """
    from config.platform_config import PLATFORM_CONFIG
    return PLATFORM_CONFIG.get(platform, {}).get('icon', '📱')

def get_platform_name(platform: str) -> str:
    """
    获取平台名称
    """
    from config.platform_config import PLATFORM_CONFIG
    return PLATFORM_CONFIG.get(platform, {}).get('name', platform)

def safe_parse_datetime(date_value: Any) -> Optional[datetime]:
    """
    安全地解析日期时间，支持字符串和datetime对象
    
    Args:
        date_value: 待解析的日期时间（可能是字符串或datetime对象）
        
    Returns:
        datetime对象或None（解析失败时）
    """
    # 如果已经是datetime对象，直接返回
    if isinstance(date_value, datetime):
        return date_value
        
    # 如果是字符串，尝试解析
    if isinstance(date_value, str):
        try:
            return datetime.fromisoformat(date_value)
        except ValueError:
            # 尝试其他常见格式
            for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S.%fZ', '%Y-%m-%d']:
                try:
                    return datetime.strptime(date_value, fmt)
                except ValueError:
                    continue
                    
        logger.warning(f"无法解析日期字符串: {date_value}")
        return None
        
    # 其他类型
    logger.warning(f"不支持的日期类型: {type(date_value)}")
    return None
def process_tags(tags, max_length=100):
    """
    处理标签列表，确保每个标签长度不超过max_length
    
    Args:
        tags: 标签列表或单个标签字符串
        max_length: 标签最大长度限制
        
    Returns:
        处理后的标签列表
    """
    # 确保输入是列表
    if not isinstance(tags, list):
        if not tags:  # 空值处理
            return []
        tags = [str(tags)]  # 转换为单元素列表
    
    processed = []
    for tag in tags:
        if isinstance(tag, str):
            # 截断过长标签
            if len(tag) > max_length:
                tag = tag[:max_length]
            if tag.strip():  # 只保留非空标签
                processed.append(tag.strip())
    return processed
def parse_json_string(s: str) -> Optional[List[Dict]]:
    """将JSON字符串解析为数组（处理可能的格式错误）"""
    try:
        return json.loads(s)
    except json.JSONDecodeError as e:
        logger.warning(f"JSON字符串解析失败: {e}, 原始字符串: {s[:100]}")
        return None
    
def safe_fromisoformat(date_str: Any) -> Optional[datetime]:
    """
    安全地将字符串转换为datetime对象
    
    Args:
        date_str: 待转换的日期字符串
        
    Returns:
        datetime对象或None（转换失败时）
    """
    if not isinstance(date_str, str):
        logger.warning(f"尝试将非字符串类型转换为datetime: {type(date_str)}")
        return None
        
    try:
        return datetime.fromisoformat(date_str)
    except ValueError:
        # 尝试处理其他常见格式
        for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S.%fZ', '%Y-%m-%d']:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
                
        logger.warning(f"无法解析日期字符串: {date_str}")
        return None
    
def safe_get(data, key, default=None):
    """安全获取数据（支持嵌套字典/列表）"""
    if isinstance(data, dict):
        return data.get(key, default)
    elif isinstance(data, list) and isinstance(key, int) and 0 <= key < len(data):
        return data[key]
    return default

    # def scrape_platform_via_web(self, platform_code: str) -> List[Dict]:
    #     """优化网页解析（作为API备份）"""
    #     config = self.get_platform_config(platform_code)
    #     if not config:
    #         return []
    #     tab = platform_code  # 简化tab映射
    #     url = f"{self.base_url}/?tab={tab}"
    #     try:
    #         html = self.fetch_page(url)
    #         if not html:
    #             return []
    #         # 尝试解析网页中的JSON数据（现代网站常用）
    #         soup = BeautifulSoup(html, 'html.parser')
    #         # 查找内嵌JSON（如<script id="__NEXT_DATA__">）
    #         script = soup.find('script', id='__NEXT_DATA__')
    #         if script:
    #             try:
    #                 web_json = json.loads(script.text)
    #                 web_items = safe_get(web_json, ['props', 'pageProps', 'data', 'list'])
    #                 if isinstance(web_items, list):
    #                     return self._parse_web_items(web_items, platform_code)
    #             except json.JSONDecodeError as e:
    #                 logger.warning(f"平台 {platform_code} 网页JSON解析失败: {e}")
    #         return self._parse_web_html(soup, platform_code)
    #     except Exception as e:
    #         logger.error(f"平台 {platform_code} 网页解析失败: {e}")
    #         return []

    # def _parse_web_items(self, items: List[Dict], platform_code: str) -> List[Dict]:
    #     """解析网页中的JSON数据项"""
    #     topics = []
    #     for idx, item in enumerate(items, 1):
    #         title = clean_text(safe_get(item, 'title', ""))
    #         if not title:
    #             continue
    #         topics.append({
    #             "platform": platform_code,
    #             "title": title,
    #             "rank": idx,
    #             "heat_value": self.extract_heat_value(safe_get(item, 'heat_str', "")),
    #             "timestamp": datetime.now().isoformat(),
    #             "hash_id": generate_hash(f"{title}_{platform_code}"),
    #             "tags": process_tags(clean_text(safe_get(item, 'tag', "")))  # 添加这行
    #         })
    #     return topics

    # def _parse_web_html(self, soup: BeautifulSoup, platform_code: str) -> List[Dict]:
    #     """解析网页HTML标签（按平台定制选择器）"""
    #     # 不同平台网页结构不同，这里以抖音为例
    #     selectors = {
    #         'douyin': '.hot-item',
    #         'weibo': '.weibo-item',
    #         'zhihu': '.zhihu-topic'
    #     }
    #     selector = selectors.get(platform_code, '.hot-item')
    #     items = soup.select(selector)
    #     topics = []
    #     for idx, item in enumerate(items, 1):
    #         title_elem = item.select_one('.title')
    #         if not title_elem:
    #             continue
    #         title = clean_text(title_elem.text)
    #         heat_elem = item.select_one('.heat')
    #         heat_str = heat_elem.text if heat_elem else ""
    #         topics.append({
    #             "platform": platform_code,
    #             "title": title,
    #             "rank": idx,
    #             "heat_value": self.extract_heat_value(heat_str),
    #             "hash_id": generate_hash(f"{title}_{platform_code}")
    #         })
    #     return topics

    # def fetch_page(self, url: str, max_retries: int = 3) -> Optional[str]:
    #     """获取网页内容"""
    #     retries = 0
    #     while retries < max_retries:
    #         try:
    #             self.update_headers()
    #             response = self.session.get(url, timeout=10)
    #             response.raise_for_status()
    #             return response.text
    #         except RequestException as e:
    #             logger.warning(f"网页 {url} 获取失败 ({retries+1}/{max_retries}): {e}")
    #             retries += 1
    #             time.sleep(2 * retries)
    #     return None