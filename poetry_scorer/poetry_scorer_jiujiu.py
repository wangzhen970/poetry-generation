#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
诗词格律评分工具
从格式、平仄和押韵三个维度进行评分
改进：加入对合法拗救的加分，拗救的字算作平仄正确
新特性：支持自定义字段名和JSONL文件格式，支持选择韵书体系，支持生成详细得分和综合得分文件
"""

import json
import re
import sys
import os
import argparse

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from shi.shi_rhythm import ShiRhythm
from rhythm.pingshui_rhythm import rhythm_name, rhythm_name_trad, rhythm_correspond
import rhythm.new_rhythm as nw


def extract_chinese(text: str, comma_remain=False) -> str:
    """删除输入文本中的非汉字部分以及括号内的部分"""
    # 首先删除括号及其中的内容
    text = re.sub(r'[(（].*?[)）]', '', text)
    hanzi_range = (r'\u2642\u2E80-\u2EFF\u2F00-\u2FDF\u4e00-\u9fff\u3400-\u4dbf\u3007\uF900-\uFAFF'
                   r'\U00020000-\U0002A6DF'
                   r'\U0002F800-\U0002FA1F')
    if comma_remain:
        punctuation = r',\.\?!:，。？！、：'
        pattern = re.compile(f'[{hanzi_range}{punctuation}]')
    else:
        pattern = re.compile(f'[{hanzi_range}]')
    filtered_text = ''.join(pattern.findall(text)).replace('\n', '')
    return filtered_text


class PoetryScorer:
    def __init__(self):
        # 自定义中文数字映射
        self.cn_nums = {'一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9, '十': 10}
        # 韵书字典
        self.rhyme_systems = {
            'pingshui': {'id': 1, 'name': '平水韵', 'field': 'rhyme_score_pingshui'},
            'xin': {'id': 2, 'name': '中华新韵', 'field': 'rhyme_score_xin'},
            'tong': {'id': 3, 'name': '中华通韵', 'field': 'rhyme_score_tong'}
        }

    def parse_instruct(self, instruct: str) -> dict:
        """解析instruct中的格律要求"""
        result = {'sentence_length': None, 'poem_type': None}

        # 解析句长
        if '五言' in instruct:
            result['sentence_length'] = 5
        elif '七言' in instruct:
            result['sentence_length'] = 7

        # 解析诗体
        if '绝句' in instruct:
            result['poem_type'] = '绝句'
        elif '律诗' in instruct:
            result['poem_type'] = '律诗'
        elif '排律' in instruct:
            result['poem_type'] = '排律'

        return result

    def check_format(self, poem: str, instruct: str) -> float:
        """格式评分"""
        instruct_info = self.parse_instruct(instruct)
        score = 0.0

        # 计算实际句长和诗体 - 清理文本后再计算
        processed_poem = extract_chinese(poem)
        poem_len = len(processed_poem)

        # 如果处理后长度为0（无中文字符），直接返回0分
        if poem_len == 0:
            return 0.0

        if poem_len % 5 == 0:
            actual_sentence_length = 5
            total_lines = poem_len // 5
        elif poem_len % 7 == 0:
            actual_sentence_length = 7
            total_lines = poem_len // 7
        else:
            return 0.0

        if total_lines == 4:
            actual_poem_type = '绝句'
        elif total_lines == 8:
            actual_poem_type = '律诗'
        else:
            actual_poem_type = '排律'

        # 句长评分（50分）
        if instruct_info['sentence_length'] == actual_sentence_length:
            score += 50

        # 诗体评分（50分）
        if instruct_info['poem_type'] == actual_poem_type:
            score += 50

        return score

    def analyze_pingze_result_with_jiujiu(self, result_text: str) -> tuple[int, int]:
        """分析平仄校验结果，返回(正确数, 总数)，包含拗救加分"""
        correct_count = 0
        total_count = 0

        lines = result_text.split("\n")

        # 解析拗救信息 - 查找报告中的拗救提示
        jiujiu_lines = set()  # 使用集合记录有拗救的句子位置信息

        # 遍历所有行，查找拗救提示
        for i, line in enumerate(lines):
            if "本联" in line and "拗句" in line:
                # 找到拗救提示，确定是哪一句
                if "本联上句" in line:
                    # 上一句有拗救，确定上一句的平仄标记行位置
                    jiujiu_line_idx = None
                    for j in range(i - 1, max(i - 5, 0), -1):
                        if any(symbol in lines[j] for symbol in ["〇", "◎", "●"]):
                            jiujiu_line_idx = j
                            break
                    if jiujiu_line_idx is not None:
                        jiujiu_lines.add(jiujiu_line_idx)

                elif "本联下句" in line:
                    # 下一句有拗救，确定下一句的平仄标记行位置
                    jiujiu_line_idx = None
                    for j in range(i - 1, max(i - 5, 0), -1):
                        if any(symbol in lines[j] for symbol in ["〇", "◎", "●"]):
                            jiujiu_line_idx = j + 1
                            break
                    if jiujiu_line_idx is not None:
                        jiujiu_lines.add(jiujiu_line_idx)

        # 统计平仄符号和拗救
        pingze_lines = []  # 记录平仄符号行的索引
        for i, line in enumerate(lines):
            # 检查是否是平仄标记行（包含〇、◎、●）
            if any(symbol in line for symbol in ["〇", "◎", "●"]):
                pingze_lines.append(i)

        # 现在，遍历每个平仄标记行，统计符号数量
        for idx, line_idx in enumerate(pingze_lines):
            line = lines[line_idx]
            # 检查这一行是否有拗救
            has_jiujiu = line_idx in jiujiu_lines

            # 统计每个平仄符号
            for char in line:
                if char == "〇" or char == "◎":
                    # 正确或多音字，直接得分
                    correct_count += 1
                    total_count += 1
                elif char == "●":
                    # 平仄错误，但如果属于合法拗救，也算正确
                    if has_jiujiu:
                        # 属于合法拗救，按正确处理
                        correct_count += 1
                        # print(f"DEBUG: 发现拗救，●算作正确: {line}")
                    total_count += 1

        return correct_count, total_count

    def calculate_pingze_score(self, result_text: str) -> float:
        """平仄评分，包含对合法拗救的加分"""
        correct_count, total_count = self.analyze_pingze_result_with_jiujiu(result_text)

        if total_count == 0:
            return 0.0

        return (correct_count / total_count) * 100

    def extract_rhyme_info(self, result_text: str, poem_type: str) -> dict:
        """从结果文本中提取押韵信息"""
        rhyme_info = {
            'required_positions': [],
            'actual_correct': 0,
            'rhyme_lines': []
        }

        lines = result_text.split('\n')
        # 找出所有包含押韵信息的行，并记录原始顺序
        rhyme_infos = []
        for i, line in enumerate(lines):
            if ' 押韵 ' in line or ' 不押韵 ' in line:
                # 获取诗句行
                if i >= 2:
                    poem_line = lines[i - 1]
                    # 提取韵部信息
                    parts = line.split()
                    if len(parts) >= 2:
                        rhyme_part = parts[-2]
                    else:
                        rhyme_part = ''

                    is_correct = '不押韵' not in line
                    # 首句邻韵判断（仅在平水韵中考虑）
                    is_half = False
                    if poem_type in ['绝句', '律诗'] and len(rhyme_infos) == 0 and is_correct:
                        # 检查是否是邻韵（需要后续判断）
                        is_half = False  # 这里简化处理，暂不实现邻韵检测

                    rhyme_infos.append({
                        'content': poem_line.strip(),
                        'rhyme_part': rhyme_part.strip(),
                        'is_correct': is_correct,
                        'is_half': is_half
                    })

        # 根据诗体计算得分
        if poem_type == '绝句':
            # 绝句：共4句，第2、4句必押韵
            # 统计押韵正确的句数
            correct_count = sum(1 for info in rhyme_infos if info['is_correct'])

            # 绝句要求至少有2句押韵（第2、4句必须押韵）
            if correct_count >= 2:
                rhyme_info['actual_correct'] = 2  # 满分
            elif correct_count >= 1:
                rhyme_info['actual_correct'] = 1  # 半分
            else:
                rhyme_info['actual_correct'] = 0  # 零分

        elif poem_type == '律诗':
            # 律诗：共8句，第2、4、6、8句必押韵
            # 统计押韵正确的句数
            correct_count = sum(1 for info in rhyme_infos if info['is_correct'])

            # 律诗要求至少有4句押韵
            if correct_count >= 4:
                rhyme_info['actual_correct'] = 4  # 满分
            elif correct_count >= 3:
                rhyme_info['actual_correct'] = 3  # 75%
            elif correct_count >= 2:
                rhyme_info['actual_correct'] = 2  # 50%
            elif correct_count >= 1:
                rhyme_info['actual_correct'] = 1  # 25%
            else:
                rhyme_info['actual_correct'] = 0  # 零分

        else:  # 排律
            # 排律：所有偶数句必押韵，首句可押可不押
            # 统计押韵正确的句数
            for i, info in enumerate(rhyme_infos):
                if i % 2 == 1:  # 偶数句(0-based)
                    if info['is_correct']:
                        rhyme_info['actual_correct'] += 1
                    elif info['is_half']:
                        rhyme_info['actual_correct'] += 0.5

        rhyme_info['rhyme_lines'] = rhyme_infos
        return rhyme_info

    def calculate_rhyme_score(self, result_text, poem_type: str) -> float:
        """押韵评分"""
        # 检查result_text是否为错误码
        if isinstance(result_text, int):
            return 0.0

        rhyme_info = self.extract_rhyme_info(result_text, poem_type)

        # 确定应押韵句数
        if poem_type == '绝句':
            required_count = 2  # 第2、4句
        elif poem_type == '律诗':
            required_count = 4  # 第2、4、6、8句
        else:  # 排律
            # 从结果中计算实际的偶数句数
            total_lines = len(rhyme_info['rhyme_lines'])
            if total_lines <= 1:
                required_count = 0
            else:
                required_count = total_lines // 2

        if required_count == 0:
            return 0.0

        # 确保分数不超过100
        score = (rhyme_info['actual_correct'] / required_count) * 100
        return min(score, 100.0)

    def score_poem(self, poem: str, instruct: str, rhyme_system: str = 'pingshui') -> dict:
        """对一首诗进行全面评分"""
        # 默认使用平水韵，同时计算所有韵书的分数（保留完整性）
        results = {
            'poem': poem,
            'instruct': instruct,
            'format_score': 0.0,
            'pingze_score': 0.0,
            'rhyme_score_pingshui': 0.0,
            'rhyme_score_xin': 0.0,
            'rhyme_score_tong': 0.0,
            'selected_rhyme_system': rhyme_system
        }

        # 格式评分
        results['format_score'] = self.check_format(poem, instruct)

        # 解析诗体信息用于押韵评分
        instruct_info = self.parse_instruct(instruct)

        # 预处理诗句
        processed = extract_chinese(poem)
        processed_comma = extract_chinese(poem, comma_remain=True)

        # 对三种韵书体系分别进行评分
        yun_shu_list = [1, 2, 3]  # 平水韵、中华新韵、中华通韵

        for yun_shu in yun_shu_list:
            try:
                # 创建校验器并运行
                shi_rhythm = ShiRhythm(yun_shu, processed, processed_comma, False)
                result = shi_rhythm.main_shi()

                # 如果是错误码，设为0分
                if isinstance(result, int):
                    if yun_shu == 1:
                        results['rhyme_score_pingshui'] = 0.0
                    elif yun_shu == 2:
                        results['rhyme_score_xin'] = 0.0
                    else:
                        results['rhyme_score_tong'] = 0.0
                    continue

                # 平仄评分（只需要计算一次，使用第一个结果）
                if yun_shu == 1:
                    results['pingze_score'] = self.calculate_pingze_score(result)

                # 押韵评分
                rhyme_score = self.calculate_rhyme_score(result, instruct_info['poem_type'])
                if yun_shu == 1:
                    results['rhyme_score_pingshui'] = rhyme_score
                elif yun_shu == 2:
                    results['rhyme_score_xin'] = rhyme_score
                else:
                    results['rhyme_score_tong'] = rhyme_score

            except Exception as e:
                print(f"Error processing poem with yun_shu={yun_shu}: {e}")
                if yun_shu == 1:
                    results['rhyme_score_pingshui'] = 0.0
                elif yun_shu == 2:
                    results['rhyme_score_xin'] = 0.0
                else:
                    results['rhyme_score_tong'] = 0.0

        # 仅输出选中的韵书分数到主押韵分
        if rhyme_system in self.rhyme_systems:
            field = self.rhyme_systems[rhyme_system]['field']
            results['rhyme_score'] = results[field]
        else:
            # 如果传入了无效的韵书系统，默认使用平水韵
            print(f"Warning: Invalid rhyme system '{rhyme_system}', using default 'pingshui'")
            results['rhyme_score'] = results['rhyme_score_pingshui']

        return results

    def process_file(self, input_file: str, detailed_output: str, summary_output: str,
                     poem_field: str = 'prediction', instruct_field: str = 'instruct',
                     is_jsonl: bool = False, rhyme_system: str = 'pingshui',
                     save_detailed: bool = False, save_summary: bool = True):
        """处理JSON或JSONL文件并输出评分结果"""
        try:
            # 判断文件格式
            if is_jsonl:
                results = self._process_jsonl_file(input_file, poem_field, instruct_field, rhyme_system)
            else:
                results = self._process_json_file(input_file, poem_field, instruct_field, rhyme_system)

            # 保存结果
            self._save_results(results, detailed_output, summary_output, save_detailed, save_summary, rhyme_system)
        except Exception as e:
            print(f"Error processing file: {e}")

    def _process_json_file(self, input_file: str, poem_field: str, instruct_field: str, rhyme_system: str) -> list:
        """处理标准JSON文件"""
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            print(f"Error reading input file: {e}")
            return []

        if not isinstance(data, list):
            print("Input file should contain a list of objects")
            return []

        results = []
        total = len(data)

        for i, item in enumerate(data):
            print(f"Processing {i + 1}/{total}...")

            if poem_field not in item or instruct_field not in item:
                print(f"Skipping item {i + 1}: missing required fields '{poem_field}' or '{instruct_field}'")
                continue

            poem = item[poem_field]
            instruct = item[instruct_field]

            result = self.score_poem(poem, instruct, rhyme_system)
            results.append(result)

        return results

    def _process_jsonl_file(self, input_file: str, poem_field: str, instruct_field: str, rhyme_system: str) -> list:
        """处理JSONL文件（每行一个JSON对象）"""
        results = []
        line_count = 0
        processed_count = 0

        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue

                    line_count += 1
                    try:
                        item = json.loads(line)

                        if poem_field not in item or instruct_field not in item:
                            print(
                                f"Skipping line {line_count}: missing required fields '{poem_field}' or '{instruct_field}'")
                            continue

                        poem = item[poem_field]
                        instruct = item[instruct_field]

                        print(f"Processing line {line_count}...")

                        result = self.score_poem(poem, instruct, rhyme_system)
                        results.append(result)
                        processed_count += 1

                    except json.JSONDecodeError:
                        print(f"Skipping line {line_count}: invalid JSON")
                        continue
        except Exception as e:
            print(f"Error reading input file: {e}")

        print(f"Processed {processed_count} out of {line_count} lines")

        return results

    def _save_results(self, results: list, detailed_output: str, summary_output: str,
                      save_detailed: bool, save_summary: bool, rhyme_system: str):
        """保存结果到文件"""
        # 保存详细得分文件
        if save_detailed and detailed_output:
            try:
                with open(detailed_output, 'w', encoding='utf-8') as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)
                print(f"Detailed results saved to {detailed_output}")
            except Exception as e:
                print(f"Error writing detailed output file: {e}")

        # 保存综合得分文件
        if save_summary and summary_output:
            self._save_summary_results(results, summary_output, rhyme_system)

        # 打印统计信息
        self.print_statistics(results, rhyme_system)

    def _save_summary_results(self, results: list, summary_output: str, rhyme_system: str):
        """生成并保存综合得分文件"""
        if not results:
            print("No results to generate summary")
            return

        # 获取选中的韵书信息
        system_info = self.rhyme_systems[rhyme_system] if rhyme_system in self.rhyme_systems else self.rhyme_systems[
            'pingshui']

        # 计算各指标的平均分
        n = len(results)
        avg_format = sum(r['format_score'] for r in results) / n
        avg_pingze = sum(r['pingze_score'] for r in results) / n
        avg_rhyme = sum(r[f"rhyme_score_{rhyme_system}"] for r in results) / n

        # 计算总分（三个指标各占1/3权重）
        total_score = (avg_format + avg_pingze + avg_rhyme) / 3

        # 创建综合得分数据结构
        summary = {
            "dataset_statistics": {
                "sample_count": n,
                "rhyme_system": system_info['name']
            },
            "average_scores": {
                "format_score": round(avg_format, 2),
                "pingze_score": round(avg_pingze, 2),
                f"rhyme_score_{rhyme_system}": round(avg_rhyme, 2),
                "rhyme_score": round(avg_rhyme, 2),
                "total_score": round(total_score, 2)
            },
            "weights": {
                "format_score": 0.333,
                "pingze_score": 0.333,
                "rhyme_score": 0.333
            }
        }

        # 保存综合得分文件
        try:
            with open(summary_output, 'w', encoding='utf-8') as f:
                json.dump(summary, f, ensure_ascii=False, indent=2)
            print(f"Summary results saved to {summary_output}")
        except Exception as e:
            print(f"Error writing summary output file: {e}")

    def print_statistics(self, results: list, rhyme_system: str):
        """打印统计信息"""
        if not results:
            print("No results to analyze")
            return

        n = len(results)

        # 获取选中的韵书信息
        system_info = self.rhyme_systems[rhyme_system] if rhyme_system in self.rhyme_systems else self.rhyme_systems[
            'pingshui']

        # 计算各维度平均分
        avg_format = sum(r['format_score'] for r in results) / n
        avg_pingze = sum(r['pingze_score'] for r in results) / n
        avg_rhyme = sum(r[f"rhyme_score_{rhyme_system}"] for r in results) / n

        # 计算总分
        total_score = (avg_format + avg_pingze + avg_rhyme) / 3

        print("\n=== 评分统计 ===")
        print(f"样本数量: {n}")
        print(f"格式分平均: {avg_format:.2f}")
        print(f"平仄分平均: {avg_pingze:.2f}")
        print(f"押韵分({system_info['name']})平均: {avg_rhyme:.2f}")
        print(f"总分平均: {total_score:.2f} (三指标各占1/3权重)")


def main():
    parser = argparse.ArgumentParser(description='诗词格律评分工具（支持拗救加分）')
    parser.add_argument('input_file', help='输入JSON/JSONL文件路径')
    parser.add_argument('--detailed-output', help='详细得分输出文件路径')
    parser.add_argument('--summary-output', help='综合得分输出文件路径')

    # 字段控制参数
    parser.add_argument('--save-detailed', type=str, default="false", choices=['true', 'false'],
                        help='是否保存详细得分文件 (默认: false)')
    parser.add_argument('--save-summary', type=str, default="true", choices=['true', 'false'],
                        help='是否保存综合得分文件 (默认: true)')

    # 其他参数
    parser.add_argument('--poem-field', default='prediction', help='诗句字段名 (默认: prediction)')
    parser.add_argument('--instruct-field', default='instruct', help='指令字段名 (默认: instruct)')
    parser.add_argument('--is-jsonl', action='store_true', help='输入文件为JSONL格式')
    parser.add_argument('--rhyme-system', default='pingshui',
                        choices=['pingshui', 'xin', 'tong'],
                        help='韵书系统选择: pingshui(平水韵), xin(中华新韵), tong(中华通韵) (默认: pingshui)')

    args = parser.parse_args()

    # 设置默认输出文件名
    save_detailed = args.save_detailed.lower() == "true"
    save_summary = args.save_summary.lower() == "true"

    if not args.detailed_output and save_detailed:
        # 如果没有指定详细输出文件但需要保存，使用默认名称
        base_name = os.path.splitext(os.path.basename(args.input_file))[0]
        args.detailed_output = f"{base_name}_detailed.json"

    if not args.summary_output and save_summary:
        # 如果没有指定综合输出文件但需要保存，使用默认名称
        base_name = os.path.splitext(os.path.basename(args.input_file))[0]
        args.summary_output = f"{base_name}_summary.json"

    scorer = PoetryScorer()
    scorer.process_file(
        args.input_file,
        args.detailed_output or "",
        args.summary_output or "",
        args.poem_field,
        args.instruct_field,
        args.is_jsonl,
        args.rhyme_system,
        save_detailed,
        save_summary
    )


if __name__ == '__main__':
    main()
