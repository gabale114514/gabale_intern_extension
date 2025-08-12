"""
热搜话题处理工具接口
"""

import logging
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
import hashlib

from config.platform_config import TOOL_CONFIG, PROCESSING_CONFIG
from main.scraper.utils import (
    clean_text, extract_tags, generate_hash, categorize_topic,
    validate_platform, validate_rank, validate_heat_value,
    is_duplicate_topic, get_platform_icon, get_platform_name
)

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

@dataclass
class HotTopicItem:
    """热搜话题数据模型"""
    platform: str
    title: str
    rank: int
    tags: List[str] = None
    url: Optional[str] = None
    heat_value: Optional[int] = None
    category: Optional[str] = None
    created_at: Optional[datetime] = None
    hash_id: Optional[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.hash_id is None:
            self.hash_id = self._generate_hash()
    
    def _generate_hash(self) -> str:
        """生成用于去重的哈希值"""
        content = f"{self.platform}_{self.title}_{self.rank}"
        return hashlib.md5(content.encode('utf-8')).hexdigest()

class HotTopicProcessor:
    """热搜话题处理器"""
    
    def __init__(self):
        self.processed_items = []
        self.duplicate_count = 0
        self.error_count = 0
        
    def process_single_topic(self, raw_data: Dict[str, Any]) -> Optional[HotTopicItem]:
        """
        处理单个热搜话题
        
        Args:
            raw_data: 原始数据字典
            
        Returns:
            处理后的HotTopicItem对象，如果处理失败返回None
        """
        try:
            # 验证必需字段
            if not self._validate_required_fields(raw_data):
                logger.error(f"必需字段验证失败: {raw_data}")
                self.error_count += 1
                return None
            
            # 清理和验证数据
            platform = raw_data['platform']
            title = clean_text(raw_data['title'])
            rank = raw_data['rank']
            
            # 验证平台
            if not validate_platform(platform):
                logger.error(f"无效的平台: {platform}")
                self.error_count += 1
                return None
            
            # 验证排名
            if not validate_rank(rank):
                logger.error(f"无效的排名: {rank}")
                self.error_count += 1
                return None
            
            # 验证热度值
            heat_value = raw_data.get('heat_value')
            if not validate_heat_value(heat_value):
                logger.error(f"无效的热度值: {heat_value}")
                self.error_count += 1
                return None
            
            # 提取标签
            tags = extract_tags(title)
            
            # 自动分类
            category = categorize_topic(title)
            
            # 创建HotTopicItem对象
            item = HotTopicItem(
                platform=platform,
                title=title,
                rank=rank,
                tags=tags,
                url=raw_data.get('url'),
                heat_value=heat_value,
                category=category
            )
            
            # 检查重复
            if self._is_duplicate_with_existing(item):
                self.duplicate_count += 1
                return None
            
            # 添加到已处理列表
            self.processed_items.append(item)
            
            logger.info(f"成功处理话题: {title} (平台: {platform}, 排名: {rank})")
            return item
            
        except Exception as e:
            logger.error(f"处理话题时发生错误: {e}, 数据: {raw_data}")
            self.error_count += 1
            return None
    
    def process_batch_topics(self, raw_data_list: List[Dict[str, Any]]) -> List[HotTopicItem]:
        """
        批量处理热搜话题
        
        Args:
            raw_data_list: 原始数据列表
            
        Returns:
            处理后的HotTopicItem对象列表
        """
        logger.info(f"开始批量处理 {len(raw_data_list)} 条数据")
        
        processed_items = []
        for raw_data in raw_data_list:
            item = self.process_single_topic(raw_data)
            if item:
                processed_items.append(item)
        
        logger.info(f"批量处理完成: 成功 {len(processed_items)} 条, "
                   f"重复 {self.duplicate_count} 条, 错误 {self.error_count} 条")
        
        return processed_items
    
    def _validate_required_fields(self, data: Dict[str, Any]) -> bool:
        """验证必需字段"""
        required_fields = ['platform', 'title', 'rank']
        return all(field in data and data[field] for field in required_fields)
    
    def _is_duplicate_with_existing(self, new_item: HotTopicItem) -> bool:
        """检查是否与已处理的项目重复"""
        for existing_item in self.processed_items:
            if is_duplicate_topic(
                {'title': new_item.title, 'platform': new_item.platform},
                {'title': existing_item.title, 'platform': existing_item.platform}
            ):
                return True
        return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取处理统计信息"""
        return {
            'total_processed': len(self.processed_items),
            'duplicate_count': self.duplicate_count,
            'error_count': self.error_count,
            'success_rate': len(self.processed_items) / (len(self.processed_items) + self.error_count) * 100 if (len(self.processed_items) + self.error_count) > 0 else 0
        }
    
    def export_to_dict(self) -> List[Dict[str, Any]]:
        """导出为字典格式"""
        result = []
        for item in self.processed_items:
            item_dict = asdict(item)
            # 处理datetime序列化
            if item_dict['created_at']:
                item_dict['created_at'] = item_dict['created_at'].isoformat()
            result.append(item_dict)
        return result
    
    def export_to_json(self, filepath: str = None) -> str:
        """导出为JSON格式"""
        data = self.export_to_dict()
        json_str = json.dumps(data, ensure_ascii=False, indent=2, default=str)
        
        if filepath:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(json_str)
            logger.info(f"数据已导出到: {filepath}")
        
        return json_str

# 工具接口函数
def process_hot_topic(raw_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    处理单个热搜话题的工具接口
    
    Args:
        raw_data: 原始数据字典
        
    Returns:
        处理后的数据字典，如果处理失败返回None
    """
    processor = HotTopicProcessor()
    item = processor.process_single_topic(raw_data)
    if item:
        item_dict = asdict(item)
        # 处理datetime序列化
        if item_dict['created_at']:
            item_dict['created_at'] = item_dict['created_at'].isoformat()
        return item_dict
    return None

def process_hot_topics_batch(raw_data_list: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    批量处理热搜话题的工具接口
    
    Args:
        raw_data_list: 原始数据列表
        
    Returns:
        包含处理结果和统计信息的字典
    """
    processor = HotTopicProcessor()
    processed_items = processor.process_batch_topics(raw_data_list)
    
    return {
        'success': True,
        'data': processor.export_to_dict(),
        'statistics': processor.get_statistics(),
        'timestamp': datetime.now().isoformat()
    }

def get_tool_info() -> Dict[str, Any]:
    """
    获取工具信息
    
    Returns:
        工具信息字典
    """
    return {
        **TOOL_CONFIG,
        'supported_platforms': list(PROCESSING_CONFIG.keys()),
        'features': {
            'auto_categorize': PROCESSING_CONFIG['enable_auto_categorize'],
            'duplicate_check': PROCESSING_CONFIG['enable_duplicate_check'],
            'max_title_length': PROCESSING_CONFIG['max_title_length'],
            'max_tags_count': PROCESSING_CONFIG['max_tags_count']
        }
    }

# 示例使用
if __name__ == "__main__":
    # 示例数据
    sample_data = [
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
        }
    ]
    
    # 测试批量处理
    result = process_hot_topics_batch(sample_data)
    print(json.dumps(result, ensure_ascii=False, indent=2))
