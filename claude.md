# Bilibili Hot Video Trend Analyzer

## 项目概述

这是一个用于分析哔哩哔哩(B站)热门视频趋势的Python工具，包含命令行脚本和Web可视化界面。

## 技术栈

- **语言**: Python 3.8+
- **Web框架**: Flask
- **数据处理**: pandas, numpy
- **中文分词**: jieba
- **可视化**: matplotlib, wordcloud, ECharts (前端)
- **HTTP请求**: requests
- **数据库**: SQLite (内置)

## 项目结构

```
bilibili-hot-analyzer/
├── bilibili_analyzer.py   # 命令行分析脚本
├── web_app.py             # Flask Web应用
├── database.py            # SQLite数据库模块
├── setup.sh               # Linux/macOS部署脚本
├── setup.bat              # Windows部署脚本
├── templates/
│   └── index.html         # Web界面模板
├── requirements.txt       # Python依赖
├── README.md              # 项目文档
└── output/                # 输出目录(自动创建)
    └── bilibili_data.db   # SQLite数据库文件
```

## 核心功能模块

### bilibili_analyzer.py
- `BilibiliAnalyzer` 类: 主分析器
  - `fetch_popular_videos()`: 获取综合热门视频
  - `fetch_ranking_videos()`: 获取分区排行榜
  - `analyze_keywords()`: 关键词分析
  - `analyze_statistics()`: 统计分析
  - `generate_wordcloud()`: 生成词云
  - `generate_charts()`: 生成图表
  - `auto_save_raw_data()`: 自动保存原始数据

### web_app.py
- Flask路由:
  - `GET /`: 主页
  - `POST /api/fetch`: 获取数据
  - `GET /api/analysis`: 获取分析结果
  - `GET /api/export`: 导出CSV
  - `GET /api/history`: 获取历史爬取记录
  - `GET /api/history/<id>`: 获取指定记录详情
  - `GET /api/stats`: 数据库统计
  - `GET /api/search`: 搜索视频
  - `GET /api/top-ups`: 热门UP主

### database.py
- `BilibiliDatabase` 类: 数据库操作
  - `save_crawl_record()`: 保存爬取记录
  - `save_videos()`: 批量保存视频
  - `save_keywords()`: 保存关键词
  - `get_crawl_records()`: 获取历史记录
  - `get_videos_by_crawl_id()`: 按ID获取视频
  - `search_videos()`: 搜索视频
  - `get_statistics()`: 数据库统计

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `BILIBILI_AUTO_SAVE` | 自动保存爬取数据 | `true` |
| `BILIBILI_DB_ENABLED` | 启用SQLite数据库 | `true` |

## 开发指南

### 运行项目

```bash
# 安装依赖
pip install -r requirements.txt

# 命令行模式
python bilibili_analyzer.py -p 5

# Web模式
python web_app.py
```

### 代码风格

- 使用中文注释说明关键逻辑
- 函数需要有docstring说明参数和返回值
- 使用logging记录重要操作
- 错误处理使用try-except并记录日志

### API使用注意

- B站API请求需要设置User-Agent和Referer
- 请求间隔默认1秒，避免被限流
- API响应code为0表示成功

### 常用命令

```bash
# 获取10页热门视频
python bilibili_analyzer.py -p 10

# 获取游戏区排行榜
python bilibili_analyzer.py -t 排行榜 -r 游戏

# 关闭自动保存
BILIBILI_AUTO_SAVE=false python bilibili_analyzer.py
```

## 分区ID映射

主要分区: 全站(0), 动画(1), 音乐(3), 游戏(4), 知识(36), 科技(188), 生活(160), 娱乐(5), 影视(181)

## 输出文件格式

- CSV: 视频列表数据
- PNG: 词云图、分析图表
- TXT: 文字分析报告
- JSON: 原始数据(自动保存)
- SQLite: 历史数据存储 (bilibili_data.db)

## 注意事项

- 生成词云需要系统安装中文字体
- Web界面使用CDN加载ECharts
- 数据实时性: 每次运行获取最新热门数据
- 遵守B站服务条款，仅用于学习研究
