#!/usr/bin/env python
"""测试数据库连接"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
from urllib.parse import urlparse
from sqlalchemy import text
from app import create_app, db
import pymysql

def test_db_connection():
    try:
        project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        load_dotenv()
        load_dotenv(os.path.join(project_dir, '.env'))
        db_url = os.getenv('DEV_DATABASE_URL') or os.getenv('VISIRAY_DATABASE_URL')
        if not db_url:
            print('未找到数据库URL环境变量')
            return
        parsed = urlparse(db_url)
        user = parsed.username
        password = parsed.password
        host = parsed.hostname
        port = parsed.port or 3306
        database = parsed.path.lstrip('/')
        conn = pymysql.connect(host=host, port=port, user=user, password=password, database=database, charset='utf8mb4')
        cur = conn.cursor()
        cur.execute('SELECT 1')
        print('pymysql SELECT 1:', cur.fetchone())
        cur.close()
        conn.close()
        app = create_app()
        with app.app_context():
            r = db.session.execute(text('SELECT 1'))
            print('sqlalchemy SELECT 1:', list(r))
    except Exception as e:
        print(f'数据库连接失败: {e}')

if __name__ == '__main__':
    test_db_connection()