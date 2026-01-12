"""
从jsonl数据集文件里面随机抽取1000条数据
"""

import json
import random

input_file = "output.jsonl"
output_file = "split_1000.jsonl"
n_samples = 1000

# 读取所有行
with open(input_file, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 随机抽样（若总行数 < 1000，则全部保留）
sample_lines = random.sample(lines, min(n_samples, len(lines)))

# 写入新文件
with open(output_file, 'w', encoding='utf-8') as f:
    f.writelines(sample_lines)

print(f"已抽取 {len(sample_lines)} 条数据到 {output_file}")
