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
        },
        'pagination': {
            'param_name': 'page',  # 分页参数名
            'start_page': 1,       # 起始页码
            'max_pages': 1,       # 最大爬取页数
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
        },
        'pagination': {
            'param_name': 'page',  # 分页参数名
            'start_page': 1,       # 起始页码
            'max_pages': 1,       # 最大爬取页数
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
        },
        'pagination': {
            'param_name': 'page',  # 分页参数名
            'start_page': 1,       # 起始页码
            'max_pages': 1,       # 最大爬取页数
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
        },
        'pagination': {
            'param_name': 'page',  # 分页参数名
            'start_page': 1,       # 起始页码
            'max_pages': 1,       # 最大爬取页数
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
    },
    'pagination': {
            'param_name': 'page',  # 分页参数名
            'start_page': 1,       # 起始页码
            'max_pages': 1,       # 最大爬取页数
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
        },
        'pagination': {
            'param_name': 'page',  # 分页参数名
            'start_page': 1,       # 起始页码
            'max_pages': 10,       # 最大爬取页数
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
        },
        'pagination': {
            'param_name': 'page',  # 分页参数名
            'start_page': 1,       # 起始页码
            'max_pages': 1,       # 最大爬取页数
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
        },
        'pagination': {
            'param_name': 'page',  # 分页参数名
            'start_page': 1,       # 起始页码
            'max_pages': 1,       # 最大爬取页数
        }
    }
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

# 1. 定义需要爬取的平台和分类
platform_categories = {
    'weibo': ['ent', 'search', 'news'],
    'zhihu': ['hot'],
    'douyin': ['hot'],
    'toutiao': ['hot'],
    'baidu': ['realtime','phrase','novel','movie','teleplay','car','game'],
    'bilibili': ['popular','weekly','rank'],
    'xiaohongshu': ['hot-search'],
    'xueqiu': ['topic','news','notice']
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