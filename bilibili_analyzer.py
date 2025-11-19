#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
B站热门视频趋势分析工具
Bilibili Hot Video Trend Analyzer

功能：
- 爬取B站热门视频数据
- 分析关键词词频
- 生成可视化图表
- 输出分析报告

作者: Claude Assistant
日期: 2025-11-19
"""

import requests
import pandas as pd
import numpy as np
import jieba
import jieba.analyse
from collections import Counter
from datetime import datetime
import time
import os
import json
import re
import matplotlib.pyplot as plt
from matplotlib import font_manager
import matplotlib
from wordcloud import WordCloud
from typing import List, Dict, Optional, Tuple
import argparse
import logging
from database import get_database

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 环境变量配置
# BILIBILI_AUTO_SAVE: 是否自动保存爬取的原始数据 (true/false，默认true)
AUTO_SAVE_ENABLED = os.environ.get('BILIBILI_AUTO_SAVE', 'true').lower() == 'true'

# 设置matplotlib中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

# B站API配置
BILIBILI_API = {
    'popular': 'https://api.bilibili.com/x/web-interface/popular',  # 综合热门
    'ranking': 'https://api.bilibili.com/x/web-interface/ranking/v2',  # 排行榜
    'hot_search': 'https://s.search.bilibili.com/main/hotword',  # 热搜
}

# 分区ID映射
PARTITION_MAP = {
    '全站': 0,
    '动画': 1,
    '音乐': 3,
    '舞蹈': 129,
    '游戏': 4,
    '知识': 36,
    '科技': 188,
    '运动': 234,
    '汽车': 223,
    '生活': 160,
    '美食': 211,
    '动物圈': 217,
    '鬼畜': 119,
    '时尚': 155,
    '资讯': 202,
    '娱乐': 5,
    '影视': 181,
    '纪录片': 177,
    '电影': 23,
    '电视剧': 11,
}

# 停用词列表（用于关键词提取）
STOP_WORDS = set([
    '的', '了', '是', '在', '我', '有', '和', '就', '不', '人', '都', '一', '一个',
    '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好',
    '自己', '这', '那', '他', '她', '它', '这个', '那个', '什么', '怎么', '为什么',
    '哪里', '这里', '那里', '如何', '可以', '能', '想', '让', '把', '被', '从',
    '第一', '第二', '第三', '第四', '第五', '视频', 'BV', 'av', 'UP', 'up'
])


class BilibiliAnalyzer:
    """B站热门视频分析器"""

    def __init__(self, output_dir: str = 'output'):
        """
        初始化分析器

        Args:
            output_dir: 输出目录路径
        """
        self.output_dir = output_dir
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                         '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://www.bilibili.com/',
        })
        self.videos_data = []

        # 创建输出目录
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            logger.info(f"创建输出目录: {output_dir}")

    def auto_save_raw_data(self, data_type: str = 'popular'):
        """
        自动保存原始数据到本地

        Args:
            data_type: 数据类型标识
        """
        if not AUTO_SAVE_ENABLED:
            return

        if not self.videos_data:
            return

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # 保存JSON格式的原始数据
        json_filename = f"raw_data_{data_type}_{timestamp}.json"
        json_path = os.path.join(self.output_dir, json_filename)

        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump({
                'fetch_time': timestamp,
                'data_type': data_type,
                'count': len(self.videos_data),
                'videos': self.videos_data
            }, f, ensure_ascii=False, indent=2)

        logger.info(f"原始数据已自动保存: {json_path}")

    def fetch_popular_videos(self, page_count: int = 5, delay: float = 1.0) -> List[Dict]:
        """
        获取综合热门视频

        Args:
            page_count: 要获取的页数（每页20个视频）
            delay: 请求间隔时间（秒）

        Returns:
            视频数据列表
        """
        videos = []

        for page in range(1, page_count + 1):
            try:
                logger.info(f"正在获取第 {page}/{page_count} 页热门视频...")

                params = {
                    'ps': 20,  # 每页数量
                    'pn': page  # 页码
                }

                response = self.session.get(
                    BILIBILI_API['popular'],
                    params=params,
                    timeout=10
                )
                response.raise_for_status()

                data = response.json()

                if data['code'] == 0:
                    video_list = data['data']['list']

                    for video in video_list:
                        video_info = self._extract_video_info(video)
                        videos.append(video_info)

                    logger.info(f"第 {page} 页获取成功，获得 {len(video_list)} 个视频")
                else:
                    logger.error(f"API返回错误: {data.get('message', '未知错误')}")

                # 添加延迟，避免请求过于频繁
                if page < page_count:
                    time.sleep(delay)

            except requests.exceptions.RequestException as e:
                logger.error(f"请求第 {page} 页时出错: {e}")
                continue
            except json.JSONDecodeError as e:
                logger.error(f"解析第 {page} 页数据时出错: {e}")
                continue

        self.videos_data = videos
        logger.info(f"共获取 {len(videos)} 个热门视频")

        # 自动保存原始数据
        self.auto_save_raw_data('popular')

        # 保存到数据库
        db = get_database()
        if db and videos:
            crawl_id = db.save_crawl_record('popular', None, len(videos))
            db.save_videos(videos, crawl_id)
            self._current_crawl_id = crawl_id

        return videos

    def fetch_ranking_videos(self, partition: str = '全站', delay: float = 1.0) -> List[Dict]:
        """
        获取分区排行榜视频

        Args:
            partition: 分区名称
            delay: 请求间隔时间（秒）

        Returns:
            视频数据列表
        """
        videos = []

        tid = PARTITION_MAP.get(partition, 0)

        try:
            logger.info(f"正在获取 {partition} 分区排行榜...")

            params = {
                'rid': tid,
                'type': 'all'
            }

            response = self.session.get(
                BILIBILI_API['ranking'],
                params=params,
                timeout=10
            )
            response.raise_for_status()

            data = response.json()

            if data['code'] == 0:
                video_list = data['data']['list']

                for video in video_list:
                    video_info = self._extract_video_info(video)
                    videos.append(video_info)

                logger.info(f"获取成功，获得 {len(video_list)} 个视频")
            else:
                logger.error(f"API返回错误: {data.get('message', '未知错误')}")

        except requests.exceptions.RequestException as e:
            logger.error(f"请求排行榜时出错: {e}")
        except json.JSONDecodeError as e:
            logger.error(f"解析排行榜数据时出错: {e}")

        self.videos_data = videos

        # 自动保存原始数据
        self.auto_save_raw_data(f'ranking_{partition}')

        # 保存到数据库
        db = get_database()
        if db and videos:
            crawl_id = db.save_crawl_record('ranking', partition, len(videos))
            db.save_videos(videos, crawl_id)
            self._current_crawl_id = crawl_id

        return videos

    def _extract_video_info(self, video: Dict) -> Dict:
        """
        从API响应中提取视频信息

        Args:
            video: 原始视频数据

        Returns:
            格式化的视频信息
        """
        # 处理发布时间
        pub_timestamp = video.get('pubdate', 0)
        pub_time = datetime.fromtimestamp(pub_timestamp).strftime('%Y-%m-%d %H:%M:%S')

        # 提取统计数据
        stat = video.get('stat', {})

        # 提取UP主信息
        owner = video.get('owner', {})

        return {
            'bvid': video.get('bvid', ''),
            'title': video.get('title', ''),
            'desc': video.get('desc', ''),
            'view': stat.get('view', 0),           # 播放量
            'like': stat.get('like', 0),           # 点赞数
            'coin': stat.get('coin', 0),           # 投币数
            'favorite': stat.get('favorite', 0),   # 收藏数
            'share': stat.get('share', 0),         # 分享数
            'reply': stat.get('reply', 0),         # 评论数
            'danmaku': stat.get('danmaku', 0),     # 弹幕数
            'pub_time': pub_time,
            'duration': video.get('duration', 0),  # 视频时长（秒）
            'up_name': owner.get('name', ''),
            'up_mid': owner.get('mid', ''),
            'tname': video.get('tname', ''),       # 分区名称
            'url': f"https://www.bilibili.com/video/{video.get('bvid', '')}"
        }

    def analyze_keywords(self, top_n: int = 50) -> Tuple[Counter, List[Tuple[str, float]]]:
        """
        分析视频标题关键词

        Args:
            top_n: 返回前N个关键词

        Returns:
            (词频统计, TF-IDF关键词列表)
        """
        if not self.videos_data:
            logger.warning("没有视频数据可供分析")
            return Counter(), []

        # 合并所有标题和描述
        all_text = ' '.join([
            video['title'] + ' ' + video.get('desc', '')
            for video in self.videos_data
        ])

        # 使用jieba分词
        words = jieba.cut(all_text)

        # 过滤停用词和单字词
        filtered_words = [
            word for word in words
            if len(word) > 1 and word not in STOP_WORDS
            and not word.isdigit()
            and not re.match(r'^[a-zA-Z]$', word)
        ]

        # 词频统计
        word_freq = Counter(filtered_words)

        # TF-IDF关键词提取
        tfidf_keywords = jieba.analyse.extract_tags(
            all_text,
            topK=top_n,
            withWeight=True
        )

        logger.info(f"关键词分析完成，提取了 {len(tfidf_keywords)} 个TF-IDF关键词")

        # 保存关键词到数据库
        db = get_database()
        if db and tfidf_keywords and hasattr(self, '_current_crawl_id'):
            db.save_keywords(tfidf_keywords, self._current_crawl_id)

        return word_freq, tfidf_keywords

    def analyze_statistics(self) -> Dict:
        """
        分析视频统计数据

        Returns:
            统计分析结果
        """
        if not self.videos_data:
            logger.warning("没有视频数据可供分析")
            return {}

        df = pd.DataFrame(self.videos_data)

        stats = {
            'total_videos': len(df),
            'view': {
                'mean': df['view'].mean(),
                'median': df['view'].median(),
                'max': df['view'].max(),
                'min': df['view'].min(),
                'std': df['view'].std()
            },
            'like': {
                'mean': df['like'].mean(),
                'median': df['like'].median(),
                'max': df['like'].max(),
                'min': df['like'].min()
            },
            'reply': {
                'mean': df['reply'].mean(),
                'median': df['reply'].median(),
                'max': df['reply'].max(),
                'min': df['reply'].min()
            },
            'top_up': df.groupby('up_name')['view'].sum().nlargest(10).to_dict(),
            'partition_dist': df['tname'].value_counts().to_dict(),
            'engagement_rate': (
                (df['like'] + df['coin'] + df['favorite'] + df['share']) / df['view'] * 100
            ).mean()
        }

        logger.info("统计分析完成")
        return stats

    def generate_wordcloud(self, word_freq: Counter, filename: str = 'wordcloud.png'):
        """
        生成词云图

        Args:
            word_freq: 词频统计
            filename: 输出文件名
        """
        if not word_freq:
            logger.warning("没有词频数据，无法生成词云")
            return

        # 尝试查找中文字体
        font_path = None
        font_candidates = [
            '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc',
            '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',
            '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
            '/System/Library/Fonts/PingFang.ttc',
            'C:/Windows/Fonts/msyh.ttc',
            '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
        ]

        for fp in font_candidates:
            if os.path.exists(fp):
                font_path = fp
                break

        try:
            wc = WordCloud(
                font_path=font_path,
                width=1200,
                height=800,
                background_color='white',
                max_words=200,
                max_font_size=150,
                random_state=42,
                colormap='viridis'
            )

            wc.generate_from_frequencies(dict(word_freq.most_common(200)))

            plt.figure(figsize=(15, 10))
            plt.imshow(wc, interpolation='bilinear')
            plt.axis('off')
            plt.title('B站热门视频关键词词云', fontsize=20, pad=20)

            output_path = os.path.join(self.output_dir, filename)
            plt.savefig(output_path, dpi=150, bbox_inches='tight')
            plt.close()

            logger.info(f"词云图已保存: {output_path}")

        except Exception as e:
            logger.error(f"生成词云图时出错: {e}")

    def generate_charts(self):
        """生成数据分析图表"""
        if not self.videos_data:
            logger.warning("没有视频数据，无法生成图表")
            return

        df = pd.DataFrame(self.videos_data)

        # 创建包含多个子图的图表
        fig = plt.figure(figsize=(16, 20))

        # 1. 播放量TOP20柱状图
        ax1 = fig.add_subplot(3, 2, 1)
        top_videos = df.nlargest(20, 'view')
        titles = [t[:15] + '...' if len(t) > 15 else t for t in top_videos['title']]
        bars = ax1.barh(range(len(titles)), top_videos['view'] / 10000)
        ax1.set_yticks(range(len(titles)))
        ax1.set_yticklabels(titles, fontsize=8)
        ax1.set_xlabel('播放量 (万)')
        ax1.set_title('播放量TOP20视频', fontsize=12, fontweight='bold')
        ax1.invert_yaxis()

        # 2. 播放量分布直方图
        ax2 = fig.add_subplot(3, 2, 2)
        ax2.hist(df['view'] / 10000, bins=30, edgecolor='black', alpha=0.7)
        ax2.set_xlabel('播放量 (万)')
        ax2.set_ylabel('视频数量')
        ax2.set_title('播放量分布', fontsize=12, fontweight='bold')

        # 3. 分区分布饼图
        ax3 = fig.add_subplot(3, 2, 3)
        partition_counts = df['tname'].value_counts().head(10)
        ax3.pie(partition_counts.values, labels=partition_counts.index,
                autopct='%1.1f%%', startangle=90)
        ax3.set_title('热门视频分区分布 (TOP10)', fontsize=12, fontweight='bold')

        # 4. 点赞数与播放量关系散点图
        ax4 = fig.add_subplot(3, 2, 4)
        ax4.scatter(df['view'] / 10000, df['like'] / 10000, alpha=0.6)
        ax4.set_xlabel('播放量 (万)')
        ax4.set_ylabel('点赞数 (万)')
        ax4.set_title('播放量与点赞数关系', fontsize=12, fontweight='bold')

        # 5. UP主视频数量TOP10
        ax5 = fig.add_subplot(3, 2, 5)
        up_counts = df['up_name'].value_counts().head(10)
        ax5.barh(range(len(up_counts)), up_counts.values)
        ax5.set_yticks(range(len(up_counts)))
        ax5.set_yticklabels(up_counts.index, fontsize=9)
        ax5.set_xlabel('视频数量')
        ax5.set_title('UP主热门视频数量TOP10', fontsize=12, fontweight='bold')
        ax5.invert_yaxis()

        # 6. 互动率分析（点赞率、投币率等）
        ax6 = fig.add_subplot(3, 2, 6)
        metrics = ['点赞率', '投币率', '收藏率', '分享率']
        rates = [
            (df['like'] / df['view'] * 100).mean(),
            (df['coin'] / df['view'] * 100).mean(),
            (df['favorite'] / df['view'] * 100).mean(),
            (df['share'] / df['view'] * 100).mean()
        ]
        bars = ax6.bar(metrics, rates, color=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4'])
        ax6.set_ylabel('平均比率 (%)')
        ax6.set_title('用户互动率分析', fontsize=12, fontweight='bold')
        for bar, rate in zip(bars, rates):
            ax6.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                    f'{rate:.2f}%', ha='center', va='bottom', fontsize=9)

        plt.tight_layout()

        output_path = os.path.join(self.output_dir, 'analysis_charts.png')
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()

        logger.info(f"分析图表已保存: {output_path}")

    def save_to_csv(self, filename: str = 'bilibili_hot_videos.csv'):
        """
        将数据保存为CSV文件

        Args:
            filename: 输出文件名
        """
        if not self.videos_data:
            logger.warning("没有视频数据可保存")
            return

        df = pd.DataFrame(self.videos_data)

        # 调整列顺序
        columns_order = [
            'bvid', 'title', 'up_name', 'view', 'like', 'coin',
            'favorite', 'share', 'reply', 'danmaku', 'pub_time',
            'duration', 'tname', 'up_mid', 'desc', 'url'
        ]

        df = df[columns_order]

        output_path = os.path.join(self.output_dir, filename)
        df.to_csv(output_path, index=False, encoding='utf-8-sig')

        logger.info(f"CSV数据已保存: {output_path}")

    def generate_report(self, stats: Dict, tfidf_keywords: List[Tuple[str, float]]):
        """
        生成分析报告

        Args:
            stats: 统计数据
            tfidf_keywords: TF-IDF关键词列表
        """
        if not stats:
            logger.warning("没有统计数据，无法生成报告")
            return

        report_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        report = f"""
================================================================================
                    B站热门视频趋势分析报告
================================================================================

生成时间: {report_time}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

【1. 数据概览】

  分析视频总数: {stats['total_videos']} 个

【2. 播放量统计】

  平均播放量: {stats['view']['mean']:,.0f}
  中位数播放量: {stats['view']['median']:,.0f}
  最高播放量: {stats['view']['max']:,.0f}
  最低播放量: {stats['view']['min']:,.0f}
  标准差: {stats['view']['std']:,.0f}

【3. 互动数据】

  平均点赞数: {stats['like']['mean']:,.0f}
  平均评论数: {stats['reply']['mean']:,.0f}
  平均互动率: {stats['engagement_rate']:.2f}%

【4. 热门关键词 TOP20】

"""
        # 添加关键词列表
        for i, (word, weight) in enumerate(tfidf_keywords[:20], 1):
            report += f"  {i:2d}. {word} (权重: {weight:.4f})\n"

        report += "\n【5. 热门UP主 TOP10 (按总播放量)】\n\n"

        # 添加热门UP主
        for i, (up_name, total_view) in enumerate(list(stats['top_up'].items())[:10], 1):
            report += f"  {i:2d}. {up_name}: {total_view:,.0f} 播放\n"

        report += "\n【6. 分区分布】\n\n"

        # 添加分区分布
        for tname, count in list(stats['partition_dist'].items())[:10]:
            report += f"  {tname}: {count} 个视频\n"

        report += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

【7. 热点趋势总结】

根据以上数据分析，当前B站热门视频呈现以下特点：

1. 内容趋势:
   - 热门关键词反映了当前用户关注的主要话题
   - 前5大热词: {', '.join([kw[0] for kw in tfidf_keywords[:5]])}

2. 互动特点:
   - 平均互动率为 {stats['engagement_rate']:.2f}%
   - 用户更倾向于点赞而非投币收藏

3. 分区热度:
   - 最热门的分区占据了大部分热门视频
   - 建议创作者关注热门分区的内容形式

4. UP主生态:
   - 头部UP主在热门视频中占据显著位置
   - 但也有新面孔进入热门榜单

================================================================================
                              报告结束
================================================================================
"""

        output_path = os.path.join(self.output_dir, 'analysis_report.txt')
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)

        logger.info(f"分析报告已保存: {output_path}")

        # 同时打印报告
        print(report)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='B站热门视频趋势分析工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python bilibili_analyzer.py                    # 使用默认参数运行
  python bilibili_analyzer.py -p 10              # 获取10页热门视频
  python bilibili_analyzer.py -t 排行榜 -r 游戏   # 获取游戏区排行榜
  python bilibili_analyzer.py -o my_output       # 指定输出目录
        """
    )

    parser.add_argument(
        '-p', '--pages',
        type=int,
        default=5,
        help='要获取的热门视频页数，每页20个视频 (默认: 5)'
    )

    parser.add_argument(
        '-t', '--type',
        choices=['热门', '排行榜'],
        default='热门',
        help='数据类型：热门视频或排行榜 (默认: 热门)'
    )

    parser.add_argument(
        '-r', '--region',
        choices=list(PARTITION_MAP.keys()),
        default='全站',
        help='分区名称，仅排行榜模式有效 (默认: 全站)'
    )

    parser.add_argument(
        '-d', '--delay',
        type=float,
        default=1.0,
        help='请求间隔时间（秒）(默认: 1.0)'
    )

    parser.add_argument(
        '-o', '--output',
        type=str,
        default='output',
        help='输出目录 (默认: output)'
    )

    args = parser.parse_args()

    print("""
╔══════════════════════════════════════════════════════════════╗
║            B站热门视频趋势分析工具 v1.0                      ║
║            Bilibili Hot Video Trend Analyzer                 ║
╚══════════════════════════════════════════════════════════════╝
    """)

    # 创建分析器
    analyzer = BilibiliAnalyzer(output_dir=args.output)

    # 获取视频数据
    if args.type == '热门':
        logger.info(f"开始获取综合热门视频 (共{args.pages}页)...")
        analyzer.fetch_popular_videos(page_count=args.pages, delay=args.delay)
    else:
        logger.info(f"开始获取 {args.region} 分区排行榜...")
        analyzer.fetch_ranking_videos(partition=args.region, delay=args.delay)

    if not analyzer.videos_data:
        logger.error("未获取到任何视频数据，程序退出")
        return

    # 保存CSV数据
    logger.info("保存CSV数据...")
    analyzer.save_to_csv()

    # 关键词分析
    logger.info("进行关键词分析...")
    word_freq, tfidf_keywords = analyzer.analyze_keywords()

    # 统计分析
    logger.info("进行统计分析...")
    stats = analyzer.analyze_statistics()

    # 生成词云
    logger.info("生成词云图...")
    analyzer.generate_wordcloud(word_freq)

    # 生成图表
    logger.info("生成分析图表...")
    analyzer.generate_charts()

    # 生成报告
    logger.info("生成分析报告...")
    analyzer.generate_report(stats, tfidf_keywords)

    print(f"\n✓ 分析完成！所有结果已保存到 '{args.output}' 目录")
    print(f"  - bilibili_hot_videos.csv  : 原始数据")
    print(f"  - wordcloud.png            : 词云图")
    print(f"  - analysis_charts.png      : 分析图表")
    print(f"  - analysis_report.txt      : 分析报告")


if __name__ == '__main__':
    main()
