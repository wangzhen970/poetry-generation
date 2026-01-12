"""
检测5、7言绝句和律诗，提取出来，并在对应字段标明类型
支持常见古籍排版格式（单行、多行、两行八句等）
"""

import json
import re
import random
import argparse
from collections import Counter

def clean_content_for_output(text):
    """仅移除换行符，保留所有标点、数字、括号等"""
    if not isinstance(text, str):
        return ""
    return text.replace('\n', '').replace('\r', '')


def is_part_of_series(title):
    """
    判断标题是否为组诗（包括总称或其中一篇）
    返回 True 表示应过滤
    """
    if not title:
        return False

    # 白名单：少数著名组诗可保留（可选）
    SERIES_WHITELIST = {"秋兴八首", "咏怀古迹五首", "诸将五首", "羌村三首"}
    for white in SERIES_WHITELIST:
        if white in title:
            return False

    # === 新增：匹配 "X诗Y首" 总标题 ===
    # 模式：任意文字 + 数字 + (首|章|篇|阕)
    # 例如：杂诗七首、古风五章、绝句四首、田园诗六篇
    total_series_pattern = r'.*[一二三四五六七八九十\d]+[首篇章阕]'

    # === 原有：匹配 "其X" 子篇 ===
    part_patterns = [
        r'[一二三四五六七八九十\d]+[首篇章阕]\s*[·\.]?\s*其?[一二三四五六七八九十\d]+',
        r'其[一二三四五六七八九十\d]+\s*$',
        r'第[一二三四五六七八九十\d]+[首篇章]',
        r'[一二三四五六七八九十\d]+[首篇章]\s+.*其[一二三四五六七八九十\d]+',
        r'[（\(]其[一二三四五六七八九十\d]+[）\)]'
    ]

    # 如果匹配总标题模式（且不含白名单），则过滤
    if re.search(total_series_pattern, title):
        return True

    # 如果匹配子篇模式，也过滤
    for pattern in part_patterns:
        if re.search(pattern, title):
            return True

    return False


# 常见词牌名及非目标诗歌标题
CI_KEYWORDS = {
    "一剪梅", "卜算子", "八声甘州", "八六子", "八归", "八拍蛮", "八音谐",
    "九张机", "九日", "九回肠", "九辩", "了", "人月圆", "人南渡", "十六字令",
    "十样花", "十二时", "十二时慢", "十拍子", "十样花", "入塞", "入梦", "入蜀",
    "八拍蛮", "八六子", "八归", "八音谐", "八声甘州",
    "大江东去", "大酺", "女冠子", "女红", "小重山", "小梅花", "小圣乐",
    "千秋岁", "千秋岁引", "千秋万岁", "千秋岁令", "千秋岁慢",
    "万年欢", "万年枝", "万年春", "万年欢慢", "万年欢引",
    "上行杯", "上江虹", "上西平", "上南平", "上平南", "上平西", "上平中",
    "上阳春", "上林春", "上林春令", "上林春慢", "上林春引",
    "夜行船", "夜飞鹊", "夜游宫", "夜合花", "夜半乐", "夜捣衣", "夜如年",
    "天仙子", "天门谣", "天香", "天香引", "天净沙", "天仙子慢", "天仙子引",
    "忆江南", "忆王孙", "忆秦娥", "忆少年", "忆旧游", "忆帝京", "忆汉月",
    "忆萝月", "忆故人", "忆君王", "忆闷令", "忆黄梅", "忆馀杭", "忆仙姿",
    "风入松", "风流子", "风中柳", "凤栖梧", "凤箫吟", "凤楼春", "凤求凰",
    "木兰花", "木兰花令", "木兰花慢", "木兰花引", "木兰花序",
    "水调歌头", "水龙吟", "水调歌", "水调", "水调歌引", "水调歌慢",
    "玉楼春", "玉蝴蝶", "玉漏迟", "玉连环", "玉簟秋", "玉人歌", "玉山枕",
    "甘州曲", "甘州遍", "甘州子", "甘州令", "甘州八声", "甘州摘红",
    "石州慢", "石州引", "石州行", "石州慢引", "石州慢令",
    "生查子", "生查子慢", "生查子近", "生查子令",
    "台城路", "台城游", "台城路慢", "台城路引",
    "市桥柳", "市桥柳令", "市桥柳引",
    "兰陵王", "兰陵王慢", "兰陵王引",
    "永遇乐", "永遇乐慢", "永遇乐引",
    "永新歌", "永新妇", "永新乐", "永新引",
    "过龙门", "过龙门令", "过龙门引",
    "过秦楼", "过秦楼慢", "过秦楼引",
    "行香子", "行香子慢", "行香子令", "行香子引",
    "庆清朝", "庆清朝慢", "庆清朝引",
    "庆春宫", "庆春宫慢", "庆春宫引",
    "庆宫春", "庆宫春慢", "庆宫春引",
    "庆金枝", "庆金枝令", "庆金枝引",
    "庆佳节", "庆佳节令", "庆佳节引",
    "庆同天", "庆同天令", "庆同天引",
    "庆长春", "庆长春令", "庆长春引",
    "庆清朝", "庆清朝慢", "庆清朝引",
    "齐天乐", "齐天乐慢", "齐天乐引",
    "齐天乐令", "齐天乐引",
    "阮郎归", "阮郎归令", "阮郎归引",
    "诉衷情", "诉衷情令", "诉衷情引", "诉衷情近",
    "步蟾宫", "步虚子", "步虚词", "步虚声", "步虚引",
    "步虚子令", "步虚子引",
    "步蟾宫令", "步蟾宫引",
    '浣溪沙', '虞美人', '菩萨蛮', '水调歌头', '念奴娇', '满江红',
    '临江仙', '蝶恋花', '清平乐', '鹧鸪天', '西江月', '南乡子',
    '卜算子', '江城子', '踏莎行', '渔家傲', '定风波', '青玉案',
    '木兰花', '兰陵王', '八声甘州', '摸鱼儿', '贺新郎', '永遇乐',
    '玉楼春', '浪淘沙', '点绛唇', '好事近', '醉花阴', '行香子',
    '步蟾宫', '沁园春', '声声慢', '扬州慢', '桂枝香', '齐天乐',
    '夜行船', '绝命诗',
    '水龙吟', '满庭芳', '蝶恋花', '临江仙', '鹧鸪天',
    '龟虽寿', '短歌行', '观沧海', '蒿里行', '燕歌行', '白马篇',
    '将进酒', '蜀道难', '兵车行', '丽人行','玉阑干','鹊桥仙','南歌子','杂曲','恋绣衾','锦帐春'
}

def is_likely_ci(title):
    """判断是否为词或非目标诗歌"""
    if not title:
        return False

    clean_title = re.sub(r'[·（）().\d一二三四五六七八九十\s]', '', title)

    # 1. 关键词匹配
    for kw in CI_KEYWORDS:
        if kw in clean_title:
            return True

    # 2. 词牌特征字
    if re.search(r'[令引近慢犯摊破减字]', clean_title):
        return True

    # 3. 启发式：长标题且不含诗题常见结尾
    if len(clean_title) >= 3 and not re.search(r'(诗|吟|歌|行|引|谣|篇|辞|叹|作|题)$', clean_title):
        common_endings = {'诗', '吟', '歌', '行', '引', '谣', '篇', '辞'}
        if not any(end in clean_title for end in common_endings):
            return True

    return False

def split_into_lines(content):
    """智能分行：支持标准多行、单行多句、两行八句等格式"""
    content = content.strip()
    if not content:
        return []

    # 先按 \n 分割
    lines_by_nl = [line.strip() for line in content.split('\n') if line.strip()]

    # 情况1: 已是4或8行 → 直接返回
    if len(lines_by_nl) in (4, 8):
        return lines_by_nl

    # 情况2: 2行 → 尝试每行切为4句（针对七律/五律）
    if len(lines_by_nl) == 2:
        all_parts = []
        for line in lines_by_nl:
            parts = re.split(r'[，。；！？]', line)
            parts = [p.strip() for p in parts if p.strip()]
            all_parts.extend(parts)
        if len(all_parts) == 8:
            return [p + '。' for p in all_parts]

    # 情况3: 无换行 → 按句末标点切
    if '\n' not in content:
        sentences = re.split(r'[。！？；]', content)
        sentences = [s.strip() for s in sentences if s.strip()]
        if len(sentences) in (4, 8):
            return [s + '。' for s in sentences]

    # 情况4: fallback 到固定字数（仅限标准长度）
    han_only = ''.join(re.findall(r'[\u4e00-\u9fa5]', content))
    total = len(han_only)
    if total == 56:  # 七律
        return [han_only[i:i+7] for i in range(0, 56, 7)]
    elif total == 40:  # 五律
        return [han_only[i:i+5] for i in range(0, 40, 5)]
    elif total == 28:  # 七绝
        return [han_only[i:i+7] for i in range(0, 28, 7)]
    elif total == 20:  # 五绝
        return [han_only[i:i+5] for i in range(0, 20, 5)]

    return lines_by_nl if lines_by_nl else [content]

def classify_poem(raw_content, title=""):
    if not raw_content or not isinstance(raw_content, str):
        return None

        # === 新增：过滤组诗中的单篇 ===
    if is_part_of_series(title):
        return None

    # 快速排除已知非目标诗歌
    reject_titles = {'龟虽寿', '短歌行', '观沧海', '蒿里行', '燕歌行', '白马篇'}
    if any(rt in title for rt in reject_titles):
        return None

    # 过滤词
    if is_likely_ci(title):
        return None

    # 智能分行
    lines = split_into_lines(raw_content)
    num_lines = len(lines)

    # 允许绝句=4行，律诗=7~9行（容忍变体）
    if num_lines == 4:
        poem_form = "jueju"
    elif 7 <= num_lines <= 9:
        poem_form = "lvshi"
    else:
        return None

    # 过滤联句等
    full_text = "".join(lines)
    if '--' in full_text or '〔' in full_text or '［' in full_text:
        return None

    # 提取每行汉字数
    han_counts = []
    for line in lines:
        han_only = re.findall(r'[\u4e00-\u9fa5]', line)
        han_counts.append(len(han_only))

    # 快速排除非5/7言
    if not any(c in (5, 6, 7, 8) for c in han_counts):
        return None

    # 确定主字数（必须是5或7）
    main_count = None
    if poem_form == "jueju":
        cnt = Counter(han_counts)
        for num in [7, 5]:
            if cnt.get(num, 0) >= 3:  # 4句中至少3句标准
                main_count = num
                break
        if main_count is None:
            return None
    else:  # lvshi
        cnt = Counter(han_counts)
        for num in [7, 5]:
            if cnt.get(num, 0) >= 5:  # 7-9句中至少5句标准
                main_count = num
                break
        if main_count is None:
            return None

    # 验证合规句比例
    threshold = 4 if poem_form == "jueju" else 7
    valid_count = sum(1 for c in han_counts if abs(c - main_count) <= 1)
    if valid_count < threshold:
        return None

    # 返回类型
    if poem_form == "jueju":
        return "五言绝句" if main_count == 5 else "七言绝句"
    else:
        return "五言律诗" if main_count == 5 else "七言律诗"

def main():
    parser = argparse.ArgumentParser(description="抽取古诗并标注诗体，保留 content 中的标点，仅去除换行符")
    parser.add_argument("input", help="输入 JSONL 文件路径")
    parser.add_argument("output", help="输出 JSONL 文件路径")
    parser.add_argument("--content-field", default="content", help="诗歌文本字段名（默认: content）")
    parser.add_argument("--keep-fields", nargs="+", default=None,
                        help="要保留的字段列表（默认保留所有字段）")
    parser.add_argument("--seed", type=int, default=42, help="随机种子")
    args = parser.parse_args()

    random.seed(args.seed)

    target_types = ["五言绝句", "七言绝句", "五言律诗", "七言律诗"]
    poems_by_type = {t: [] for t in target_types}

    print("正在读取并分类诗歌...")
    with open(args.input, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue

            raw_content = record.get(args.content_field, "")
            title = record.get("title", "")
            poem_type = classify_poem(raw_content, title)

            if poem_type in target_types:
                if args.keep_fields is None:
                    new_record = record.copy()
                else:
                    new_record = {k: record[k] for k in args.keep_fields if k in record}

                if args.content_field in record:
                    clean_content = clean_content_for_output(record[args.content_field])
                    new_record[args.content_field] = clean_content

                new_record["instruct"] = poem_type
                poems_by_type[poem_type].append(new_record)

    # 抽样：n_needed控制输出多少条数据，每种类型各占四分之一
    sampled = []
    for ptype in target_types:
        pool = poems_by_type[ptype]
        n_needed = 10000    # 控制输出多少条数据
        if len(pool) < n_needed:
            print(f"⚠️  警告：{ptype} 只有 {len(pool)} 条，少于{n_needed}条")
            sampled.extend(pool)
        else:
            sampled.extend(random.sample(pool, n_needed))

    random.shuffle(sampled)

    # 写入输出
    with open(args.output, 'w', encoding='utf-8') as f:
        for rec in sampled:
            f.write(json.dumps(rec, ensure_ascii=False) + '\n')

    print(f"\n✅ 完成！共抽取 {len(sampled)} 条诗歌，已保存至 {args.output}")
    for t in target_types:
        count = sum(1 for x in sampled if x.get("instruct") == t)
        print(f"  - {t}: {count} 条")

if __name__ == "__main__":
    main()
