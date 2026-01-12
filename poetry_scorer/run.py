#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
诗词评分工具运行脚本
提供命令行交互界面，方便用户使用各种功能
"""

import sys
import os
import argparse

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from poetry_scorer_jiujiu import PoetryScorer
from poetry_quality_extractor import PoetryQualityExtractor


def main():
    """主函数，提供命令行交互界面"""
    parser = argparse.ArgumentParser(description='诗词评分工具运行脚本')

    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    # 评分命令
    score_parser = subparsers.add_parser('score', help='对诗词进行格律评分')
    score_parser.add_argument('input_file', help='输入JSON/JSONL文件路径')
    score_parser.add_argument('--detailed-output', help='详细得分输出文件路径')
    score_parser.add_argument('--summary-output', help='综合得分输出文件路径')
    score_parser.add_argument('--save-detailed', default="false", choices=['true', 'false'],
                              help='是否保存详细得分文件 (默认: false)')
    score_parser.add_argument('--save-summary', default="true", choices=['true', 'false'],
                              help='是否保存综合得分文件 (默认: true)')
    score_parser.add_argument('--poem-field', default='prediction', help='诗句字段名 (默认: prediction)')
    score_parser.add_argument('--instruct-field', default='instruct', help='指令字段名 (默认: instruct)')
    score_parser.add_argument('--is-jsonl', action='store_true', help='输入文件为JSONL格式')
    score_parser.add_argument('--rhyme-system', default='pingshui', choices=['pingshui', 'xin', 'tong'],
                              help='韵书系统选择 (默认: pingshui)')

    # 提取命令
    extract_parser = subparsers.add_parser('extract', help='提取优质诗词数据')
    extract_parser.add_argument('input_file', help='输入JSON/JSONL文件路径')
    extract_parser.add_argument('output_file', help='输出文件路径')
    extract_parser.add_argument('--poem-field', default='content', help='诗句字段名 (默认: content)')
    extract_parser.add_argument('--instruct-field', default='instruct', help='指令字段名 (默认: instruct)')
    extract_parser.add_argument('--keep-fields', nargs='+', default=['instruct', 'title', 'content', 'dynasty', 'author' ],
                                help='需要保留到输出文件的字段列表')
    extract_parser.add_argument('--max-five-quatrain', type=int, default=1000, help='五言绝句最大输出数量 (默认: 1000)')
    extract_parser.add_argument('--max-seven-quatrain', type=int, default=1000, help='七言绝句最大输出数量 (默认: 1000)')
    extract_parser.add_argument('--max-five-regulated', type=int, default=1000, help='五言律诗最大输出数量 (默认: 1000)')
    extract_parser.add_argument('--max-seven-regulated', type=int, default=1000, help='七言律诗最大输出数量 (默认: 1000)')
    extract_parser.add_argument('--is-jsonl', action='store_true', help='输入文件为JSONL格式')
    extract_parser.add_argument('--rhyme-system', default='pingshui', choices=['pingshui', 'xin', 'tong'],
                                help='韵书系统选择 (默认: pingshui)')

    # 测试命令
    test_parser = subparsers.add_parser('test', help='运行测试')

    args = parser.parse_args()

    # 处理命令
    if args.command == 'score':
        print("运行诗词评分功能...")

        # 设置默认输出文件名
        save_detailed = args.save_detailed.lower() == "true"
        save_summary = args.save_summary.lower() == "true"
        detailed_output = args.detailed_output or ""
        summary_output = args.summary_output or ""

        if not detailed_output and save_detailed:
            base_name = os.path.splitext(os.path.basename(args.input_file))[0]
            detailed_output = f"{base_name}_detailed.json"

        if not summary_output and save_summary:
            base_name = os.path.splitext(os.path.basename(args.input_file))[0]
            summary_output = f"{base_name}_summary.json"

        scorer = PoetryScorer()
        scorer.process_file(
            args.input_file,
            detailed_output,
            summary_output,
            args.poem_field,
            args.instruct_field,
            args.is_jsonl,
            args.rhyme_system,
            save_detailed,
            save_summary
        )

    elif args.command == 'extract':
        print("运行优质诗词提取功能...")

        max_per_category = {
            'five_quatrain': args.max_five_quatrain,
            'seven_quatrain': args.max_seven_quatrain,
            'eight_five': args.max_five_regulated,
            'eight_seven': args.max_seven_regulated
        }

        extractor = PoetryQualityExtractor(args.rhyme_system)
        extractor.process_dataset(
            args.input_file,
            args.poem_field,
            args.instruct_field,
            args.output_file,
            max_per_category,
            args.keep_fields,
            args.is_jsonl
        )

    elif args.command == 'test':
        print("运行测试...")

        # 直接运行测试脚本
        import subprocess
        result = subprocess.run([sys.executable, 'test_scorer.py'])
        sys.exit(result.returncode)

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
