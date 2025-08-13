"""
工具接口配置文件
"""

import os
from typing import Dict, Any

# 工具接口配置
TOOL_CONFIG = {
    'name': '热搜话题处理工具',
    'version': '1.0.0',
    'description': '处理热搜话题数据并收录到数据库的工具接口'
}

# 数据处理配置
PROCESSING_CONFIG = {
    'max_title_length': 500,  # 标题最大长度
    'max_tags_count': 10,     # 标签最大数量
    'enable_auto_categorize': True,  # 启用自动分类
    'enable_duplicate_check': True,  # 启用重复检查
    'similarity_threshold': 0.8,     # 相似度阈值
}

# 标签配置
TAG_PATTERNS = {
    '热': r'热|🔥|hot|HOT',
    '新': r'新|new|NEW',
    '辟谣': r'辟谣|辟谣|辟谣',
    '沸': r'沸|boiling|BOILING',
    '爆': r'爆|explode|EXPLODE',
    '荐': r'荐|推荐|RECOMMEND',
    '置顶': r'置顶|置顶|PINNED'
}

# 分类配置
CATEGORY_KEYWORDS = {
    '娱乐': ['明星', '演员', '歌手', '电影', '电视剧', '综艺', '娱乐'],
    '科技': ['科技', 'AI', '人工智能', '互联网', '手机', '电脑', '软件'],
    '体育': ['体育', '足球', '篮球', '比赛', '运动员', '奥运会'],
    '财经': ['股票', '基金', '投资', '经济', '金融', '理财'],
    '社会': ['社会', '新闻', '事件', '事故', '案件'],
    '教育': ['教育', '学校', '考试', '学习', '培训'],
    '健康': ['健康', '医疗', '医院', '疾病', '养生'],
    '政治': ['政治', '政府', '政策', '官员', '会议']
}

# 日志配置
LOGGING_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'file': 'hot_topic_tool.log',
    'max_bytes': 10 * 1024 * 1024,  # 10MB
    'backup_count': 5
}
