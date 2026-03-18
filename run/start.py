# 主运行
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from run.report import test_report

if __name__ == '__main__':
    test_report()
