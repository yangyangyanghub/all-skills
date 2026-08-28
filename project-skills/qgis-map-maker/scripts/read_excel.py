# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')

import pandas as pd

excel_path = r'E:\BaiduNetdiskDownload\制图Data\制图Data\Data2\城市关系强度图\城市关系强度.xlsx'
df = pd.read_excel(excel_path)

print(f"行数: {len(df)}")
print(f"列名: {df.columns.tolist()}")
print(f"\n前10行:")
print(df.head(10).to_string())
print(f"\n数据类型:\n{df.dtypes}")
