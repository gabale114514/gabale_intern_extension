"""
工具函数模块 - 数据处理和清洗
"""

import re
import hashlib
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
from config import TAG_PATTERNS, CATEGORY_KEYWORDS, PROCESSING_CONFIG

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
    from config import PLATFORM_CONFIG
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
    from config import PLATFORM_CONFIG
    return PLATFORM_CONFIG.get(platform, {}).get('icon', '📱')

def get_platform_name(platform: str) -> str:
    """
    获取平台名称
    """
    from config import PLATFORM_CONFIG
    return PLATFORM_CONFIG.get(platform, {}).get('name', platform)
