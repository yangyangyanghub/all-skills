import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts'))
sys.argv = ['inspect_data.py', '--data', r'E:\BaiduNetdiskDownload\制图Data\制图Data\Data2\城市关系强度图']
from inspect_data import main
main()
