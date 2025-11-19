# B站热门视频趋势分析工具

一个用于分析哔哩哔哩(bilibili)热门视频趋势的Python工具。

## 功能特性

- **数据采集**: 通过B站公开API获取热门视频和排行榜数据
- **关键词分析**: 使用jieba分词进行关键词提取和词频统计
- **数据可视化**: 生成词云图、播放量排行、分区分布等图表
- **报告生成**: 自动生成包含趋势分析的详细报告
- **Web界面**: 提供交互式可视化仪表盘（基于Flask + ECharts）

## 安装

### 快速部署（推荐）

使用一键部署脚本自动完成所有安装步骤：

**Linux/macOS:**
```bash
chmod +x setup.sh
./setup.sh
```

**Windows:**
```cmd
setup.bat
```

脚本会自动完成：创建虚拟环境、安装依赖、安装中文字体、测试API连接。

### 手动安装

#### 1. 克隆项目

```bash
git clone <repository-url>
cd bilibili-hot-analyzer
```

#### 2. 创建虚拟环境（推荐）

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
```

#### 3. 安装依赖

```bash
pip install -r requirements.txt
```

#### 4. 安装中文字体（用于词云生成）

**Ubuntu/Debian:**
```bash
sudo apt-get install fonts-wqy-microhei fonts-wqy-zenhei
```

**CentOS/RHEL:**
```bash
sudo yum install wqy-microhei-fonts wqy-zenhei-fonts
```

**macOS:**
系统自带中文字体，无需安装。

**Windows:**
系统自带中文字体，无需安装。

## 使用方法

### 基本用法

```bash
# 使用默认参数（获取5页热门视频）
python bilibili_analyzer.py

# 获取10页热门视频（200个视频）
python bilibili_analyzer.py -p 10

# 获取游戏区排行榜
python bilibili_analyzer.py -t 排行榜 -r 游戏

# 指定输出目录
python bilibili_analyzer.py -o my_analysis
```

### 命令行参数

| 参数 | 简写 | 说明 | 默认值 |
|------|------|------|--------|
| `--pages` | `-p` | 热门视频页数（每页20个） | 5 |
| `--type` | `-t` | 数据类型：热门/排行榜 | 热门 |
| `--region` | `-r` | 分区名称（排行榜模式） | 全站 |
| `--delay` | `-d` | 请求间隔时间（秒） | 1.0 |
| `--output` | `-o` | 输出目录 | output |

### 支持的分区

全站、动画、音乐、舞蹈、游戏、知识、科技、运动、汽车、生活、美食、动物圈、鬼畜、时尚、资讯、娱乐、影视、纪录片、电影、电视剧

### Web可视化界面

启动Web服务器，在浏览器中查看交互式分析结果：

```bash
python web_app.py
```

然后访问 http://localhost:5000

**Web界面功能：**
- 交互式词云图
- 动态图表（播放量分布、分区饼图、互动率等）
- 视频列表展示
- 一键导出CSV
- 支持选择不同分区和数据量

## 输出文件

运行后会在输出目录生成以下文件：

| 文件名 | 说明 |
|--------|------|
| `bilibili_hot_videos.csv` | 原始视频数据（CSV格式） |
| `wordcloud.png` | 关键词词云图 |
| `analysis_charts.png` | 数据分析图表集 |
| `analysis_report.txt` | 文字分析报告 |

### CSV数据字段

| 字段 | 说明 |
|------|------|
| bvid | 视频BV号 |
| title | 视频标题 |
| up_name | UP主名称 |
| view | 播放量 |
| like | 点赞数 |
| coin | 投币数 |
| favorite | 收藏数 |
| share | 分享数 |
| reply | 评论数 |
| danmaku | 弹幕数 |
| pub_time | 发布时间 |
| duration | 视频时长（秒） |
| tname | 分区名称 |
| url | 视频链接 |

## 使用示例

### 示例1：分析全站热门视频

```bash
python bilibili_analyzer.py -p 10
```

### 示例2：分析科技区排行榜

```bash
python bilibili_analyzer.py -t 排行榜 -r 科技
```

### 示例3：快速测试（减少请求）

```bash
python bilibili_analyzer.py -p 2 -d 0.5
```

## 环境变量配置

| 环境变量 | 说明 | 默认值 |
|----------|------|--------|
| `BILIBILI_AUTO_SAVE` | 是否自动保存爬取的原始数据 | `true` |

### 使用示例

```bash
# 关闭自动保存
BILIBILI_AUTO_SAVE=false python bilibili_analyzer.py

# 开启自动保存（默认行为）
BILIBILI_AUTO_SAVE=true python bilibili_analyzer.py

# Windows PowerShell
$env:BILIBILI_AUTO_SAVE="false"; python bilibili_analyzer.py

# Windows CMD
set BILIBILI_AUTO_SAVE=false && python bilibili_analyzer.py
```

自动保存功能会将爬取的原始数据保存为JSON文件到 `output` 目录，文件名格式为 `raw_data_{type}_{timestamp}.json`。

## 注意事项

1. **请求频率**: 脚本默认每次请求间隔1秒，请勿过于频繁调用以避免被限制
2. **API限制**: 使用B站公开API，无需登录即可使用
3. **中文字体**: 生成词云需要中文字体支持，请确保系统已安装
4. **数据时效**: 热门视频数据实时更新，每次运行结果可能不同

## 法律声明

- 本工具仅供学习和研究使用
- 请遵守B站的服务条款和相关法律法规
- 不得用于商业用途或任何违法目的
- 采集的数据请勿用于侵犯他人隐私

## 技术说明

### 使用的API

- 综合热门: `https://api.bilibili.com/x/web-interface/popular`
- 排行榜: `https://api.bilibili.com/x/web-interface/ranking/v2`

### 依赖库

- `requests`: HTTP请求
- `pandas`: 数据处理
- `jieba`: 中文分词
- `matplotlib`: 图表绑制
- `wordcloud`: 词云生成
- `flask`: Web服务器

## 常见问题

### Q: 词云图显示方框或乱码？

A: 需要安装中文字体，参考安装部分的说明。

### Q: 请求被拒绝？

A: 可能是请求过于频繁，增加 `-d` 参数的值（如 `-d 2`）。

### Q: 如何获取更多数据？

A: 增加 `-p` 参数值，但建议不要超过50页以避免给服务器造成压力。

## 贡献

欢迎提交Issue和Pull Request！

## 许可证

MIT License
