# 热榜今日(rebang.today)网站爬虫

## 概述

本模块提供了一个用于采集热榜今日(https://rebang.today)网站上各大平台热搜榜数据的爬虫框架。该网站聚合了微博、知乎、今日头条、百度、抖音、哔哩哔哩、小红书和雪球等平台的热搜榜数据。

## 文件说明

- `rebang_scraper.py`: 主爬虫模块，包含爬虫的核心实现
- `test_rebang_scraper.py`: 测试脚本，用于测试爬虫的各项功能

## 功能特点

1. **多平台支持**: 支持采集8个主流平台的热搜榜数据
2. **数据清洗**: 自动清洗和标准化采集到的数据
3. **去重处理**: 使用哈希ID避免重复数据
4. **分类标签**: 自动为热搜话题添加分类和标签
5. **数据存储**: 将采集到的数据保存到数据库
6. **错误处理**: 完善的错误处理和日志记录
7. **定时采集**: 支持定时采集功能

## 使用方法

### 采集单个平台

```python
from rebang_scraper import scrape_platform

# 采集今日头条热搜榜
result = scrape_platform('toutiao')

# 查看采集结果
print(f"采集状态: {result['status']}")
print(f"采集数量: {result['stats']['total_count']}")
print(f"成功数量: {result['stats']['success_count']}")
```

### 采集所有平台

```python
from rebang_scraper import scrape_all_platforms

# 采集所有平台热搜榜
results = scrape_all_platforms()

# 查看各平台采集结果
for platform, result in results.items():
    if 'stats' in result:
        print(f"{platform}: {result['status']}, 总数: {result['stats']['total_count']}")
```

### 运行测试脚本

```bash
python test_rebang_scraper.py
```

测试脚本会依次测试以下功能：
1. 页面获取
2. 热搜话题解析
3. 单平台采集
4. 所有平台采集（可选）

## 实现流程

1. **初始化**: 创建爬虫实例，设置请求头
2. **获取页面**: 发送HTTP请求获取页面内容
3. **解析内容**: 使用BeautifulSoup解析HTML内容
4. **提取数据**: 提取热搜话题的标题、排名、热度等信息
5. **数据处理**: 清洗数据，添加分类和标签
6. **保存数据**: 将处理后的数据保存到数据库
7. **记录日志**: 记录采集过程和结果

## 平台映射

rebang.today平台标识与系统内部平台代码的映射关系：

| rebang.today标识 | 系统内部代码 | 平台名称 |
|-----------------|------------|---------|
| weibo           | weibo      | 微博     |
| zhihu           | zhihu      | 知乎     |
| toutiao         | toutiao    | 今日头条  |
| baidu           | baidu      | 百度     |
| douyin          | douyin     | 抖音     |
| bilibili        | bilibili   | 哔哩哔哩  |
| xhs             | xiaohongshu| 小红书    |
| xueqiu          | xueqiu     | 雪球     |

## 自定义和扩展

### 添加新平台

如果rebang.today网站添加了新的平台，可以通过更新`PLATFORM_MAPPING`字典来支持：

```python
# 在rebang_scraper.py中添加新平台
PLATFORM_MAPPING['new_platform'] = 'new_platform_code'
REVERSE_PLATFORM_MAPPING = {v: k for k, v in PLATFORM_MAPPING.items()}
```

### 修改解析逻辑

如果网站结构发生变化，可以修改`parse_hot_topics`方法中的选择器：

```python
# 修改热搜项的选择器
hot_items = soup.select('.new-hot-list .new-item')
```

### 自定义数据处理

可以修改或扩展数据处理逻辑，例如添加新的标签提取规则：

```python
# 在utils.py中添加新的标签提取规则
TAG_PATTERNS['新标签'] = r'新的正则表达式'
```

## 注意事项

1. **请求频率**: 避免过于频繁的请求，以免对目标网站造成压力
2. **网站变化**: 网站结构可能会变化，需要及时更新解析逻辑
3. **数据库连接**: 确保数据库配置正确，并在使用前连接数据库
4. **错误处理**: 注意处理网络错误、解析错误等异常情况

## 依赖项

- requests: HTTP请求库
- BeautifulSoup4: HTML解析库
- mysql-connector-python: MySQL数据库连接库

## 调试和问题排查

如果遇到问题，可以查看日志文件`hot_topic_tool.log`，其中记录了详细的运行信息和错误信息。

常见问题排查：

1. **无法连接网站**: 检查网络连接和请求头设置
2. **解析失败**: 检查网站结构是否变化，更新选择器
3. **数据库错误**: 检查数据库配置和连接状态
4. **数据不完整**: 检查解析逻辑和数据处理流程

## 后续优化方向

1. **并发采集**: 使用多线程或异步IO提高采集效率
2. **代理支持**: 添加代理IP支持，避免IP被封
3. **更智能的分类**: 使用NLP技术提高话题分类准确性
4. **数据分析**: 添加热搜话题趋势分析功能
5. **API接口**: 提供RESTful API接口供其他系统调用