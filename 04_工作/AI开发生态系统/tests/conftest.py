"""
pytest configuration
"""

import pytest
import sys
import os

# 确保 src 目录在路径中
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))