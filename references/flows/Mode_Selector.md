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

### 0.4 记忆加载（滑动窗口）

```
短期记忆（近1周）：
└── a-stock-YYYYMMDD/data/ 中的历史数据
    ├── 过去7天的 sentiment_*.json
    ├── 过去7天的 fund_flow_*.json
    └── 过去7天的 market_*.csv

长期记忆（近1月）：
└── a-stock-YYYYMMDD/ 中的历史大盘上下文
    ├── 00-大盘上下文.md（过去30天）
    └── 标的分析/（过去30天的重要标的复盘）
```

```python
def load_short_term_memory():
    """加载短期记忆（近1周）"""
    today = datetime.now()
    week_data = []

    for i in range(1, 8):  # 近7天
        date = (today - timedelta(days=i)).strftime('%Y%m%d')
        workspace = f"a-stock-{date}"

        # 读取情绪数据
        sentiment_file = f"{workspace}/data/sentiment_{date}.json"
        # 读取资金数据
        fund_file = f"{workspace}/data/fund_flow_{date}.json"

        # AI提炼关键信息
        week_summary = {
            'date': date,
            '涨停均值': '...',
            '资金流向': '...',
            '热点板块': '...',
            '情绪变化': '...'
        }
        week_data.append(week_summary)

    return week_data

def load_long_term_memory():
    """加载长期记忆（近1月）"""
    today = datetime.now()
    month_data = []

    for i in range(1, 31):  # 近30天
        date = (today - timedelta(days=i)).strftime('%Y%m%d')
        workspace = f"a-stock-{date}"

        # 读取大盘上下文
        context_file = f"{workspace}/00-大盘上下文.md"

        # AI提炼关键信息
        month_summary = {
            'date': date,
            '安全等级': '...',
            '市场特征': '...',
            '重点标的': '...',
            '操作结果': '...'
        }
        month_data.append(month_summary)

    return month_data

def merge_memory_for_context():
    """合并记忆生成上下文"""
    short_term = load_short_term_memory()
    long_term = load_long_term_memory()

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

### 0.5 数据准备输出

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

## 记忆上下文
### 短期记忆（近1周）
- 涨停均值：45家/天，趋势向上
- 资金持续净流入
- 热点：液冷服务器贯穿全周

### 长期记忆（近1月）
- 安全等级：多数日子在🟢-🟡
- 高标股特征：7板以上慎追
- 板块轮动：每3-5天切换一次

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