# 模式选择器 (Mode Selector)

根据市场环境自动选择最适合的操作模式，指导当日交易决策。

---

## 执行总流程

```
┌─────────────────────────────────────────────────────────────┐
│  Step 0: 数据准备（所有功能的前置条件）                        │
│  - 获取市场行情数据                                           │
│  - 获取新闻数据（AI分析整理）                                 │
│  - 获取淘股吧舆情语料（AI分析整理）                           │
│  - 获取KOL观点（AI汇总）                                      │
│  - 加载短期记忆（近1周）+ 长期记忆（近1月）                   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  Step 1: 判市                                               │
│  判断市场环境是否安全，决定仓位                               │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  Step 2: 选股                                               │
│  从全市场筛选重点关注池                                     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  Step 3: 诊股                                               │
│  对候选股票进行五维打分                                     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  Step 4: 策略                                               │
│  制定交易计划（买点/卖点/仓位/止损）                        │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  Step 5: 复盘                                               │
│  每日收盘后总结，更新记忆                                    │
└─────────────────────────────────────────────────────────────┘
```

---

## 数据准备前置流程

### 目录初始化与Tag检查

```
每次执行任何功能前，必须先检查数据准备状态：
```

```python
import os
from datetime import datetime

def check_data_ready():
    """
    检查数据准备状态

    目录结构：
    a-stock-YYYYMMDD/
    ├── 00-大盘上下文.md
    ├── 01-策略大纲.md
    ├── 02-标的观察池.md
    ├── short_term_memory.md     # 短期记忆（近1周）
    ├── long_term_memory.md     # 长期记忆（近1月）
    ├── trading-plan.json
    ├── data/
    │   ├── market_YYYYMMDD.csv
    │   ├── sentiment_YYYYMMDD.json
    │   ├── fund_flow_YYYYMMDD.json
    │   ├── sector_rank_YYYYMMDD.json
    │   ├── news_YYYYMMDD.json
    │   ├── tgb_YYYYMMDD_corpus.txt
    │   └── tgb_list_YYYYMMDD.txt
    ├── logs/
    ├── 标的分析/
    ├── DATA_SUCCESS          # 数据准备成功Tag
    └── DATA_DEGRADED          # 数据降级Tag（如有）
    """
    date_str = datetime.now().strftime('%Y%m%d')
    workspace = f"a-stock-{date_str}"

    # 检查目录是否存在
    if not os.path.exists(workspace):
        # 创建目录结构
        os.makedirs(workspace, exist_ok=True)
        os.makedirs(f"{workspace}/data", exist_ok=True)
        os.makedirs(f"{workspace}/logs", exist_ok=True)
        os.makedirs(f"{workspace}/标的分析", exist_ok=True)
        return 'need_prepare'

    # 检查Tag文件
    if os.path.exists(f"{workspace}/DATA_SUCCESS"):
        return 'ready'  # 数据已准备，无需重复获取

    if os.path.exists(f"{workspace}/DATA_DEGRADED"):
        return 'degraded'  # 已有降级数据，继续使用

    # 目录存在但无Tag，需要准备
    return 'need_prepare'
```

### 数据准备流程

```python
def prepare_data_with_retry(max_retries=3):
    """
    数据准备流程（带重试）

    状态流转：
    need_prepare → preparing → success/degraded
                         ↓
                    failed（重试3次后降级）
    """
    date_str = datetime.now().strftime('%Y%m%d')
    workspace = f"a-stock-{date_str}"

    status = check_data_ready()

    if status == 'ready':
        print(f"✅ 数据已就绪，跳过数据准备")
        return 'ready'

    if status == 'degraded':
        print(f"⚠️ 存在降级数据，继续使用")
        return 'degraded'

    # 需要准备，执行数据准备
    for attempt in range(1, max_retries + 1):
        try:
            print(f"📥 开始数据准备（第{attempt}次尝试）...")

            # 执行Step 0数据准备
            success = execute_data_preparation()

            if success:
                # 创建成功Tag
                with open(f"{workspace}/DATA_SUCCESS", 'w') as f:
                    f.write(f"数据准备完成: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"✅ 数据准备成功")
                return 'ready'

        except Exception as e:
            print(f"❌ 第{attempt}次失败: {e}")
            if attempt >= max_retries:
                # 重试3次后仍失败，降级
                create_degraded_tag(workspace, error_msg=str(e))
                return 'degraded'

    return 'degraded'
```

### 降级Tag规则

```
降级条件：
1. 数据获取失败（网络超时/API不可用）
2. 重试3次后依然不成功

降级处理：
- 创建 DATA_DEGRADED Tag文件
- 记录失败原因和数据缺失情况
- 后续分析降低置信度（明确标注数据缺失）

禁止行为：
- ❌ 禁止使用Mock数据填充
- ❌ 禁止假设数据存在
- ❌ 禁止捏造数据

降级输出示例：
```markdown
# 数据准备降级报告 - 20251229

## 状态：DATA_DEGRADED

## 失败原因
- 新闻数据获取失败：API超时
- 淘股吧语料获取失败：网络不可达

## 缺失数据
- ❌ news_YYYYMMDD.json（未获取）
- ❌ tgb_YYYYMMDD_corpus.txt（未获取）
- ✅ market_YYYYMMDD.csv（已获取）
- ✅ sentiment_YYYYMMDD.json（已获取）

## 影响评估
- 消息面分析：无法进行
- 舆情分析：无法进行
- 判市置信度：降低 20%
- 选股置信度：降低 15%

## 后续处理
1. 明确告知用户数据缺失情况
2. 在分析和结论中标注"数据来源：[降级]"
3. 增加风险提示
```

### 数据复用规则

```
已存在DATA_SUCCESS时：
✅ 复用已有数据（行情/情绪/资金）
✅ 基于已有数据进行分析
❌ 不重复调用数据脚本

非必要情况：
- 仅修改少量参数时不需要重新获取
- 查看昨日数据时不需要重新获取
- 复盘时复用当日数据

需要重新获取的情况：
- 用户明确要求刷新数据
- Tag文件过期（超过24小时）
- 数据明显异常需要重新获取
```

---

## Step 0: 数据准备

### 0.1 基础数据获取

**行情数据**

```python
import akshare as ak
import pandas as pd
from datetime import datetime, timedelta

def fetch_market_data():
    """获取市场行情数据"""
    # 全市场实时行情
    df = ak.stock_zh_a_spot_em()

    # 指数数据
    indices = {
        '上证': ak.stock_zh_index_spot_em(symbol="000001"),
        '深证': ak.stock_zh_index_spot_em(symbol="399001"),
        '创业板': ak.stock_zh_index_spot_em(symbol="399006")
    }

    # 情绪数据
    limit_up = len(df[df['涨跌幅'] >= 9.5])
    limit_down = len(df[df['涨跌幅'] <= -9.5])

    return {
        'market': df,
        'indices': indices,
        'limit_up': limit_up,
        'limit_down': limit_down
    }
```

**资金数据**

```python
def fetch_fund_data():
    """获取资金流向数据"""
    # 北向资金
    hsgt = ak.stock_hsgt_fund_flow_summary_em()

    # 主力资金
    main_fund = ak.stock_main_fund_flow()

    # 板块资金流
    sector = ak.stock_board_industry_spot_em()

    return {
        'hsgt': hsgt,
        'main_fund': main_fund,
        'sector': sector
    }
```

### 0.2 新闻数据获取与AI整理

```python
def fetch_and_analyze_news():
    """获取并AI整理新闻数据"""
    # 获取龙虎榜（包含重要新闻线索）
    lhb = ak.stock_lhb_detail_em(
        start_date=(datetime.now() - timedelta(days=7)).strftime('%Y%m%d'),
        end_date=datetime.now().strftime('%Y%m%d')
    )

    # 获取业绩公告
    yjbb = ak.stock_yjbb_em(date="20241231")

    # AI整理后的新闻结构
    news_summary = {
        '政策面': [],
        '行业面': [],
        '公司面': [],
        '外盘': [],
        '情绪关键词': []
    }

    """
    AI分析要求：
    1. 从新闻中提取关键信息
    2. 判断对市场的影响（利好/利空/中性）
    3. 识别热点板块和题材
    4. 提取情绪关键词

    输出示例：
    {
        '政策面': ['新能源汽车补贴政策延续', 'AI产业扶持政策'],
        '行业面': ['液冷服务器概念爆发', '储能板块持续景气'],
        '公司面': ['圣阳股份7连板', '某公司重大重组'],
        '外盘': ['美股道指+0.5%', '纳指+0.8%'],
        '情绪关键词': ['龙头', '主升', '确认', '满仓']
    }
    """
    return news_summary
```

### 0.3 淘股吧舆情语料获取与AI整理

```python
def fetch_and_analyze_tgb_sentiment():
    """获取并AI整理淘股吧舆情数据"""
    date_str = datetime.now().strftime("%m-%d")

    # 读取当日语料
    corpus_file = f"a-stock-{datetime.now().strftime('%Y%m%d')}/data/tgb_{date_str}_corpus.txt"

    """
    AI分析要求：
    1. 统计正负面情绪词出现频率
    2. 识别高标股（连板股）讨论热度
    3. 提取市场热点话题
    4. 判断当前市场情绪倾向

    输出示例：
    {
        '正面词占比': '62%',
        '负面词占比': '18%',
        '中性词占比': '20%',
        '高标讨论热度': '圣阳股份7连板，讨论热度+150%',
        '热点话题': ['龙头', '主升', '确认买入'],
        '情绪倾向': '乐观'
    }
    """
    return sentiment_analysis
```

### 0.4 KOL观点总结

从淘股吧热帖中提取头部作者（KOL）的观点，进行AI汇总。

```python
def fetch_and_summarize_kol_opinions():
    """获取并AI整理KOL观点"""
    date_str = datetime.now().strftime("%m-%d")

    # 读取当日淘股吧列表（包含作者信息）
    list_file = f"a-stock-{datetime.now().strftime('%Y%m%d')}/data/tgb_{date_str}_list.txt"

    """
    KOL定义：
    - 粉丝数 > 10万
    - 或近30天发帖被点赞数 > 1000
    - 或龙头战法、情绪周期等主流理论创始人

    AI分析要求：
    1. 识别当日热帖作者中的KOL
    2. 提取KOL的核心观点（买什么/怎么看市场）
    3. 判断KOL之间的共识和分歧
    4. 给出KOL观点的可信度评分

    输出示例：
    {
        'kol_opinions': [
            {
                'author': '龙头泰山',
                'followers': '50万',
                'viewpoint': '圣阳股份是这波行情的总龙头，8板可以期待',
                'confidence': 85,
                'tags': ['龙头', '连板', '满仓']
            },
            {
                'author': '作手阿意',
                'followers': '30万',
                'viewpoint': '圣阳周期深度拆解，注意7板后的分歧风险',
                'confidence': 78,
                'tags': ['周期', '分歧', '谨慎']
            }
        ],
        'consensus': '多数KOL看好圣阳，但提醒高位风险',
        'divergence': '部分KOL已开始关注补涨标的',
        'actionable': '关注圣阳分歧后的低吸机会'
    }
    """
    return kol_summary
```

### 0.5 记忆加载（滑动窗口）

记忆文件存储在当前workspace下，持久化为md文件：

```
a-stock-YYYYMMDD/
├── 00-大盘上下文.md         # 当日判市结果
├── 01-策略大纲.md           # 当日选股结果
├── 02-标的观察池.md         # 当日观察池
├── short_term_memory.md     # 短期记忆（近1周）持久化
├── long_term_memory.md      # 长期记忆（近1月）持久化
├── data/
│   ├── market_YYYYMMDD.csv
│   ├── sentiment_YYYYMMDD.json
│   ├── fund_flow_YYYYMMDD.json
│   ├── sector_rank_YYYYMMDD.json
│   ├── news_YYYYMMDD.json
│   ├── tgb_YYYYMMDD_corpus.txt
│   └── tgb_list_YYYYMMDD.txt
├── logs/
└── 标的分析/
```

```python
def generate_short_term_memory():
    """生成短期记忆并持久化为md（近1周）"""
    today = datetime.now()
    date_str = today.strftime('%Y%m%d')
    workspace = f"a-stock-{date_str}"

    week_data = []
    for i in range(1, 8):  # 近7天
        date = (today - timedelta(days=i)).strftime('%Y%m%d')
        historical_workspace = f"a-stock-{date}"

        # 读取历史情绪数据
        sentiment_file = f"{historical_workspace}/data/sentiment_{date}.json"
        fund_file = f"{historical_workspace}/data/fund_flow_{date}.json"

        # AI提炼关键信息
        week_summary = {
            'date': date,
            '涨停均值': '...',
            '资金流向': '...',
            '热点板块': '...',
            '情绪变化': '...'
        }
        week_data.append(week_summary)

    # 持久化为md文件
    md_content = "# 短期记忆（近1周）\n\n"
    md_content += f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"

    for item in week_data:
        md_content += f"## {item['date']}\n"
        md_content += f"- 涨停均值: {item['涨停均值']}\n"
        md_content += f"- 资金流向: {item['资金流向']}\n"
        md_content += f"- 热点板块: {item['热点板块']}\n"
        md_content += f"- 情绪变化: {item['情绪变化']}\n\n"

    # 写入文件
    with open(f"{workspace}/short_term_memory.md", 'w', encoding='utf-8') as f:
        f.write(md_content)

    return week_data

def generate_long_term_memory():
    """生成长期记忆并持久化为md（近1月）"""
    today = datetime.now()
    date_str = today.strftime('%Y%m%d')
    workspace = f"a-stock-{date_str}"

    month_data = []
    for i in range(1, 31):  # 近30天
        date = (today - timedelta(days=i)).strftime('%Y%m%d')
        historical_workspace = f"a-stock-{date}"

        # 读取大盘上下文
        context_file = f"{historical_workspace}/00-大盘上下文.md"

        # AI提炼关键信息
        month_summary = {
            'date': date,
            '安全等级': '...',
            '市场特征': '...',
            '重点标的': '...',
            '操作结果': '...'
        }
        month_data.append(month_summary)

    # 持久化为md文件
    md_content = "# 长期记忆（近1月）\n\n"
    md_content += f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"

    for item in month_data:
        md_content += f"## {item['date']}\n"
        md_content += f"- 安全等级: {item['安全等级']}\n"
        md_content += f"- 市场特征: {item['市场特征']}\n"
        md_content += f"- 重点标的: {item['重点标的']}\n"
        md_content += f"- 操作结果: {item['操作结果']}\n\n"

    # 写入文件
    with open(f"{workspace}/long_term_memory.md", 'w', encoding='utf-8') as f:
        f.write(md_content)

    return month_data

def load_memory():
    """加载记忆（优先从md文件读取）"""
    today = datetime.now()
    date_str = today.strftime('%Y%m%d')
    workspace = f"a-stock-{date_str}"

    short_term_file = f"{workspace}/short_term_memory.md"
    long_term_file = f"{workspace}/long_term_memory.md"

    short_term = []
    long_term = []

    # 读取短期记忆
    if os.path.exists(short_term_file):
        with open(short_term_file, 'r', encoding='utf-8') as f:
            content = f.read()
            # AI解析md内容，提取关键信息
            short_term = parse_short_term_memory(content)

    # 读取长期记忆
    if os.path.exists(long_term_file):
        with open(long_term_file, 'r', encoding='utf-8') as f:
            content = f.read()
            # AI解析md内容，提取关键信息
            long_term = parse_long_term_memory(content)

    return short_term, long_term

def merge_memory_for_context():
    """合并记忆生成上下文"""
    short_term, long_term = load_memory()

    context = {
        '近期趋势': [],      # 短期记忆提炼
        '市场特征': [],      # 长期记忆提炼
        '规律发现': [],      # AI发现的规律
        '注意事项': []       # 历史教训
    }

    """
    AI处理要求：
    1. 从近7天数据提炼短期趋势（涨停家数变化、资金流向变化）
    2. 从近30天数据提炼市场特征（什么情况下容易赚钱/亏钱）
    3. 发现规律（热点板块轮动规律、高标股特征）
    4. 记录历史教训（避免重复犯错）
    """

    return context
```

### 0.6 数据准备输出

```markdown
# 数据准备报告 - 20251229

## 行情数据
- 全市场股票数：5862只
- 涨停：52家 / 跌停：6家
- 指数：上证 +0.52%，深证 +0.63%

## 资金数据
- 北向：+48亿（连续7日净流入）
- 主力：+62亿
- 热点板块：液冷服务器、储能、白酒

## 新闻AI整理
- 政策面：新能源汽车补贴延续、AI产业扶持
- 行业面：液冷服务器爆发、储能持续景气
- 外盘：美股收涨，道指+0.5%

## 舆情AI整理
- 正面词占比：62%（乐观）
- 高标热度：圣阳7连板，讨论热度+150%
- 情绪倾向：高涨

## KOL观点总结
- **龙头泰山**：圣阳是总龙头，8板可期待，满仓干
- **作手阿意**：7板后注意分歧风险，周期深度拆解
- **共识**：多数KOL看好圣阳，但提醒高位风险
- **分歧**：部分已开始关注补涨标的
- **可操作**：圣阳分歧后低吸机会

## 记忆上下文
### 短期记忆（近1周）
- 涨停均值：45家/天，趋势向上
- 资金持续净流入
- 热点：液冷服务器贯穿全周

### 长期记忆（近1月）
- 安全等级：多数日子在🟢-🟡
- 高标股特征：7板以上慎追
- 板块轮动：每3-5天切换一次

### 记忆持久化
- ✅ short_term_memory.md（已生成）
- ✅ long_term_memory.md（已生成）

## 结论
当前市场环境适合积极操作
```

---

## Step 1: 判市

见 `Market_Assessment.md`

---

## Step 2: 选股

见 `Stock_Screening.md`

---

## Step 3: 诊股

见 `Stock_Diagnosis.md`

---

## Step 4: 策略

见 `Trading_Strategy.md`

---

## Step 5: 复盘

见 `EOD_Review.md`

---

## 工作目录结构

```
a-stock-YYYYMMDD/
├── 00-大盘上下文.md         # 判市结果 + 复盘更新
├── 01-策略大纲.md           # 选股结果
├── 02-标的观察池.md         # 观察池
├── trading-plan.json       # 交易计划
├── data/                   # 数据目录
│   ├── market_YYYYMMDD.csv
│   ├── sentiment_YYYYMMDD.json
│   ├── fund_flow_YYYYMMDD.json
│   ├── sector_rank_YYYYMMDD.json
│   ├── news_YYYYMMDD.json
│   └── tgb_YYYYMMDD_corpus.txt
├── logs/
└── 标的分析/
```

---

## 使用示例

```bash
# 完整流程（包含数据准备）
python scripts/mode_selector.py --step all

# 单步执行（自动先执行数据准备）
python scripts/mode_selector.py --step market
python scripts/mode_selector.py --step stock
python scripts/mode_selector.py --step diagnosis
python scripts/mode_selector.py --step strategy
python scripts/mode_selector.py --step review

# 仅数据准备（不执行任何功能）
python scripts/mode_selector.py --step prepare
```

---

## 状态流转

```
每日流程：
Step 0（数据准备）→ Step 1（判市）→ Step 2（选股）→ Step 3（诊股）→ Step 4（策略）→ Step 5（复盘）

状态标记：
- pending：待执行
- preparing：数据准备中
- scanning：执行中
- done：已完成
- failed：失败
```

---

## 关键规则

1. **任何功能执行前，必须先完成数据准备（Step 0）**
2. **数据准备时，AI必须同时分析新闻和舆情**
3. **记忆加载时，AI必须提炼关键信息而非简单罗列**
4. **复盘后必须更新记忆，供次日使用**