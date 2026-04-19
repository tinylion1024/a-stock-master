# A股大师 (A-Stock Master)

A 股投资分析助手，基于 AKShare 提供的数据，辅助投资者进行股票筛选、技术分析和交易决策。

## 五大核心功能

### 1️⃣ 判市（Market Assessment）
判断市场环境是否安全，能否开仓
- 指数状态（均线多头/空头/缠绕）
- 情绪指标（涨停/跌停家数、炸板率）
- 资金状态（北向/主力/融资）
- 安全等级（🟢绿/🟡黄/🔴红）

### 2️⃣ 选股（Stock Screening）
从 5000+ 只股票中筛选重点关注池
- 基础筛选（非ST、流动性、PE>0）
- 量化筛选（价值/成长/技术/资金/突破）
- 排序评分（综合排名）
- 人工复核（行业逻辑、消息催化）

### 3️⃣ 诊股（Stock Diagnosis）
单只股票五维质量打分
- 趋势分（25%）：均线、MACD、KDJ
- 资金分（25%）：北向、主力、融资
- 人气分（20%）：换手率、研报、热度
- 情绪分（15%）：涨停、连板、溢价
- 基本面分（15%）：PE、PB、ROE、增速

### 4️⃣ 策略（Trading Strategy）
制定完整交易计划
- 择时（打板/回封/突破/低吸）
- 仓位（根据评分动态调整）
- 止损（固定+移动止损）
- 止盈（分批卖出）
- 目标价计算

### 5️⃣ 复盘（EOD Review）
每日收盘后总结
- 市场总结（指数/情绪/资金/事件）
- 操作检讨（选股/买点/仓位/止损/止盈）
- 问题分析（亏损原因、改进措施）
- 明日计划（市场预期、操作标的）

## 目录结构

```
a-stock-master/
├── SKILL.md
├── references/
│   ├── flows/
│   │   ├── 01-Market/           # 判市
│   │   │   └── Market_Assessment.md
│   │   ├── 02-Stock/           # 选股
│   │   │   └── Stock_Screening.md
│   │   ├── 03-Diagnosis/       # 诊股
│   │   │   └── Stock_Diagnosis.md
│   │   ├── 04-Strategy/        # 策略
│   │   │   └── Trading_Strategy.md
│   │   ├── 05-Review/           # 复盘
│   │   │   └── EOD_Review.md
│   │   └── Shared/              # 共享基础设施
│   │       └── Infrastructure.md
│   ├── mode/                    # 模式选择
│   │   └── Mode_Selector.md
│   └── guides/
│       └── technical-analysis-guide.md
└── scripts/
    ├── market_scanner.py        # 判市扫描
    ├── stock_screener.py        # 智能选股
    ├── stock_diagnosis.py       # 诊股分析
    ├── strategy_builder.py      # 策略制定
    ├── eod_reviewer.py          # 复盘工具
    ├── stock_*.py               # 其他工具脚本
    └── tgb_spider.py            # 淘股吧爬虫
```

## 使用流程

```
每日操作流程：

1. 开盘前（9:15-9:30）
   → 执行判市 → 判断能否开仓

2. 盘中（9:30-15:00）
   → 执行选股 → 筛选关注池
   → 执行诊股 → 给股票打分
   → 执行策略 → 制定买卖计划

3. 收盘后（15:30-16:00）
   → 执行复盘 → 总结经验教训
```

## 快速开始

```python
import akshare as ak

# 获取实时行情
df = ak.stock_zh_a_spot_em()

# 筛选低估值股票
low_pe = df[(df['市盈率-动态'] > 0) & (df['市盈率-动态'] < 15)]
print(low_pe[['代码', '名称', '最新价', '涨跌幅']])
```

## 使用限制

- 数据来源为 AKShare，免费数据可能有延迟
- 本工具仅供辅助参考，不构成投资建议
- 股市有风险，投资需谨慎