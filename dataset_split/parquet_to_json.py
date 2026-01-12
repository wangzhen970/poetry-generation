"""
将 Parquet 转为 JSONL（保留中文）
"""

import pandas as pd
import os

# 读取 Parquet
input_file = 'poem1.parquet'
if not os.path.exists(input_file):
    print(f"错误: 文件 '{input_file}' 不存在")
    print("请确保poem1.parquet文件存在于当前目录")
    exit(1)

df = pd.read_parquet(input_file)

# 转为 JSON，保留中文（不转义为 \uXXXX）
json_str = df.to_json(orient='records', lines=True, force_ascii=False)

# 写入文件（注意指定 encoding='utf-8'）
with open('output1.jsonl', 'w', encoding='utf-8') as f:
    f.write(json_str)
