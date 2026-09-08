import sys
from pathlib import Path

# 让 pytest 能 import app.* 模块
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))