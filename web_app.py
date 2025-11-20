#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
B站热门视频趋势分析 - Web可视化界面
Bilibili Hot Video Trend Analyzer - Web Dashboard

使用Flask提供Web界面，使用ECharts进行数据可视化
"""

from flask import Flask, render_template, jsonify, request
import pandas as pd
import jieba
import jieba.analyse
from collections import Counter
from datetime import datetime
import time
import requests
import json
import re
import os
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 环境变量配置
# BILIBILI_AUTO_SAVE: 是否自动保存爬取的原始数据 (true/false，默认true)
AUTO_SAVE_ENABLED = os.environ.get('BILIBILI_AUTO_SAVE', 'true').lower() == 'true'

# 导入数据库模块
from database import get_database

app = Flask(__name__)

# B站API配置
BILIBILI_API = {
    'popular': 'https://api.bilibili.com/x/web-interface/popular',
    'ranking': 'https://api.bilibili.com/x/web-interface/ranking/v2',
}

# 分区ID映射
PARTITION_MAP = {
    '全站': 0, '动画': 1, '音乐': 3, '舞蹈': 129, '游戏': 4,
    '知识': 36, '科技': 188, '运动': 234, '汽车': 223, '生活': 160,
    '美食': 211, '动物圈': 217, '鬼畜': 119, '时尚': 155, '资讯': 202,
    '娱乐': 5, '影视': 181, '纪录片': 177, '电影': 23, '电视剧': 11,
}

# 停用词
STOP_WORDS = set([
    '的', '了', '是', '在', '我', '有', '和', '就', '不', '人', '都', '一', '一个',
    '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好',
    '自己', '这', '那', '他', '她', '它', '这个', '那个', '什么', '怎么', '为什么',
    '哪里', '这里', '那里', '如何', '可以', '能', '想', '让', '把', '被', '从',
    '第一', '第二', '第三', '视频', 'BV', 'av', 'UP', 'up'
])

# 缓存配置
CACHE_DIR = 'output'
CACHE_FILE = os.path.join(CACHE_DIR, 'web_cache.json')

# 全局缓存
cache = {
    'videos': [],
    'last_fetch': None,
    'fetch_type': None
}

def load_cache_from_file():
    """从文件加载缓存"""
    global cache
    try:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                cache = json.load(f)
            logger.info(f"从缓存文件加载数据: {len(cache.get('videos', []))} 个视频")
            return True
    except Exception as e:
        logger.error(f"加载缓存失败: {e}")
    return False

def save_cache_to_file():
    """保存缓存到文件"""
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
        logger.info("缓存已保存到文件")
    except Exception as e:
        logger.error(f"保存缓存失败: {e}")


def auto_save_raw_data(videos, data_type='popular'):
    """自动保存原始数据到本地"""
    if not AUTO_SAVE_ENABLED:
        return

    if not videos:
        return

    output_dir = 'output'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    json_filename = f"raw_data_{data_type}_{timestamp}.json"
    json_path = os.path.join(output_dir, json_filename)

    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump({
            'fetch_time': timestamp,
            'data_type': data_type,
            'count': len(videos),
            'videos': videos
        }, f, ensure_ascii=False, indent=2)

    logger.info(f"原始数据已自动保存: {json_path}")


def fetch_videos(data_type='popular', pages=5, partition='全站', delay=0.5):
    """获取B站视频数据"""
    videos = []
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://www.bilibili.com/',
        'Origin': 'https://www.bilibili.com',
    })

    if data_type == 'popular':
        for page in range(1, pages + 1):
            try:
                response = session.get(
                    BILIBILI_API['popular'],
                    params={'ps': 20, 'pn': page},
                    timeout=10
                )
                data = response.json()
                if data['code'] == 0:
                    for video in data['data']['list']:
                        videos.append(extract_video_info(video))
                if page < pages:
                    time.sleep(delay)
            except Exception as e:
                logger.error(f"获取第{page}页失败: {e}")
    else:
        # 排行榜API不支持分页，只能获取固定数量（约100个）
        try:
            tid = PARTITION_MAP.get(partition, 0)
            # 排行榜API需要特定的Referer
            session.headers.update({
                'Referer': 'https://www.bilibili.com/v/popular/rank/all'
            })

            logger.info(f"注意：排行榜API只返回固定数量的视频（约100个），不支持分页")

            response = session.get(
                BILIBILI_API['ranking'],
                params={'rid': tid, 'type': 'all'},
                timeout=10
            )
            data = response.json()
            if data['code'] == 0:
                for video in data['data']['list']:
                    videos.append(extract_video_info(video))
                logger.info(f"排行榜获取成功：{len(videos)} 个视频")
            else:
                logger.error(f"排行榜API返回错误: code={data['code']}, message={data.get('message', '未知')}")
        except Exception as e:
            logger.error(f"获取排行榜失败: {e}", exc_info=True)

    return videos


def extract_video_info(video):
    """提取视频信息"""
    stat = video.get('stat', {})
    owner = video.get('owner', {})
    pub_timestamp = video.get('pubdate', 0)

    # 将图片URL从HTTP转换为HTTPS，避免混合内容警告
    pic_url = video.get('pic', '')
    if pic_url.startswith('http://'):
        pic_url = pic_url.replace('http://', 'https://', 1)

    return {
        'bvid': video.get('bvid', ''),
        'title': video.get('title', ''),
        'desc': video.get('desc', ''),
        'view': stat.get('view', 0),
        'like': stat.get('like', 0),
        'coin': stat.get('coin', 0),
        'favorite': stat.get('favorite', 0),
        'share': stat.get('share', 0),
        'reply': stat.get('reply', 0),
        'danmaku': stat.get('danmaku', 0),
        'pub_time': datetime.fromtimestamp(pub_timestamp).strftime('%Y-%m-%d %H:%M'),
        'duration': video.get('duration', 0),
        'up_name': owner.get('name', ''),
        'up_mid': owner.get('mid', ''),
        'tname': video.get('tname', ''),
        'pic': pic_url,
        'url': f"https://www.bilibili.com/video/{video.get('bvid', '')}"
    }


def analyze_keywords(videos, top_n=100):
    """分析关键词"""
    all_text = ' '.join([v['title'] + ' ' + v.get('desc', '') for v in videos])
    words = jieba.cut(all_text)
    filtered = [w for w in words if len(w) > 1 and w not in STOP_WORDS and not w.isdigit()]
    word_freq = Counter(filtered)
    tfidf = jieba.analyse.extract_tags(all_text, topK=top_n, withWeight=True)
    return word_freq.most_common(top_n), tfidf


def analyze_statistics(videos):
    """统计分析"""
    df = pd.DataFrame(videos)

    return {
        'total': len(df),
        'view_stats': {
            'mean': int(df['view'].mean()),
            'median': int(df['view'].median()),
            'max': int(df['view'].max()),
            'min': int(df['view'].min())
        },
        'like_stats': {
            'mean': int(df['like'].mean()),
            'max': int(df['like'].max())
        },
        'reply_stats': {
            'mean': int(df['reply'].mean()),
            'max': int(df['reply'].max())
        },
        'engagement_rate': round(
            ((df['like'] + df['coin'] + df['favorite'] + df['share']) / df['view'] * 100).mean(), 2
        ),
        'top_videos': df.nlargest(20, 'view')[['title', 'view', 'like', 'up_name', 'pic', 'url']].to_dict('records'),
        'partition_dist': df['tname'].value_counts().head(15).to_dict(),
        'top_ups': df.groupby('up_name')['view'].sum().nlargest(10).to_dict(),
        'interaction_rates': {
            'like_rate': round((df['like'] / df['view'] * 100).mean(), 2),
            'coin_rate': round((df['coin'] / df['view'] * 100).mean(), 2),
            'favorite_rate': round((df['favorite'] / df['view'] * 100).mean(), 2),
            'share_rate': round((df['share'] / df['view'] * 100).mean(), 2)
        }
    }


@app.route('/')
def index():
    """主页"""
    return render_template('index.html', partitions=list(PARTITION_MAP.keys()))


@app.route('/api/fetch', methods=['POST'])
def api_fetch():
    """获取数据API"""
    data = request.json
    data_type = data.get('type', 'popular')
    pages = min(int(data.get('pages', 5)), 20)
    partition = data.get('partition', '全站')

    logger.info(f"开始获取数据: type={data_type}, pages={pages}, partition={partition}")

    videos = fetch_videos(data_type, pages, partition)

    if videos:
        cache['videos'] = videos
        cache['last_fetch'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cache['fetch_type'] = f"{data_type}-{partition}" if data_type == 'ranking' else data_type

        # 保存缓存到文件
        save_cache_to_file()

        # 自动保存原始数据
        save_type = f"{data_type}_{partition}" if data_type == 'ranking' else data_type
        auto_save_raw_data(videos, save_type)

        # 保存到数据库
        db = get_database()
        if db:
            partition_name = partition if data_type == 'ranking' else None
            crawl_id = db.save_crawl_record(data_type, partition_name, len(videos))
            db.save_videos(videos, crawl_id)
            cache['crawl_id'] = crawl_id

        return jsonify({
            'success': True,
            'count': len(videos),
            'message': f'成功获取 {len(videos)} 个视频'
        })
    else:
        return jsonify({
            'success': False,
            'message': '获取数据失败，请稍后重试'
        })


@app.route('/api/analysis')
def api_analysis():
    """获取分析结果API"""
    if not cache['videos']:
        return jsonify({'success': False, 'message': '请先获取数据'})

    videos = cache['videos']
    word_freq, tfidf = analyze_keywords(videos)
    stats = analyze_statistics(videos)

    # 准备词云数据
    wordcloud_data = [{'name': w, 'value': c} for w, c in word_freq[:100]]

    # 准备TF-IDF关键词
    keywords = [{'word': w, 'weight': round(s, 4)} for w, s in tfidf[:30]]

    return jsonify({
        'success': True,
        'fetch_time': cache['last_fetch'],
        'fetch_type': cache['fetch_type'],
        'stats': stats,
        'wordcloud': wordcloud_data,
        'keywords': keywords,
        'videos': videos
    })


@app.route('/api/export')
def api_export():
    """导出CSV"""
    if not cache['videos']:
        return jsonify({'success': False, 'message': '没有数据可导出'})

    df = pd.DataFrame(cache['videos'])
    output_dir = 'output'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    filename = f"bilibili_hot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    filepath = os.path.join(output_dir, filename)
    df.to_csv(filepath, index=False, encoding='utf-8-sig')

    return jsonify({
        'success': True,
        'message': f'数据已导出到 {filepath}',
        'filename': filename
    })


@app.route('/api/history')
def api_history():
    """获取历史爬取记录"""
    db = get_database()
    if not db:
        return jsonify({'success': False, 'message': '数据库未启用'})

    limit = request.args.get('limit', 20, type=int)
    records = db.get_crawl_records(limit)

    return jsonify({
        'success': True,
        'records': records
    })


@app.route('/api/history/<int:crawl_id>')
def api_history_detail(crawl_id):
    """获取指定爬取记录的详细数据"""
    db = get_database()
    if not db:
        return jsonify({'success': False, 'message': '数据库未启用'})

    videos = db.get_videos_by_crawl_id(crawl_id)
    keywords = db.get_trending_keywords(crawl_id)

    return jsonify({
        'success': True,
        'videos': videos,
        'keywords': keywords
    })


@app.route('/api/stats')
def api_stats():
    """获取数据库统计信息"""
    db = get_database()
    if not db:
        return jsonify({'success': False, 'message': '数据库未启用'})

    stats = db.get_statistics()

    return jsonify({
        'success': True,
        'stats': stats
    })


@app.route('/api/search')
def api_search():
    """搜索历史视频"""
    db = get_database()
    if not db:
        return jsonify({'success': False, 'message': '数据库未启用'})

    keyword = request.args.get('q', '')
    if not keyword:
        return jsonify({'success': False, 'message': '请提供搜索关键词'})

    videos = db.search_videos(keyword)

    return jsonify({
        'success': True,
        'videos': videos,
        'count': len(videos)
    })


@app.route('/api/top-ups')
def api_top_ups():
    """获取热门UP主"""
    db = get_database()
    if not db:
        return jsonify({'success': False, 'message': '数据库未启用'})

    days = request.args.get('days', 7, type=int)
    limit = request.args.get('limit', 20, type=int)
    ups = db.get_top_ups(days, limit)

    return jsonify({
        'success': True,
        'ups': ups
    })


if __name__ == '__main__':
    # 创建模板目录
    if not os.path.exists('templates'):
        os.makedirs('templates')

    # 加载缓存数据
    if load_cache_from_file():
        print(f"✅ 已从缓存加载 {len(cache.get('videos', []))} 个视频数据")
    else:
        print("ℹ️  未找到缓存数据，需要重新获取")

    print("""
╔══════════════════════════════════════════════════════════════╗
║        B站热门视频趋势分析 - Web可视化界面                   ║
║        Bilibili Hot Video Analyzer - Web Dashboard           ║
╚══════════════════════════════════════════════════════════════╝

启动Web服务器...
访问地址: http://localhost:5000
    """)

    app.run(debug=True, host='0.0.0.0', port=5000)
