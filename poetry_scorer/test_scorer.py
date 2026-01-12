#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试脚本，验证诗词评分工具是否正常工作
"""

import json
import sys
import os

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from poetry_scorer_jiujiu import PoetryScorer


def test_poetry_scorer():
    """测试诗词评分功能"""
    print("开始测试诗词评分功能...")

    # 创建测试数据
    test_poems = [
        {
            "poem": "床前明月光，疑是地上霜。举头望明月，低头思故乡。",
            "instruct": "五言绝句"
        },
        {
            "poem": "白日依山尽，黄河入海流。欲穷千里目，更上一层楼。",
            "instruct": "五言绝句"
        },
        {
            "poem": "春眠不觉晓，处处闻啼鸟。夜来风雨声，花落知多少。",
            "instruct": "五言绝句"
        }
    ]

    # 创建评分器实例
    scorer = PoetryScorer()

    # 对每首诗进行评分
    results = []
    for i, test_case in enumerate(test_poems):
        print(f"\n正在测试第 {i + 1} 首诗...")
        print(f"诗句: {test_case['poem']}")

        result = scorer.score_poem(test_case['poem'], test_case['instruct'])
        results.append(result)

        print(f"格式分: {result['format_score']}")
        print(f"平仄分: {result['pingze_score']}")
        print(f"押韵分(平水韵): {result['rhyme_score_pingshui']}")
        print(f"押韵分(新韵): {result['rhyme_score_xin']}")
        print(f"押韵分(通韵): {result['rhyme_score_tong']}")
        print(f"押韵分(选中): {result['rhyme_score']}")

    # 保存测试结果
    with open('test_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print("\n测试完成！结果已保存到 test_results.json")

    # 计算平均分
    avg_format = sum(r['format_score'] for r in results) / len(results)
    avg_pingze = sum(r['pingze_score'] for r in results) / len(results)
    avg_rhyme = sum(r['rhyme_score'] for r in results) / len(results)
    total_avg = (avg_format + avg_pingze + avg_rhyme) / 3

    print(f"\n=== 平均分 ===")
    print(f"格式分: {avg_format:.2f}")
    print(f"平仄分: {avg_pingze:.2f}")
    print(f"押韵分: {avg_rhyme:.2f}")
    print(f"总分: {total_avg:.2f}")

    return True


if __name__ == "__main__":
    try:
        test_poetry_scorer()
        print("\n✅ 所有测试通过！")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        sys.exit(1)
