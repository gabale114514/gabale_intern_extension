# 数据库设计文档

## 概述

本文档描述了热搜话题处理工具的数据库设计。该数据库用于存储从微博、知乎、小红书、今日头条、百度、雪球、抖音、哔哩哔哩等8个平台采集的热搜榜数据。

## 数据库信息

- **数据库类型**: MySQL
- **字符集**: utf8mb4
- **排序规则**: utf8mb4_unicode_ci

## 表设计

### 1. 平台表 (platforms)

存储支持的平台信息。

| 字段名 | 类型 | 约束 | 描述 |
|--------|------|------|------|
| id | INT | PRIMARY KEY, AUTO_INCREMENT | 平台ID |
| code | VARCHAR(20) | NOT NULL, UNIQUE | 平台代码 (如 'weibo', 'zhihu') |
| name | VARCHAR(50) | NOT NULL | 平台名称 (如 '微博', '知乎') |
| icon | VARCHAR(10) | | 平台图标 (Emoji) |
| enabled | BOOLEAN | NOT NULL, DEFAULT TRUE | 是否启用 |
| created_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP | 更新时间 |

### 2. 热搜话题表 (hot_topics)

存储采集的热搜话题数据。

| 字段名 | 类型 | 约束 | 描述 |
|--------|------|------|------|
| id | BIGINT | PRIMARY KEY, AUTO_INCREMENT | 话题ID |
| platform_id | INT | NOT NULL, FOREIGN KEY | 关联平台ID |
| title | VARCHAR(500) | NOT NULL | 话题标题 |
| rank | INT | NOT NULL | 排名 (1-1000) |
| heat_value | INT | | 热度值 |
| url | VARCHAR(1000) | | 话题链接 |
| hash_id | VARCHAR(32) | NOT NULL, UNIQUE | 去重哈希ID |
| category | VARCHAR(20) | | 话题分类 |
| first_seen_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | 首次发现时间 |
| last_seen_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | 最近发现时间 |
| created_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP | 更新时间 |

### 3. 话题标签表 (topic_tags)

存储话题的标签信息。

| 字段名 | 类型 | 约束 | 描述 |
|--------|------|------|------|
| id | BIGINT | PRIMARY KEY, AUTO_INCREMENT | 标签ID |
| topic_id | BIGINT | NOT NULL, FOREIGN KEY | 关联话题ID |
| tag_name | VARCHAR(20) | NOT NULL | 标签名称 (如 '热', '新', '辟谣') |
| created_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | 创建时间 |

### 4. 采集记录表 (collection_logs)

记录每次采集的状态和结果。

| 字段名 | 类型 | 约束 | 描述 |
|--------|------|------|------|
| id | BIGINT | PRIMARY KEY, AUTO_INCREMENT | 记录ID |
| platform_id | INT | NOT NULL, FOREIGN KEY | 关联平台ID |
| status | ENUM('success', 'failed', 'partial') | NOT NULL | 采集状态 |
| total_count | INT | NOT NULL, DEFAULT 0 | 采集总数 |
| success_count | INT | NOT NULL, DEFAULT 0 | 成功数量 |
| error_count | INT | NOT NULL, DEFAULT 0 | 错误数量 |
| duplicate_count | INT | NOT NULL, DEFAULT 0 | 重复数量 |
| error_message | TEXT | | 错误信息 |
| start_time | TIMESTAMP | NOT NULL | 开始时间 |
| end_time | TIMESTAMP | NOT NULL | 结束时间 |
| created_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | 创建时间 |

## 索引设计

### hot_topics 表索引

- PRIMARY KEY (`id`)
- UNIQUE INDEX `idx_hash_id` (`hash_id`)
- INDEX `idx_platform_rank` (`platform_id`, `rank`)
- INDEX `idx_category` (`category`)
- INDEX `idx_first_seen` (`first_seen_at`)
- INDEX `idx_last_seen` (`last_seen_at`)

### topic_tags 表索引

- PRIMARY KEY (`id`)
- INDEX `idx_topic_tag` (`topic_id`, `tag_name`)

### collection_logs 表索引

- PRIMARY KEY (`id`)
- INDEX `idx_platform_time` (`platform_id`, `start_time`)
- INDEX `idx_status` (`status`)

## 关系图

```
platforms 1 --< hot_topics >-- * topic_tags
platforms 1 --< collection_logs
```

## 数据维护策略

1. **数据去重**:
   - 使用 `hash_id` 字段进行去重
   - 对于重复数据，仅更新 `last_seen_at` 和排名相关信息

2. **数据清理**:
   - 定期清理超过30天未出现在热搜榜的话题
   - 保留历史数据的摘要统计信息

3. **备份策略**:
   - 每日进行增量备份
   - 每周进行完整备份
   - 备份保留期为3个月

## 扩展性考虑

1. **新平台支持**:
   - 通过在 `platforms` 表中添加新记录即可支持新平台
   - 无需修改数据库结构

2. **数据分析需求**:
   - 可以基于现有表结构进行统计分析
   - 可以添加额外的统计表以支持更复杂的分析需求

3. **性能优化**:
   - 对于大数据量场景，可考虑按时间或平台进行表分区
   - 可以添加缓存层减轻数据库负担