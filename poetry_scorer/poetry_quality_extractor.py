#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
优质诗词数据提取工具
根据格律评分对数据集进行分类、排序和筛选
调用命令：
python poetry_quality_extractor.py split2_1000.jsonl split2_1000_filtered.json \
  --poem-field content \
  --instruct-field instruct \
  --keep-fields title content dynasty author instruct \
  --max-five-quatrain 200 \
  --max-seven-quatrain 200 \
  --max-five-regulated 100 \
  --max-seven-regulated 100 \
  --is-jsonl
"""

import json
import os
import sys
import argparse
from collections import defaultdict

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from poetry_scorer_jiujiu import PoetryScorer, extract_chinese


class PoetryQualityExtractor:
    """优质诗词提取器"""

    def __init__(self, rhyme_system='pingshui'):
        self.scorer = PoetryScorer()
        self.rhyme_system = rhyme_system
        # 四个类别：五言绝句、七言绝句、五言律诗、七言律诗
        self.categories = {
            'five_quatrain': {'name': '五言绝句', 'poem_type': '绝句', 'sentence_length': 5},
            'seven_quatrain': {'name': '七言绝句', 'poem_type': '绝句', 'sentence_length': 7},
            'eight_five': {'name': '五言律诗', 'poem_type': '律诗', 'sentence_length': 5},
            'eight_seven': {'name': '七言律诗', 'poem_type': '律诗', 'sentence_length': 7}
        }

    def parse_instruct(self, instruct: str) -> dict:
        """解析指令信息"""
        instruct_lower = instruct.lower()

        # 解析诗体
        poem_type = None
        if '绝句' in instruct_lower:
            poem_type = '绝句'
        elif '律诗' in instruct_lower:
            poem_type = '律诗'
        elif '排律' in instruct_lower:
            poem_type = '排律'

        # 解析句长
        sentence_length = None
        if '五言' in instruct_lower and '律诗' in instruct_lower:
            sentence_length = 5
        elif '七言' in instruct_lower and '律诗' in instruct_lower:
            sentence_length = 7
        elif '五言' in instruct_lower:
            sentence_length = 5
        elif '七言' in instruct_lower:
            sentence_length = 7

        # 自动检测句长
        if sentence_length is None:
            for key, value in self.categories.items():
                if value['name'] in instruct:
                    sentence_length = value['sentence_length']
                    poem_type = value['poem_type']
                    break

        return {
            'poem_type': poem_type,
            'sentence_length': sentence_length,
            'original_instruct': instruct
        }

    def process_dataset(self, input_file: str, poem_field: str, instruct_field: str,
                        output_file: str, max_per_category: dict, keep_fields: list,
                        is_jsonl: bool = False) -> dict:
        """处理数据集并提取优质数据"""
        try:
            # 读取输入文件
            if is_jsonl:
                dataset = self._read_jsonl_file(input_file)
            else:
                dataset = self._read_json_file(input_file)

            print(f"成功读取 {len(dataset)} 条数据")

            # 分类数据
            categorized_data = defaultdict(list)
            total_scored = 0

            for item in dataset:
                # 诗句和格律字段的可选名称列表
                # 兼容多种常见命名方式
                poem_field_candidates = [poem_field, "prediction", "text", "content", "poem", "poetry"]
                instruct_field_candidates = [instruct_field, "instruct", "prompt", "type", "poem_type", "format"]

                # 查找实际存在的字段
                actual_poem_field = None
                for field in poem_field_candidates:
                    if field in item:
                        actual_poem_field = field
                        break

                actual_instruct_field = None
                for field in instruct_field_candidates:
                    if field in item:
                        actual_instruct_field = field
                        break

                if not actual_poem_field:
                    print(f"警告: 在记录中未找到诗句字段（尝试的字段: {poem_field_candidates}）")
                    continue

                if not actual_instruct_field:
                    print(f"警告: 在记录中未找到格律字段（尝试的字段: {instruct_field_candidates}）")
                    continue

                poem = item[actual_poem_field]
                instruct = item[actual_instruct_field]

                # 评分
                score_result = self.scorer.score_poem(poem, instruct, self.rhyme_system)

                # 解析指令以确定类别
                instruct_info = self.parse_instruct(instruct)

                # 确定类别
                category = self._determine_category(poem, instruct_info)
                if category is None:
                    continue

                # 添加评分信息
                scored_item = {
                    'original_data': item,
                    'scores': score_result,
                    'total_score': (score_result['format_score'] +
                                    score_result['pingze_score'] +
                                    score_result['rhyme_score']) / 3,
                    'category': category,
                    'poem_length': len(extract_chinese(poem)),
                    'determined_category': self.categories[category]['name']
                }

                categorized_data[category].append(scored_item)
                total_scored += 1

                if total_scored % 100 == 0:
                    print(f"已处理 {total_scored} 条数据...")

            print(f"完成评分，共处理 {total_scored} 条数据")

            # 按类别统计
            for category, items in categorized_data.items():
                print(f"{self.categories[category]['name']}: {len(items)} 条")

                # 按分数排序（降序）
                items.sort(key=lambda x: x['total_score'], reverse=True)

                # 限制数量
                max_count = max_per_category.get(category, float('inf'))
                filtered_items = items[:max_count]
                categorized_data[category] = filtered_items

                print(f"  筛选后保留 {len(filtered_items)} 条")
                if filtered_items:
                    avg_score = sum(item['total_score'] for item in filtered_items) / len(filtered_items)
                    print(f"  平均分: {avg_score:.2f}")

                # 显示最高分的几首
                print(f"  前三名:")
                for i, item in enumerate(filtered_items[:3]):
                    print(f"    {i + 1}. 总分: {item['total_score']:.2f} - "
                          f"格式:{item['scores']['format_score']:.1f} "
                          f"平仄:{item['scores']['pingze_score']:.1f} "
                          f"押韵:{item['scores']['rhyme_score']:.1f}")
                    # 查找实际的诗句字段名
                    poem_content = ""
                    for field in ['text', 'content', 'poem', 'poetry', 'prediction']:
                        if field in item['original_data']:
                            poem_content = item['original_data'][field]
                            break
                    print(f"       诗句: {poem_content[:30]}...")

            # 生成筛选后的数据集
            filtered_dataset = self._create_filtered_dataset(categorized_data, keep_fields)

            # 根据输出文件的扩展名决定文件格式
            if output_file.endswith('.jsonl'):
                self._save_jsonl_file(filtered_dataset, output_file)
                print("输出格式: JSONL")
            else:
                self._save_json_file(filtered_dataset, output_file)
                print("输出格式: JSON")

            # 生成统计报告
            stats = self._generate_statistics(categorized_data, total_scored)

            # 保存统计报告
            stats_file = os.path.splitext(output_file)[0] + '_statistics.json'
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(stats, f, ensure_ascii=False, indent=2)

            print(f"\n筛选结果已保存到: {output_file}")
            print(f"统计报告已保存到: {stats_file}")

            return stats

        except Exception as e:
            print(f"处理数据集时出错: {e}")
            return {'error': str(e)}

    def _determine_category(self, poem: str, instruct_info: dict) -> str:
        """确定诗词的类别"""
        processed = extract_chinese(poem)
        poem_len = len(processed)

        # 预处理：如果长度为0，返回None
        if poem_len == 0:
            return None

        # 如果通过指令信息能明确确定类别
        for key, value in self.categories.items():
            if (instruct_info['poem_type'] == value['poem_type'] and
                    instruct_info['sentence_length'] == value['sentence_length']):
                return key

        # 根据实际内容自动判断
        if poem_len == 20:  # 5字×4句 = 绝句
            return 'five_quatrain'
        elif poem_len == 28:  # 7字×4句 = 绝句
            return 'seven_quatrain'
        elif poem_len == 40:  # 5字×8句 = 律诗
            return 'eight_five'
        elif poem_len == 56:  # 7字×8句 = 律诗
            return 'eight_seven'

        # 不符合标准格式
        return None

    def _read_json_file(self, file_path: str) -> list:
        """读取JSON文件"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if not isinstance(data, list):
            raise ValueError("输入文件应包含一个对象列表")

        return data

    def _read_jsonl_file(self, file_path: str) -> list:
        """读取JSONL文件"""
        data = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        item = json.loads(line)
                        data.append(item)
                    except json.JSONDecodeError:
                        continue

        return data

    def _create_filtered_dataset(self, categorized_data: dict, keep_fields: list) -> list:
        """创建筛选后的数据集，不包含评分信息"""
        filtered_dataset = []

        # 按特定顺序组合各类别数据
        category_order = ['five_quatrain', 'seven_quatrain', 'eight_five', 'eight_seven']

        for category in category_order:
            items = categorized_data.get(category, [])

            for item in items:
                # 创建新记录
                new_item = {}

                # 添加保留字段（诗句、格律字段和用户指定的其他字段）
                for field in keep_fields:
                    if field in item['original_data']:
                        new_item[field] = item['original_data'][field]

                filtered_dataset.append(new_item)

        return filtered_dataset

    def _save_json_file(self, data: list, file_path: str):
        """保存为JSON文件"""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _save_jsonl_file(self, data: list, file_path: str):
        """保存为JSONL文件"""
        with open(file_path, 'w', encoding='utf-8') as f:
            for item in data:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')

    def _generate_statistics(self, categorized_data: dict, total_scored: int) -> dict:
        """生成统计报告"""
        stats = {
            'total_processed': total_scored,
            'categories': {},
            'extraction_settings': self.categories,
            'rhyme_system': self.rhyme_system
        }

        for category, items in categorized_data.items():
            category_name = self.categories[category]['name']
            category_stats = {
                'count': len(items),
                'scores': {
                    'total': [],
                    'format': [],
                    'pingze': [],
                    'rhyme': []
                }
            }

            for item in items:
                category_stats['scores']['total'].append(round(item['total_score'], 2))
                category_stats['scores']['format'].append(round(item['scores']['format_score'], 2))
                category_stats['scores']['pingze'].append(round(item['scores']['pingze_score'], 2))
                category_stats['scores']['rhyme'].append(round(item['scores']['rhyme_score'], 2))

            # 计算均值
            category_stats['average_scores'] = {
                'total': round(sum(category_stats['scores']['total']) / len(category_stats['scores']['total']), 2) if
                category_stats['scores']['total'] else 0,
                'format': round(sum(category_stats['scores']['format']) / len(category_stats['scores']['format']), 2) if
                category_stats['scores']['format'] else 0,
                'pingze': round(sum(category_stats['scores']['pingze']) / len(category_stats['scores']['pingze']), 2) if
                category_stats['scores']['pingze'] else 0,
                'rhyme': round(sum(category_stats['scores']['rhyme']) / len(category_stats['scores']['rhyme']), 2) if
                category_stats['scores']['rhyme'] else 0
            }

            stats['categories'][category_name] = category_stats

        return stats


def main():
    parser = argparse.ArgumentParser(description='优质诗词数据提取工具')
    parser.add_argument('input_file', help='输入JSON/JSONL文件路径')
    parser.add_argument('output_file', help='输出文件路径')

    # 字段配置
    parser.add_argument('--poem-field', default='prediction', help='诗句字段名 (默认: prediction)')
    parser.add_argument('--instruct-field', default='instruct', help='指令字段名 (默认: instruct)')
    parser.add_argument('--keep-fields', nargs='+',
                        default=['prediction', 'instruct'],
                        help='需要保留到输出文件的字段列表，默认只保留诗句和格律字段 (默认: prediction instruct)')

    # 输出控制
    parser.add_argument('--max-five-quatrain', type=int, default=100,
                        help='五言绝句最大输出数量 (默认: 100)')
    parser.add_argument('--max-seven-quatrain', type=int, default=100,
                        help='七言绝句最大输出数量 (默认: 100)')
    parser.add_argument('--max-five-regulated', type=int, default=50,
                        help='五言律诗最大输出数量 (默认: 50)')
    parser.add_argument('--max-seven-regulated', type=int, default=50,
                        help='七言律诗最大输出数量 (默认: 50)')

    # 其他选项
    parser.add_argument('--is-jsonl', action='store_true', help='输入文件为JSONL格式')
    parser.add_argument('--rhyme-system', default='pingshui',
                        choices=['pingshui', 'xin', 'tong'],
                        help='韵书系统选择: pingshui(平水韵), xin(中华新韵), tong(中华通韵) (默认: pingshui)')

    args = parser.parse_args()

    # 设置每类最大数量
    max_per_category = {
        'five_quatrain': args.max_five_quatrain,
        'seven_quatrain': args.max_seven_quatrain,
        'eight_five': args.max_five_regulated,
        'eight_seven': args.max_seven_regulated
    }

    print("开始提取优质诗词数据...")
    print(f"韵书系统: {args.rhyme_system}")
    print(f"每类最大数量: 五言绝句({max_per_category['five_quatrain']}) "
          f"七言绝句({max_per_category['seven_quatrain']}) "
          f"五言律诗({max_per_category['eight_five']}) "
          f"七言律诗({max_per_category['eight_seven']})")

    # 创建提取器并处理数据
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

    print("\n数据提取完成!")


if __name__ == '__main__':
    main()