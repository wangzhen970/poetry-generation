#!/usr/bin/env python3
"""
向 JSONL 文件添加新字段

用法：
  # 添加固定值字段
  python add_field_to_jsonl.py split_1000.jsonl output.jsonl --field-name source --field-value ancient_poem
  # 添加来源标记
python add_field_to_jsonl.py split_1000.jsonl split_1000_system.jsonl \
  --field-name system \
  --field-value "
你是一位精通中国古典诗词的诗人。当用户要求你创作一首指定体裁的诗（如五言绝句、七言绝句、五言律诗、七言律诗等），你必须严格遵守以下规则：

1. **仅输出诗句本身**，不得包含标题（如《XXX》）、序号（如“其一”）、注释、赏析、解释、引导语（如“好的”“我写一首……”）或任何额外文字。
2. 诗句必须严格符合所要求的体裁格式：
   - 五言绝句：4行，每行5字；
   - 七言绝句：4行，每行7字；
   - 五言律诗：8行，每行5字；
   - 七言律诗：8行，每行7字。
3. 每行诗句独立成行，使用中文标点（如需），但不要添加引号、编号、XML标签（如 <think>）或任何非诗句内容。
4. 完成内部推理后，**直接输出最终诗句**，不得暴露思考过程。

请始终以最简洁、规范的方式输出符合古典格律的诗歌。
"


  # 基于现有字段动态生成（使用 Python 表达式）
  python add_field_to_jsonl.py input.jsonl output.jsonl --field-name full_title --expr "record.get('title', '') + '·' + record.get('dynasty', '')"

  # 同时添加多个字段（多次运行或修改脚本）
"""

import json
import argparse
import sys


def main():
    parser = argparse.ArgumentParser(description="向 JSONL 文件添加新字段")
    parser.add_argument("input", help="输入 JSONL 文件路径")
    parser.add_argument("output", help="输出 JSONL 文件路径")
    parser.add_argument("--field-name", required=True, help="新字段的名称")
    parser.add_argument("--field-value", default=None, help="新字段的固定值（字符串）")
    parser.add_argument("--expr", default=None, help="Python 表达式，用于动态生成字段值（使用变量 'record'）")
    parser.add_argument("--encoding", default="utf-8", help="文件编码（默认: utf-8）")

    args = parser.parse_args()

    if not (args.field_value is not None) ^ (args.expr is not None):
        print("错误：必须且只能指定 --field-value 或 --expr 之一", file=sys.stderr)
        sys.exit(1)

    with open(args.input, 'r', encoding=args.encoding) as fin, \
            open(args.output, 'w', encoding=args.encoding) as fout:

        for line_num, line in enumerate(fin, 1):
            line = line.strip()
            if not line:
                continue

            try:
                record = json.loads(line)
            except json.JSONDecodeError as e:
                print(f"警告：第 {line_num} 行 JSON 解析失败，跳过: {e}", file=sys.stderr)
                continue

            # 计算新字段值
            try:
                if args.field_value is not None:
                    new_value = args.field_value
                else:
                    # 使用 eval 执行表达式（注意：仅用于可信数据）
                    new_value = eval(args.expr, {"__builtins__": {}}, {"record": record})
            except Exception as e:
                print(f"警告：第 {line_num} 行计算字段 '{args.field_name}' 失败，跳过: {e}", file=sys.stderr)
                continue

            # 添加新字段
            record[args.field_name] = new_value

            # 写入输出
            fout.write(json.dumps(record, ensure_ascii=False) + '\n')

    print(f"✅ 已完成！新增字段 '{args.field_name}'，结果保存至: {args.output}")


if __name__ == "__main__":
    main()
