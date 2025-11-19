#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
B站热门视频数据库模块
SQLite轻量级数据库，用于存储和查询历史数据
"""

import sqlite3
import os
import json
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

# 默认数据库路径
DEFAULT_DB_PATH = 'output/bilibili_data.db'


class BilibiliDatabase:
    """B站数据存储数据库"""

    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        """
        初始化数据库连接

        Args:
            db_path: 数据库文件路径
        """
        # 确保目录存在
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)

        self.db_path = db_path
        self._init_database()

    def _get_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # 支持字典式访问
        return conn

    def _init_database(self):
        """初始化数据库表结构"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # 爬取记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS crawl_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                crawl_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                data_type VARCHAR(50) NOT NULL,
                partition_name VARCHAR(50),
                video_count INTEGER DEFAULT 0,
                status VARCHAR(20) DEFAULT 'success'
            )
        ''')

        # 视频数据表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS videos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                crawl_id INTEGER,
                bvid VARCHAR(20) NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                view_count INTEGER DEFAULT 0,
                like_count INTEGER DEFAULT 0,
                coin_count INTEGER DEFAULT 0,
                favorite_count INTEGER DEFAULT 0,
                share_count INTEGER DEFAULT 0,
                reply_count INTEGER DEFAULT 0,
                danmaku_count INTEGER DEFAULT 0,
                pub_time TIMESTAMP,
                duration INTEGER DEFAULT 0,
                up_name VARCHAR(100),
                up_mid VARCHAR(50),
                partition_name VARCHAR(50),
                pic_url TEXT,
                video_url TEXT,
                crawl_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (crawl_id) REFERENCES crawl_records(id)
            )
        ''')

        # 创建索引以加速查询
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_videos_bvid ON videos(bvid)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_videos_crawl_id ON videos(crawl_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_videos_crawl_time ON videos(crawl_time)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_videos_up_name ON videos(up_name)')

        # 关键词统计表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS keywords (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                crawl_id INTEGER,
                keyword VARCHAR(100) NOT NULL,
                frequency INTEGER DEFAULT 0,
                tfidf_weight REAL DEFAULT 0,
                crawl_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (crawl_id) REFERENCES crawl_records(id)
            )
        ''')

        cursor.execute('CREATE INDEX IF NOT EXISTS idx_keywords_crawl_id ON keywords(crawl_id)')

        conn.commit()
        conn.close()

        logger.info(f"数据库初始化完成: {self.db_path}")

    def save_crawl_record(self, data_type: str, partition_name: str = None,
                         video_count: int = 0, status: str = 'success') -> int:
        """
        保存爬取记录

        Args:
            data_type: 数据类型 (popular/ranking)
            partition_name: 分区名称
            video_count: 视频数量
            status: 状态

        Returns:
            记录ID
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO crawl_records (data_type, partition_name, video_count, status)
            VALUES (?, ?, ?, ?)
        ''', (data_type, partition_name, video_count, status))

        crawl_id = cursor.lastrowid
        conn.commit()
        conn.close()

        logger.info(f"保存爬取记录: ID={crawl_id}, type={data_type}, count={video_count}")
        return crawl_id

    def save_videos(self, videos: List[Dict], crawl_id: int = None) -> int:
        """
        批量保存视频数据

        Args:
            videos: 视频数据列表
            crawl_id: 关联的爬取记录ID

        Returns:
            保存的视频数量
        """
        if not videos:
            return 0

        conn = self._get_connection()
        cursor = conn.cursor()

        count = 0
        for video in videos:
            try:
                cursor.execute('''
                    INSERT INTO videos (
                        crawl_id, bvid, title, description, view_count, like_count,
                        coin_count, favorite_count, share_count, reply_count,
                        danmaku_count, pub_time, duration, up_name, up_mid,
                        partition_name, pic_url, video_url
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    crawl_id,
                    video.get('bvid', ''),
                    video.get('title', ''),
                    video.get('desc', ''),
                    video.get('view', 0),
                    video.get('like', 0),
                    video.get('coin', 0),
                    video.get('favorite', 0),
                    video.get('share', 0),
                    video.get('reply', 0),
                    video.get('danmaku', 0),
                    video.get('pub_time', ''),
                    video.get('duration', 0),
                    video.get('up_name', ''),
                    video.get('up_mid', ''),
                    video.get('tname', ''),
                    video.get('pic', ''),
                    video.get('url', '')
                ))
                count += 1
            except Exception as e:
                logger.error(f"保存视频失败: {video.get('bvid', 'unknown')} - {e}")

        conn.commit()
        conn.close()

        logger.info(f"保存 {count} 个视频到数据库")
        return count

    def save_keywords(self, keywords: List[Tuple[str, float]], crawl_id: int = None) -> int:
        """
        保存关键词统计

        Args:
            keywords: 关键词列表 [(word, weight), ...]
            crawl_id: 关联的爬取记录ID

        Returns:
            保存的关键词数量
        """
        if not keywords:
            return 0

        conn = self._get_connection()
        cursor = conn.cursor()

        count = 0
        for word, weight in keywords:
            try:
                cursor.execute('''
                    INSERT INTO keywords (crawl_id, keyword, tfidf_weight)
                    VALUES (?, ?, ?)
                ''', (crawl_id, word, weight))
                count += 1
            except Exception as e:
                logger.error(f"保存关键词失败: {word} - {e}")

        conn.commit()
        conn.close()

        return count

    def get_crawl_records(self, limit: int = 20) -> List[Dict]:
        """
        获取爬取记录列表

        Args:
            limit: 返回数量限制

        Returns:
            爬取记录列表
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, crawl_time, data_type, partition_name, video_count, status
            FROM crawl_records
            ORDER BY crawl_time DESC
            LIMIT ?
        ''', (limit,))

        records = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return records

    def get_videos_by_crawl_id(self, crawl_id: int) -> List[Dict]:
        """
        根据爬取ID获取视频列表

        Args:
            crawl_id: 爬取记录ID

        Returns:
            视频列表
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM videos
            WHERE crawl_id = ?
            ORDER BY view_count DESC
        ''', (crawl_id,))

        videos = []
        for row in cursor.fetchall():
            video = dict(row)
            # 转换字段名以匹配原有格式
            videos.append({
                'bvid': video['bvid'],
                'title': video['title'],
                'desc': video['description'],
                'view': video['view_count'],
                'like': video['like_count'],
                'coin': video['coin_count'],
                'favorite': video['favorite_count'],
                'share': video['share_count'],
                'reply': video['reply_count'],
                'danmaku': video['danmaku_count'],
                'pub_time': video['pub_time'],
                'duration': video['duration'],
                'up_name': video['up_name'],
                'up_mid': video['up_mid'],
                'tname': video['partition_name'],
                'pic': video['pic_url'],
                'url': video['video_url']
            })

        conn.close()
        return videos

    def get_latest_videos(self, limit: int = 100) -> List[Dict]:
        """
        获取最新爬取的视频

        Args:
            limit: 返回数量限制

        Returns:
            视频列表
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # 获取最新的爬取记录ID
        cursor.execute('''
            SELECT id FROM crawl_records
            ORDER BY crawl_time DESC
            LIMIT 1
        ''')

        row = cursor.fetchone()
        conn.close()

        if row:
            return self.get_videos_by_crawl_id(row['id'])
        return []

    def get_video_history(self, bvid: str) -> List[Dict]:
        """
        获取单个视频的历史数据

        Args:
            bvid: 视频BV号

        Returns:
            历史数据列表
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT crawl_time, view_count, like_count, reply_count, danmaku_count
            FROM videos
            WHERE bvid = ?
            ORDER BY crawl_time ASC
        ''', (bvid,))

        history = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return history

    def get_top_ups(self, days: int = 7, limit: int = 20) -> List[Dict]:
        """
        获取指定天数内的热门UP主

        Args:
            days: 统计天数
            limit: 返回数量

        Returns:
            UP主统计列表
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT up_name, up_mid,
                   COUNT(DISTINCT bvid) as video_count,
                   SUM(view_count) as total_views,
                   AVG(view_count) as avg_views
            FROM videos
            WHERE crawl_time >= datetime('now', ?)
            GROUP BY up_name, up_mid
            ORDER BY total_views DESC
            LIMIT ?
        ''', (f'-{days} days', limit))

        ups = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return ups

    def get_trending_keywords(self, crawl_id: int = None, limit: int = 50) -> List[Dict]:
        """
        获取热门关键词

        Args:
            crawl_id: 爬取记录ID（为空则获取最新）
            limit: 返回数量

        Returns:
            关键词列表
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        if crawl_id:
            cursor.execute('''
                SELECT keyword, tfidf_weight
                FROM keywords
                WHERE crawl_id = ?
                ORDER BY tfidf_weight DESC
                LIMIT ?
            ''', (crawl_id, limit))
        else:
            # 获取最新的关键词
            cursor.execute('''
                SELECT keyword, tfidf_weight
                FROM keywords
                WHERE crawl_id = (SELECT MAX(crawl_id) FROM keywords)
                ORDER BY tfidf_weight DESC
                LIMIT ?
            ''', (limit,))

        keywords = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return keywords

    def get_statistics(self) -> Dict:
        """
        获取数据库统计信息

        Returns:
            统计信息字典
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        stats = {}

        # 总爬取次数
        cursor.execute('SELECT COUNT(*) FROM crawl_records')
        stats['total_crawls'] = cursor.fetchone()[0]

        # 总视频数
        cursor.execute('SELECT COUNT(*) FROM videos')
        stats['total_videos'] = cursor.fetchone()[0]

        # 独立视频数
        cursor.execute('SELECT COUNT(DISTINCT bvid) FROM videos')
        stats['unique_videos'] = cursor.fetchone()[0]

        # 独立UP主数
        cursor.execute('SELECT COUNT(DISTINCT up_name) FROM videos')
        stats['unique_ups'] = cursor.fetchone()[0]

        # 最近爬取时间
        cursor.execute('SELECT MAX(crawl_time) FROM crawl_records')
        stats['last_crawl'] = cursor.fetchone()[0]

        # 数据库文件大小
        if os.path.exists(self.db_path):
            stats['db_size'] = os.path.getsize(self.db_path)
        else:
            stats['db_size'] = 0

        conn.close()
        return stats

    def search_videos(self, keyword: str, limit: int = 50) -> List[Dict]:
        """
        搜索视频

        Args:
            keyword: 搜索关键词
            limit: 返回数量

        Returns:
            视频列表
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT DISTINCT bvid, title, up_name, view_count, like_count,
                   partition_name, pub_time, pic_url, video_url
            FROM videos
            WHERE title LIKE ? OR up_name LIKE ?
            ORDER BY view_count DESC
            LIMIT ?
        ''', (f'%{keyword}%', f'%{keyword}%', limit))

        videos = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return videos

    def cleanup_old_data(self, days: int = 30) -> int:
        """
        清理旧数据

        Args:
            days: 保留天数

        Returns:
            删除的记录数
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # 获取要删除的爬取记录ID
        cursor.execute('''
            SELECT id FROM crawl_records
            WHERE crawl_time < datetime('now', ?)
        ''', (f'-{days} days',))

        old_ids = [row[0] for row in cursor.fetchall()]

        if not old_ids:
            conn.close()
            return 0

        # 删除关联的视频和关键词
        placeholders = ','.join('?' * len(old_ids))
        cursor.execute(f'DELETE FROM videos WHERE crawl_id IN ({placeholders})', old_ids)
        cursor.execute(f'DELETE FROM keywords WHERE crawl_id IN ({placeholders})', old_ids)
        cursor.execute(f'DELETE FROM crawl_records WHERE id IN ({placeholders})', old_ids)

        deleted = len(old_ids)
        conn.commit()
        conn.close()

        logger.info(f"清理了 {deleted} 条旧数据")
        return deleted


# 环境变量控制是否启用数据库
DB_ENABLED = os.environ.get('BILIBILI_DB_ENABLED', 'true').lower() == 'true'

# 全局数据库实例
_db_instance = None


def get_database() -> Optional[BilibiliDatabase]:
    """获取数据库实例（单例模式）"""
    global _db_instance

    if not DB_ENABLED:
        return None

    if _db_instance is None:
        _db_instance = BilibiliDatabase()

    return _db_instance
