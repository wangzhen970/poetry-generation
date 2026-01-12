# 诗词格律评分工具 (poetry-scorer)

## 目录

1. [项目简介](#项目简介)
2. [项目结构](#项目结构)
3. [项目文件清单](#项目文件清单)
4. [功能特性](#功能特性)
5. [使用方法](#使用方法)
6. [参数说明](#参数说明)
7. [输入输出格式](#输入输出格式)
8. [评分维度说明](#评分维度说明)
9. [注意事项](#注意事项)
10. [常见问题](#常见问题)
11. [子模块集成指南](#子模块集成指南)
12. [开发依赖](#开发依赖)
13. [许可证](#许可证)

## 项目简介

这个项目包含两个主要工具，用于对中国古典诗词进行格律评分和质量评估：

1. **poetry_scorer_jiujiu.py** - 诗词格律评分工具，支持拗救加分
2. **poetry_quality_extractor.py** - 优质诗词数据提取工具，基于评分筛选高质量诗词

Poetry-scorer 是一个独立的诗词格律评分工具，可以作为子模块集成到其他项目中使用，特别适合在 poetry-generation 项目或其他诗词生成系统中评估生成诗词的质量。

## 项目结构

```
poetry-scorer/
├── __init__.py                    # 项目包初始化
├── run.py                         # 项目运行脚本
├── poetry_scorer_jiujiu.py        # 诗词格律评分工具
├── poetry_quality_extractor.py    # 优质诗词数据提取工具
├── test_scorer.py                 # 测试脚本
├── README.md                      # 项目说明文档（正文档）
├── common/                        # 通用模块
│   ├── __init__.py
│   ├── common.py                  # 通用功能函数
│   └── num_to_cn.py               # 数字转汉字功能
├── shi/                           # 诗歌格律模块
│   ├── __init__.py
│   ├── shi_rhythm.py              # 诗歌格律校验核心
│   └── shi_first.py               # 首句格式判断
├── rhythm/                        # 韵部模块
│   ├── __init__.py
│   ├── pingshui_rhythm.py         # 平水韵处理
│   └── new_rhythm.py              # 新韵与通韵处理
└── hanzi/                         # 汉字信息模块
    ├── __init__.py
    ├── hanzi_class.py             # 汉字韵部信息
    └── hanzi_pinyin_class.py      # 汉字拼音信息
```

## 项目文件清单

### 核心脚本

- `run.py` - 项目运行脚本，提供统一的命令行接口
- `poetry_scorer_jiujiu.py` - 诗词格律评分工具，支持拗救加分
- `poetry_quality_extractor.py` - 优质诗词数据提取工具，基于评分筛选高质量诗词
- `test_scorer.py` - 测试脚本，验证评分功能是否正常工作

### 依赖模块

#### common 目录
- `__init__.py` - 模块初始化
- `common.py` - 通用功能函数，包括汉字转拼音、韵部查询等
- `num_to_cn.py` - 数字转汉字功能

#### shi 目录
- `__init__.py` - 模块初始化
- `shi_rhythm.py` - 诗歌格律校验核心，包括平仄、押韵校验
- `shi_first.py` - 首句格式判断，处理多音字和拗救

#### rhythm 目录
- `__init__.py` - 模块初始化
- `pingshui_rhythm.py` - 平水韵处理，包括韵部查找和转换
- `new_rhythm.py` - 新韵与通韵处理，支持现代汉语韵律

#### hanzi 目录
- `__init__.py` - 模块初始化
- `hanzi_class.py` - 汉字韵部信息，包含平水韵数据
- `hanzi_pinyin_class.py` - 汉字拼音信息，包含多音字数据

## 功能特性

### poetry_scorer_jiujiu.py

- 格式评分：根据诗词的句长和诗体进行评分
- 平仄评分：检测诗词平仄是否符合格律要求，支持合法拗救加分
- 押韵评分：支持平水韵、中华新韵、中华通韵三种韵书体系
- 支持JSON和JSONL格式的批量文件处理
- 输出详细得分和综合得分两种报告

### poetry_quality_extractor.py

- 基于评分结果对诗词进行分类和排序
- 支持从大量数据中筛选高质量诗词
- 可设置每类诗词的最大输出数量
- 灵活的字段保留功能
- 自动检测诗词类型（五言绝句、七言绝句、五言律诗、七言律诗）

## 使用方法

### 使用 run.py 脚本（推荐）

```bash
# 运行测试，验证功能
python run.py test

# 诗词评分
python run.py score input.jsonl --rhyme-system pingshui --save-summary true

# 提取优质诗词
python poetry_scorer/run.py extract \
  ./data/raw/split_12540.jsonl \
  ./data/output/chinesepoem_4000.json \
  --is-jsonl
```

### 直接使用主脚本

#### poetry_scorer_jiujiu.py 使用示例

```bash
# 处理JSON文件
python poetry_scorer_jiujiu.py input.json --rhyme-system pingshui --save-summary true

# 处理JSONL文件，自定义输入输出路径
python poetry_scorer_jiujiu.py input.jsonl \
  --detailed-output detailed.json \
  --summary-output summary.json \
  --poem-field content \
  --instruct-field instruct \
  --is-jsonl \
  --rhyme-system xin
```

#### poetry_quality_extractor.py 使用示例

```bash
# 基本用法
python poetry_quality_extractor.py input.jsonl output.jsonl \
  --poem-field content \
  --instruct-field instruct \
  --keep-fields title content instruct \
  --is-jsonl

# 自定义各类别输出数量
python poetry_quality_extractor.py input.jsonl output.jsonl \
  --max-five-quatrain 200 \
  --max-seven-quatrain 200 \
  --max-five-regulated 100 \
  --max-seven-regulated 100 \
  --is-jsonl
```

## 参数说明

### poetry_scorer_jiujiu.py 参数

- `input_file`: 输入JSON/JSONL文件路径
- `--detailed-output`: 详细得分输出文件路径（可选）
- `--summary-output`: 综合得分输出文件路径（可选）
- `--save-detailed`: 是否保存详细得分文件（true/false，默认：false）
- `--save-summary`: 是否保存综合得分文件（true/false，默认：true）
- `--poem-field`: 诗句字段名（默认：prediction）
- `--instruct-field`: 指令字段名（默认：instruct）
- `--is-jsonl`: 输入文件为JSONL格式
- `--rhyme-system`: 韵书系统选择（pingshui/xin/tong，默认：pingshui）

### poetry_quality_extractor.py 参数

- `input_file`: 输入JSON/JSONL文件路径
- `output_file`: 输出文件路径
- `--poem-field`: 诗句字段名（默认：prediction）
- `--instruct-field`: 指令字段名（默认：instruct）
- `--keep-fields`: 需要保留到输出文件的字段列表（默认：prediction instruct）
- `--max-five-quatrain`: 五言绝句最大输出数量（默认：100）
- `--max-seven-quatrain`: 七言绝句最大输出数量（默认：100）
- `--max-five-regulated`: 五言律诗最大输出数量（默认：50）
- `--max-seven-regulated`: 七言律诗最大输出数量（默认：50）
- `--is-jsonl`: 输入文件为JSONL格式
- `--rhyme-system`: 韵书系统选择（pingshui/xin/tong，默认：pingshui）

## 输入输出格式

### 输入格式示例

```json
[
  {
    "content": "床前明月光，疑是地上霜。举头望明月，低头思故乡。",
    "instruct": "请创作一首五言绝句"
  },
  ...
]
```

### 输出格式示例

poetry_scorer_jiujiu.py 详细输出：
```json
[
  {
    "poem": "床前明月光，疑是地上霜。举头望明月，低头思故乡。",
    "instruct": "请创作一首五言绝句",
    "format_score": 100.0,
    "pingze_score": 75.0,
    "rhyme_score_pingshui": 50.0,
    "rhyme_score_xin": 0.0,
    "rhyme_score_tong": 0.0,
    "selected_rhyme_system": "pingshui",
    "rhyme_score": 50.0
  },
  ...
]
```

poetry_scorer_jiujiu.py 综合输出：
```json
{
  "dataset_statistics": {
    "sample_count": 100,
    "rhyme_system": "平水韵"
  },
  "average_scores": {
    "format_score": 85.5,
    "pingze_score": 70.2,
    "rhyme_score_pingshui": 65.8,
    "rhyme_score": 65.8,
    "total_score": 73.83
  },
  "weights": {
    "format_score": 0.333,
    "pingze_score": 0.333,
    "rhyme_score": 0.333
  }
}
```

## 评分维度说明

1. **格式分**：检查诗词的句长和诗体是否符合要求，满分100分
2. **平仄分**：检查诗词平仄是否正确，合法拗救视为正确，满分100分
3. **押韵分**：检查押韵是否正确，满分100分

综合评分：三个维度各占1/3权重计算平均分

## 注意事项

1. 输入文件必须是JSON或JSONL格式
2. JSONL文件每行必须是一个完整的JSON对象
3. 诗句字段必须包含有效的中文诗词内容
4. 指令字段应包含对诗词格律要求的描述
5. 评分工具会自动处理括号内内容和标点符号

## 常见问题

1. **评分为0**：检查输入是否包含有效的中文字符
2. **平仄分较低**：可能不符合格律要求，但拗救可获得加分
3. **押韵分较低**：可能使用了不押韵的语言或韵书体系不匹配

## 子模块集成指南

### 集成方式

#### 方式一：直接复制文件夹

1. 将整个 `poetry-scorer` 文件夹复制到您的项目目录中
2. 确保 `poetry-scorer` 文件夹与您的主项目代码处于同一目录层级或您的 Python 路径中

```bash
# 示例：将 poetry-scorer 复制到 poetry-generation 项目中
cp -r poetry-scorer /path/to/poetry-generation/
```

#### 方式二：作为子模块 (Git)

1. 在您的主项目中添加 poetry-scorer 作为 Git 子模块：

```bash
cd /path/to/poetry-generation
git submodule add https://github.com/your-username/poetry-scorer.git
git submodule update --init --recursive
```

### 在您的代码中导入和使用

#### 方法1：导入单个类/函数

```python
# 在您的 Python 代码中导入
import sys
import os

# 添加 poetry-scorer 到 Python 路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'poetry-scorer'))

from poetry_scorer_jiujiu import PoetryScorer
from poetry_quality_extractor import PoetryQualityExtractor

# 使用评分器
scorer = PoetryScorer()
result = scorer.score_poem("床前明月光，疑是地上霜。举头望明月，低头思故乡。", "五言绝句")
print(f"总分: {(result['format_score'] + result['pingze_score'] + result['rhyme_score']) / 3:.2f}")
```

#### 方法2：使用命令行接口

```python
# 通过命令行调用
import subprocess

# 诗词评分
result = subprocess.run([
    'python', 'poetry-scorer/run.py', 'score',
    'input.json', '--poem-field', 'content', '--instruct-field', 'instruct'
], capture_output=True, text=True)
print(result.stdout)

# 优质数据提取
result = subprocess.run([
    'python', 'poetry-scorer/run.py', 'extract',
    'input.json', 'output.jsonl', '--max-five-quatrain', '100'
], capture_output=True, text=True)
print(result.stdout)
```

### 在 poetry-generation 项目中使用的示例

1. 如果您有一个生成诗词的模型，想要评估生成的诗词质量：

```python
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'poetry-scorer'))

from poetry_scorer_jiujiu import PoetryScorer

# 初始化评分器
scorer = PoetryScorer()

# 评估一首生成的诗词
poem = "春风拂面绿芽生，万物复苏暖气升。燕子归来寻旧处，花开十里蝶飞情。"
instruct = "七言绝句"

# 评分
result = scorer.score_poem(poem, instruct, rhyme_system='pingshui')
print(f"格式分: {result['format_score']}")
print(f"平仄分: {result['pingze_score']}")
print(f"押韵分: {result['rhyme_score']}")
```

2. 如果您想要从大量生成的诗词中筛选高质量的：

```python
import sys
import os
import json
sys.path.append(os.path.join(os.path.dirname(__file__), 'poetry-scorer'))

from poetry_quality_extractor import PoetryQualityExtractor

# 加载生成的诗词数据
with open('generated_poems.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 创建提取器
extractor = PoetryQualityExtractor('pingshui')

# 筛选高质量诗词
max_per_category = {
    'five_quatrain': 50,
    'seven_quatrain': 50,
    'eight_five': 20,
    'eight_seven': 20
}

# 处理数据（这会输出高质量的诗词到指定文件）
stats = extractor.process_dataset(
    'generated_poems.json',
    'content',
    'instruct',
    'high_quality_poems.json',
    max_per_category,
    ['content', 'instruct', 'title'],
    is_jsonl=False
)

print("筛选完成！")
print(f"平均总分: {stats['average_scores']['total']}")
```

### 集成到 Web 服务中的示例

您可以使用 Flask 或 FastAPI 创建一个简单的 Web 端点来包装评分功能：

```python
from flask import Flask, request, jsonify
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'poetry-scorer'))

from poetry_scorer_jiujiu import PoetryScorer

app = Flask(__name__)
scorer = PoetryScorer()

@app.route('/score', methods=['POST'])
def score_poetry():
    data = request.json
    poem = data.get('poem', '')
    instruct = data.get('instruct', '')
    result = scorer.score_poem(poem, instruct)
    
    total_score = (result['format_score'] + result['pingze_score'] + result['rhyme_score']) / 3
    return jsonify({
        'total_score': total_score,
        'format_score': result['format_score'],
        'pingze_score': result['pingze_score'],
        'rhyme_score': result['rhyme_score']
    })
```

### 集成注意事项

1. **Python 路径**：确保 `poetry-scorer` 文件夹在您的 Python 路径中
2. **依赖关系**：poetry-scorer 不需要额外的第三方依赖，只需 Python 标准库
3. **编码**：确保您的输入文件使用 UTF-8 编码
4. **字段名称**：使用评分工具时，确保指定正确的字段名称（poem-field 和 instruct-field）

### 集成常见问题

#### Q: 在其他项目中导入时出现 ModuleNotFoundError
A: 确保 poetry-scorer 文件夹在您的 Python 路径中。可以使用以下代码添加路径：
```python
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'poetry-scorer'))
```

#### Q: 评分结果总是 0 分
A: 检查输入的诗词是否包含有效的中文字符，以及指令字段是否包含正确的诗词类型描述。

#### Q: 如何在 poetry-generation 项目中批量处理
A: 您可以创建一个批处理脚本，将 poetry-scorer 作为工具来评估生成的数据集：
```python
import sys
import os
import json
sys.path.append(os.path.join(os.path.dirname(__file__), 'poetry-scorer'))

from poetry_scorer_jiujiu import PoetryScorer

scorer = PoetryScorer()

def batch_score_poems(poems_file, output_file):
    with open(poems_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    results = []
    for item in data:
        poem = item['poem']
        instruct = item['instruct']
        result = scorer.score_poem(poem, instruct)
        
        # 计算总分
        total = (result['format_score'] + result['pingze_score'] + result['rhyme_score']) / 3
        
        results.append({
            'poem': poem,
            'instruct': instruct,
            'total_score': total,
            'format_score': result['format_score'],
            'pingze_score': result['pingze_score'],
            'rhyme_score': result['rhyme_score']
        })
    
    # 按总分排序
    results.sort(key=lambda x: x['total_score'], reverse=True)
    
    # 保存结果
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

# 使用示例
batch_score_poems('generated_poems.json', 'scored_poems.json')
```

## 开发依赖

- Python 3.6+
- 无需额外第三方库，仅使用Python标准库

## 许可证

本项目遵循原项目的许可证协议。

---

这样就完成了三个文档的整合，形成了一个完整的包含使用指南、项目说明和子模块集成方法的总文档。
