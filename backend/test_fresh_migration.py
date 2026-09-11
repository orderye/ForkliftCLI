import tempfile, os, sqlite3, subprocess, sys

# 创建一个全新的临时SQLite数据库
temp_db_path = '/tmp/temp_forklift_bao.db'
if os.path.exists(temp_db_path):
    os.remove(temp_db_path)

# First, create the base tables using SQLAlchemy (to avoid initial migration issues)
cmd1 = """
import sys
sys.path.insert(0, '.')
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base

Base = declarative_base()

# Just create all tables in the base
engine = create_engine('sqlite:///./temp_forklift_bao.db')
Base.metadata.create_all(engine)
print('Base tables created successfully')
engine.dispose()
"""

print('=== 步骤 1：创建基础表 ===')
result1 = subprocess.run([sys.executable, '-c', cmd1], capture_output=True, text=True, cwd='/Volumes/aigo S7 Med/ForkliftCLI/backend')
print(result1.stdout)
if result1.returncode != 0:
    print('错误:', result1.stderr)
    sys.exit(1)

# Now run Alembic migration
print('\n=== 步骤 2：执行 Alembic 升级 ===')
env = {'DATABASE_URL': f'sqlite:///{temp_db_path}', **dict(os.environ)}

cmd2 = """
import sys
sys.path.insert(0, '.')
from alembic.config import Config
from alembic import command

cfg = Config('alembic.ini')
cfg.set_main_option('sqlalchemy.url', 'sqlite:///./temp_forklift_bao.db')

print('开始升级到 head...')
command.upgrade(cfg, 'head')
print('升级完成！')
"""

result2 = subprocess.run([sys.executable, '-c', cmd2], capture_output=True, text=True, env=env, cwd='/Volumes/aigo S7 Med/ForkliftCLI/backend')
print(result2.stdout)
if result2.returncode != 0:
    print('错误:', result2.stderr[:500])
    sys.exit(1)

# Check results
print('\n=== 步骤 3：验证迁移结果 ===')
cmd3 = """
import sqlite3

conn = sqlite3.connect('/tmp/temp_forklift_bao.db')
tables = [row[0] for row in conn.execute("select name from sqlite_master where type='table' order by name")]
print(f'表: {len(tables)}')
for t in tables:
    cols = conn.execute(f"pragma table_info('{t}')").fetchall()
    print(f'  {t}: {len(cols)} 列')
    for col in cols:
        print(f'    {col[1]} {col[2]}')
    if t == 'alembic_version':
        print('   内容:', conn.execute(f"select * from {t}").fetchall())

conn.close()
"""

result3 = subprocess.run([sys.executable, '-c', cmd3], capture_output=True, text=True, cwd='/Volumes/aigo S7 Med/ForkliftCLI/backend')
print(result3.stdout)