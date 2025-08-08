# 热搜话题处理工具接口

一个用于处理热搜话题数据并收录到数据库的工具接口，支持微博、知乎、小红书、今日头条、百度、雪球、抖音、哔哩哔哩等8个平台。

## 功能特性

- 🧹 **数据清洗**: 自动清理和验证热搜话题数据
- 🏷️ **标签提取**: 智能提取话题标签（热、新、辟谣等）
- 📊 **自动分类**: 根据关键词自动分类话题
- 🔍 **重复检测**: 智能识别和过滤重复话题
- ✅ **数据验证**: 完整的字段验证和错误处理
- 📝 **批量处理**: 支持单个和批量话题处理
- 🔧 **可扩展**: 模块化设计，易于扩展新功能

## 系统架构

```
hot_topic_tool.py     # 核心工具接口
├── config.py         # 配置文件
├── utils.py          # 工具函数
├── test_tool.py      # 测试文件
├── requirements.txt  # 依赖包
└── README.md        # 项目说明
```

## 安装部署

### 1. 环境要求

- Python 3.10+
- Windows/Linux/macOS

### 2. 创建虚拟环境

```bash
# 使用Python 3.10创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows
venv\Scripts\activate
# Linux/macOS
source venv/bin/activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 测试工具

```bash
python test_tool.py
```

## 使用方法

### 1. 单个话题处理

```python
from hot_topic_tool import process_hot_topic

# 原始数据
raw_data = {
    'platform': 'weibo',
    'title': '这是一个热门话题🔥 新消息',
    'rank': 1,
    'heat_value': 10000,
    'url': 'https://example.com'
}

# 处理数据
result = process_hot_topic(raw_data)
if result:
    print("处理成功:", result)
else:
    print("处理失败")
```

### 2. 批量话题处理

```python
from hot_topic_tool import process_hot_topics_batch

# 原始数据列表
raw_data_list = [
    {
        'platform': 'weibo',
        'title': '热门话题1',
        'rank': 1,
        'heat_value': 10000
    },
    {
        'platform': 'zhihu',
        'title': '热门话题2',
        'rank': 2,
        'heat_value': 8000
    }
]

# 批量处理
result = process_hot_topics_batch(raw_data_list)
print("处理结果:", result)
```

### 3. 获取工具信息

```python
from hot_topic_tool import get_tool_info

info = get_tool_info()
print("工具信息:", info)
```

## 数据格式

### 输入数据格式

```json
{
    "platform": "weibo",           // 必需：平台标识
    "title": "话题标题",           // 必需：话题标题
    "rank": 1,                     // 必需：排名（1-1000）
    "heat_value": 10000,           // 可选：热度值
    "url": "https://example.com"   // 可选：话题链接
}
```

### 输出数据格式

```json
{
    "platform": "weibo",
    "title": "话题标题",
    "rank": 1,
    "tags": ["热", "新"],
    "url": "https://example.com",
    "heat_value": 10000,
    "category": "娱乐",
    "created_at": "2024-01-01T12:00:00",
    "hash_id": "abc123..."
}
```

## 配置说明

### 数据处理配置

```python
PROCESSING_CONFIG = {
    'max_title_length': 500,        # 标题最大长度
    'max_tags_count': 10,           # 标签最大数量
    'enable_auto_categorize': True, # 启用自动分类
    'enable_duplicate_check': True, # 启用重复检查
    'similarity_threshold': 0.8,    # 相似度阈值
}
```

### 平台配置

支持的平台：
- `weibo`: 微博 🐦
- `zhihu`: 知乎 📚
- `xiaohongshu`: 小红书 📖
- `toutiao`: 今日头条 📰
- `baidu`: 百度 🔍
- `xueqiu`: 雪球 📈
- `douyin`: 抖音 🎵
- `bilibili`: 哔哩哔哩 📺

### 标签配置

自动提取的标签：
- `热`: 热门话题
- `新`: 新话题
- `辟谣`: 辟谣话题
- `沸`: 沸腾话题
- `爆`: 爆炸话题
- `荐`: 推荐话题
- `置顶`: 置顶话题

### 分类配置

自动分类的类别：
- `娱乐`: 娱乐相关
- `科技`: 科技相关
- `体育`: 体育相关
- `财经`: 财经相关
- `社会`: 社会相关
- `教育`: 教育相关
- `健康`: 健康相关
- `政治`: 政治相关
- `其他`: 其他类别

## 工具函数

### 核心函数

- `clean_text(text)`: 清理文本内容
- `extract_tags(text)`: 提取标签
- `categorize_topic(title)`: 话题分类
- `validate_platform(platform)`: 验证平台
- `validate_rank(rank)`: 验证排名
- `validate_heat_value(heat_value)`: 验证热度值

### 工具接口

- `process_hot_topic(raw_data)`: 处理单个话题
- `process_hot_topics_batch(raw_data_list)`: 批量处理话题
- `get_tool_info()`: 获取工具信息

## 错误处理

工具会自动处理以下错误：

1. **字段验证错误**: 缺少必需字段或字段格式错误
2. **平台验证错误**: 不支持的平台
3. **数据格式错误**: 排名、热度值等格式错误
4. **重复数据**: 自动检测和过滤重复话题

## 扩展开发

### 添加新平台

在 `config.py` 中添加新平台配置：

```python
PLATFORM_CONFIG = {
    'new_platform': {
        'name': '新平台',
        'enabled': True,
        'icon': '🆕'
    }
}
```

### 添加新标签

在 `config.py` 中添加新标签规则：

```python
TAG_PATTERNS = {
    '新标签': r'新标签|new_tag|NEW_TAG'
}
```

### 添加新分类

在 `config.py` 中添加新分类关键词：

```python
CATEGORY_KEYWORDS = {
    '新分类': ['关键词1', '关键词2', '关键词3']
}
```

## 日志记录

工具会自动记录处理日志：

- 日志文件: `hot_topic_tool.log`
- 日志级别: INFO
- 记录内容: 处理状态、错误信息、统计信息

## 性能优化

- 文本处理优化
- 重复检测算法优化
- 内存使用优化
- 批量处理优化

## 测试

运行测试：

```bash
python test_tool.py
```

测试内容包括：
- 工具函数测试
- 单个话题处理测试
- 批量话题处理测试
- 错误处理测试
- 工具信息获取测试

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request！

## 联系方式

如有问题，请通过GitHub Issues联系。
