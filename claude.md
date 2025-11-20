# Bilibili Hot Video Trend Analyzer

## 项目概述

这是一个用于分析哔哩哔哩(B站)热门视频趋势的Python工具，包含命令行脚本和Web可视化界面。支持数据采集、关键词分析、统计可视化、历史数据存储等完整功能。

## 技术栈

- **语言**: Python 3.8+
- **Web框架**: Flask
- **数据处理**: pandas, numpy
- **中文分词**: jieba (支持TF-IDF关键词提取)
- **可视化**: matplotlib, wordcloud, ECharts (前端)
- **HTTP请求**: requests
- **数据库**: SQLite (内置，轻量级)

## 项目结构

```
bilibili-hot-analyzer/
├── bilibili_analyzer.py   # 命令行分析脚本
├── web_app.py             # Flask Web应用
├── database.py            # SQLite数据库模块
├── setup.sh               # Linux/macOS一键部署脚本
├── setup.bat              # Windows一键部署脚本
├── templates/
│   └── index.html         # Web界面模板 (响应式设计)
├── requirements.txt       # Python依赖
├── README.md              # 项目文档
├── claude.md              # 项目技术文档 (本文件)
└── output/                # 输出目录(自动创建)
    ├── bilibili_data.db   # SQLite数据库文件
    ├── raw_data_*.json    # 原始数据备份
    └── *.csv, *.png       # 导出文件
```

## 核心功能模块

### bilibili_analyzer.py (命令行分析器)

**BilibiliAnalyzer 类 - 主分析器:**

- `fetch_popular_videos(pages=5, delay=1.0)`: 获取综合热门视频
  - 分页获取，每页20个视频
  - 支持自定义请求延迟防止限流

- `fetch_ranking_videos(partition='全站')`: 获取分区排行榜
  - 支持20个分区选择
  - 返回单页排行数据

- `analyze_keywords(top_n=100)`: 关键词分析
  - 使用jieba分词
  - TF-IDF算法提取关键词
  - 过滤停用词和数字

- `analyze_statistics()`: 统计分析
  - 播放量/点赞/评论等描述统计
  - 互动率计算
  - TOP视频/UP主排行

- `generate_wordcloud(word_freq)`: 生成词云图
  - 自动查找系统中文字体
  - 支持Linux/macOS/Windows

- `generate_charts(stats)`: 生成分析图表
  - 播放量分布直方图
  - 分区分布饼图
  - TOP20视频柱状图
  - 互动率对比图

- `auto_save_raw_data(videos, data_type)`: 自动保存原始数据
  - JSON格式存储
  - 时间戳命名
  - 可通过环境变量控制

**关键实现细节:**

```python
# HTTPS图片URL转换 (修复混合内容安全问题)
pic_url = video.get('pic', '')
if pic_url.startswith('http://'):
    pic_url = pic_url.replace('http://', 'https://', 1)
```

### web_app.py (Flask Web应用)

**Flask路由定义:**

| 路由 | 方法 | 功能 | 参数 |
|------|------|------|------|
| `/` | GET | 主页渲染 | - |
| `/api/fetch` | POST | 获取视频数据 | type, pages, partition |
| `/api/analysis` | GET | 获取分析结果 | - |
| `/api/export` | GET | 导出CSV文件 | - |
| `/api/history` | GET | 获取历史爬取记录 | limit (默认20) |
| `/api/history/<id>` | GET | 获取指定记录详情 | crawl_id |
| `/api/stats` | GET | 数据库统计信息 | - |
| `/api/search` | GET | 搜索历史视频 | q (关键词) |
| `/api/top-ups` | GET | 获取热门UP主 | days (默认7), limit (默认20) |

**核心功能:**

- 全局缓存机制: 减少重复数据处理
- 自动数据保存: JSON + SQLite双重备份
- 错误处理: 统一的JSON响应格式
- 日志记录: logging模块记录操作

**数据流程:**

1. 前端请求 → `/api/fetch`
2. 调用 `fetch_videos()` 获取数据
3. 保存到缓存 `cache['videos']`
4. 自动保存JSON文件 (如果启用)
5. 保存到SQLite数据库 (如果启用)
6. 返回成功响应

### database.py (SQLite数据库模块)

**BilibiliDatabase 类 - 数据库操作:**

**数据库表结构:**

```sql
-- 爬取记录表
CREATE TABLE crawl_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    crawl_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    data_type TEXT,
    partition TEXT,
    video_count INTEGER
);

-- 视频数据表
CREATE TABLE videos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    crawl_id INTEGER,
    bvid TEXT,
    title TEXT,
    up_name TEXT,
    up_mid INTEGER,
    view INTEGER,
    like INTEGER,
    coin INTEGER,
    favorite INTEGER,
    share INTEGER,
    reply INTEGER,
    danmaku INTEGER,
    pub_time TEXT,
    duration INTEGER,
    tname TEXT,
    pic TEXT,
    url TEXT,
    FOREIGN KEY (crawl_id) REFERENCES crawl_records(id)
);

-- 关键词表
CREATE TABLE keywords (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    crawl_id INTEGER,
    keyword TEXT,
    frequency INTEGER,
    tfidf_weight REAL,
    FOREIGN KEY (crawl_id) REFERENCES crawl_records(id)
);

-- 索引优化
CREATE INDEX idx_videos_crawl_id ON videos(crawl_id);
CREATE INDEX idx_videos_bvid ON videos(bvid);
CREATE INDEX idx_videos_title ON videos(title);
CREATE INDEX idx_keywords_crawl_id ON keywords(crawl_id);
```

**核心方法:**

- `save_crawl_record()`: 保存爬取记录，返回crawl_id
- `save_videos(videos, crawl_id)`: 批量保存视频数据
- `save_keywords(keywords, crawl_id)`: 保存关键词统计
- `get_crawl_records(limit)`: 获取历史记录列表
- `get_videos_by_crawl_id(crawl_id)`: 按爬取ID获取视频
- `search_videos(keyword, limit)`: 全文搜索视频
- `get_statistics()`: 获取数据库统计信息
- `get_top_ups(days, limit)`: 获取时间范围内热门UP主
- `get_trending_keywords(crawl_id, limit)`: 获取爬取记录的热门关键词

**单例模式实现:**

```python
_db_instance = None

def get_database():
    """获取数据库单例"""
    global _db_instance
    if not DB_ENABLED:
        return None
    if _db_instance is None:
        _db_instance = BilibiliDatabase()
    return _db_instance
```

### templates/index.html (Web前端界面)

**响应式设计实现:**

```css
/* 容器宽度优化 */
.container {
    max-width: 1200px;  /* 从1400px优化为1200px */
    margin: 0 auto;
    padding: 0 15px;
}

/* 响应式断点 */
@media (max-width: 1200px) {
    .charts-grid {
        grid-template-columns: 1fr;  /* 单列布局 */
    }
}

@media (max-width: 768px) {
    .stats-grid {
        grid-template-columns: repeat(2, 1fr);  /* 移动端2列 */
    }
}
```

**ECharts配置优化:**

```javascript
// Grid配置 - 确保图表完整显示
grid: {
    left: '5%',
    right: '15%',
    top: '5%',
    bottom: '5%',
    containLabel: true  // 自动计算坐标轴标签空间
}

// 标题长度控制
name: title.length > 15 ? title.substring(0, 15) + '...' : title

// 自适应字体大小
axisLabel: {
    rotate: 45,
    fontSize: 11,
    interval: 0
}
```

**图表类型:**

- 词云图 (ECharts Wordcloud)
- 播放量分布直方图 (Bar Chart)
- 分区分布饼图 (Pie Chart)
- TOP20视频排行 (Horizontal Bar)
- 热门UP主排行 (Bar Chart)
- 互动率对比 (Bar Chart)

## 环境变量配置

| 变量 | 说明 | 默认值 | 示例 |
|------|------|--------|------|
| `BILIBILI_AUTO_SAVE` | 自动保存爬取的原始数据到JSON | `true` | `false` |
| `BILIBILI_DB_ENABLED` | 启用SQLite数据库存储 | `true` | `false` |

**使用示例:**

```bash
# Linux/macOS
export BILIBILI_AUTO_SAVE=false
python bilibili_analyzer.py

# Windows PowerShell
$env:BILIBILI_AUTO_SAVE="false"
python bilibili_analyzer.py

# Windows CMD
set BILIBILI_AUTO_SAVE=false && python bilibili_analyzer.py
```

## 开发指南

### 快速启动

```bash
# 1. 一键部署（推荐）
./setup.sh          # Linux/macOS
# 或
setup.bat           # Windows

# 2. 手动安装
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或 venv\Scripts\activate  # Windows
pip install -r requirements.txt

# 3. 运行项目
python bilibili_analyzer.py -p 5    # 命令行模式
python web_app.py                    # Web模式
```

### 代码规范

- **注释**: 使用中文注释说明关键逻辑
- **文档字符串**: 函数需要docstring说明参数和返回值
- **日志**: 使用logging模块记录重要操作
- **错误处理**: try-except捕获异常并记录日志
- **类型提示**: 建议使用类型注解提高代码可读性

### API使用注意事项

**B站API配置:**

```python
BILIBILI_API = {
    'popular': 'https://api.bilibili.com/x/web-interface/popular',
    'ranking': 'https://api.bilibili.com/x/web-interface/ranking/v2',
}

# 必需的请求头
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://www.bilibili.com/',
})
```

**请求参数:**

- 综合热门: `?ps=20&pn=页码`
- 排行榜: `?rid=分区ID&type=all`

**响应格式:**

```json
{
    "code": 0,          // 0表示成功
    "message": "0",
    "data": {
        "list": [...]   // 视频列表
    }
}
```

**注意事项:**

- 请求间隔默认1秒，避免被限流
- 超时设置为10秒
- 失败重试需要记录日志

### 常用命令

```bash
# 获取10页热门视频（200个）
python bilibili_analyzer.py -p 10

# 获取游戏区排行榜
python bilibili_analyzer.py -t 排行榜 -r 游戏

# 指定输出目录
python bilibili_analyzer.py -o my_output

# 减少请求延迟（测试用）
python bilibili_analyzer.py -p 2 -d 0.5

# 关闭自动保存和数据库
BILIBILI_AUTO_SAVE=false BILIBILI_DB_ENABLED=false python bilibili_analyzer.py

# 启动Web服务器
python web_app.py
# 访问 http://localhost:5000
```

## 分区ID映射

完整分区列表:

```python
PARTITION_MAP = {
    '全站': 0, '动画': 1, '音乐': 3, '舞蹈': 129, '游戏': 4,
    '知识': 36, '科技': 188, '运动': 234, '汽车': 223, '生活': 160,
    '美食': 211, '动物圈': 217, '鬼畜': 119, '时尚': 155, '资讯': 202,
    '娱乐': 5, '影视': 181, '纪录片': 177, '电影': 23, '电视剧': 11,
}
```

## 输出文件格式

### 命令行模式输出

| 文件名 | 格式 | 说明 |
|--------|------|------|
| `bilibili_hot_videos.csv` | CSV | 原始视频数据 |
| `wordcloud.png` | PNG | 关键词词云图 (800x600) |
| `analysis_charts.png` | PNG | 4合1分析图表 |
| `analysis_report.txt` | TXT | 文字分析报告 |
| `raw_data_*.json` | JSON | 原始数据备份 (可选) |

### 数据库存储

| 文件 | 说明 |
|------|------|
| `output/bilibili_data.db` | SQLite数据库文件 |

**CSV字段说明:**

```
bvid, title, desc, view, like, coin, favorite, share, reply, danmaku,
pub_time, duration, up_name, up_mid, tname, pic, url
```

## 最佳实践

### 1. 混合内容安全处理

**问题**: B站API返回的图片URL为HTTP，在HTTPS页面加载会被浏览器阻止

**解决方案**:

```python
def extract_video_info(video):
    # 转换HTTP图片URL为HTTPS
    pic_url = video.get('pic', '')
    if pic_url.startswith('http://'):
        pic_url = pic_url.replace('http://', 'https://', 1)
    return {'pic': pic_url, ...}
```

### 2. 响应式布局优化

**问题**: 图表在标准浏览器窗口(1920x1080)显示过宽，需要缩放

**解决方案**:

- 容器宽度: 1200px (适配主流屏幕)
- Grid布局: `containLabel: true` 自动计算标签空间
- 媒体查询: 多断点响应式设计
- 字体大小: 根据图表类型调整(11-14px)

### 3. 数据库性能优化

**索引策略**:

```sql
-- 必需索引
CREATE INDEX idx_videos_crawl_id ON videos(crawl_id);  -- 查询优化
CREATE INDEX idx_videos_bvid ON videos(bvid);          -- 去重
CREATE INDEX idx_videos_title ON videos(title);        -- 搜索加速
```

**批量插入**:

```python
# 使用executemany提高性能
cursor.executemany('INSERT INTO videos VALUES (...)', video_data)
```

### 4. 错误处理模式

```python
try:
    response = session.get(url, timeout=10)
    data = response.json()
    if data['code'] == 0:
        # 处理数据
    else:
        logger.error(f"API错误: {data.get('message')}")
except requests.RequestException as e:
    logger.error(f"网络请求失败: {e}")
except Exception as e:
    logger.error(f"未知错误: {e}")
```

### 5. 中文分词优化

**停用词过滤**:

```python
STOP_WORDS = set([
    '的', '了', '是', '在', '我', '有', '和', '就', '不', '人', '都', '一',
    '视频', 'BV', 'av', 'UP', 'up'  # B站特定词
])

# 过滤逻辑
words = jieba.cut(text)
filtered = [w for w in words if len(w) > 1 and w not in STOP_WORDS and not w.isdigit()]
```

### 6. 中文字体自动检测

```python
def find_chinese_font():
    """自动查找系统中文字体"""
    font_paths = [
        '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc',  # Linux
        '/System/Library/Fonts/PingFang.ttc',              # macOS
        'C:\\Windows\\Fonts\\msyh.ttc',                    # Windows
    ]
    for path in font_paths:
        if os.path.exists(path):
            return path
    return None
```

## 常见问题解决

### 问题1: 词云图显示方框或乱码

**原因**: 系统未安装中文字体

**解决**:

```bash
# Ubuntu/Debian
sudo apt-get install fonts-wqy-microhei fonts-wqy-zenhei

# CentOS/RHEL
sudo yum install wqy-microhei-fonts wqy-zenhei-fonts

# macOS/Windows: 系统自带，无需安装
```

### 问题2: 视频封面图片无法显示

**原因**: HTTP图片在HTTPS页面被浏览器阻止 (Mixed Content)

**解决**: 已在代码中自动转换HTTP→HTTPS

**验证**:

```bash
# 检查日志，应该看到HTTPS URL
logger.info(f"图片URL: {pic_url}")  # https://i0.hdslb.com/...
```

### 问题3: Web界面图表显示过宽

**原因**: 容器宽度设置过大或ECharts grid配置不当

**解决**: 已优化为1200px容器 + containLabel配置

**自定义调整**:

```css
/* templates/index.html */
.container {
    max-width: 1000px;  /* 根据需要调整 */
}
```

### 问题4: API请求被拒绝

**原因**: 请求频率过高

**解决**:

```bash
# 增加请求延迟
python bilibili_analyzer.py -d 2  # 2秒间隔
```

### 问题5: 数据库文件锁定

**原因**: 多个进程同时访问数据库

**解决**: 使用单例模式确保单一连接

```python
# database.py已实现单例
_db_instance = None  # 全局唯一实例
```

### 问题6: 依赖安装失败

**原因**: pip源速度慢或版本冲突

**解决**:

```bash
# 使用国内镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 升级pip
python -m pip install --upgrade pip
```

## 技术细节

### 数据采集流程

```
用户请求 → fetch_videos()
    ↓
设置User-Agent/Referer → requests.get()
    ↓
解析JSON响应 → extract_video_info()
    ↓
HTTP→HTTPS转换 → 返回视频列表
    ↓
[分支1] auto_save_raw_data() → JSON文件
[分支2] db.save_videos() → SQLite数据库
[分支3] cache['videos'] → 内存缓存
```

### 关键词分析流程

```
视频列表 → 提取标题+描述
    ↓
jieba分词 → 词频统计 (Counter)
    ↓
过滤停用词/数字 → TF-IDF提取
    ↓
返回: word_freq + tfidf_keywords
```

### Web可视化流程

```
前端点击"获取数据" → POST /api/fetch
    ↓
fetch_videos() → 保存到cache/DB
    ↓
前端自动请求 → GET /api/analysis
    ↓
analyze_keywords() + analyze_statistics()
    ↓
返回JSON → ECharts渲染图表
```

### 响应式设计断点

| 屏幕宽度 | 布局 | 说明 |
|----------|------|------|
| ≥1200px | 2列Grid | 桌面显示器 |
| 768-1199px | 1列Grid | 平板/小屏幕 |
| <768px | 2列Stats | 移动端 |

## 性能优化建议

### 1. 减少API请求

```python
# 使用缓存避免重复请求
if cache['videos'] and cache['last_fetch']:
    time_diff = datetime.now() - datetime.strptime(cache['last_fetch'], '%Y-%m-%d %H:%M:%S')
    if time_diff.seconds < 300:  # 5分钟内使用缓存
        return cache['videos']
```

### 2. 数据库查询优化

```python
# 使用LIMIT减少返回数据量
cursor.execute('SELECT * FROM videos LIMIT ?', (limit,))

# 使用索引字段查询
cursor.execute('SELECT * FROM videos WHERE crawl_id = ?', (crawl_id,))
```

### 3. 前端渲染优化

```javascript
// 限制视频列表显示数量
const displayVideos = videos.slice(0, 20);

// ECharts按需加载
echarts.init(dom, null, {renderer: 'canvas'});  // canvas模式更快
```

## 扩展开发建议

### 新增功能思路

1. **定时任务**: 使用APScheduler定时爬取数据
2. **数据对比**: 对比不同时间段的热门趋势
3. **UP主分析**: 深度分析特定UP主视频表现
4. **评论分析**: 爬取评论进行情感分析
5. **导出报告**: PDF格式的分析报告生成

### API扩展示例

```python
@app.route('/api/compare')
def api_compare():
    """对比两次爬取的数据"""
    crawl_id1 = request.args.get('id1', type=int)
    crawl_id2 = request.args.get('id2', type=int)
    # 实现对比逻辑...
```

## 注意事项

1. **请求频率**: 默认1秒间隔，请勿过于频繁避免被B站限制
2. **API限制**: 使用公开API，无需登录但有访问限制
3. **中文字体**: 生成词云必需，确保系统已安装
4. **数据时效**: 热门数据实时更新，结果每次可能不同
5. **存储空间**: 长期运行注意数据库文件大小
6. **隐私保护**: 采集数据仅供分析，勿用于侵犯隐私
7. **法律合规**: 遵守B站服务条款和相关法律法规

## 许可证

MIT License - 仅供学习和研究使用
