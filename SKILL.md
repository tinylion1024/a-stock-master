# A股大师 (A-Stock Master)

A 股投资分析助手，基于 AKShare 提供的数据，辅助投资者进行股票筛选、技术分析和基本面分析。

## 核心能力

- **实时行情**：获取 A 股实时价格、涨跌幅、成交量等
- **技术分析**：均线、K 线形态、MACD、KDJ 等技术指标
- **基本面筛选**：市值、PE、PB、ROE 等财务指标筛选
- **板块监测**：行业板块涨跌监控，热点追踪
- **消息面分析**：个股新闻、龙虎榜、业绩公告、情绪关键词
- **社区舆情**：淘股吧帖子爬取，热帖监测、作者筛选
- **形态识别**：K 线组合形态识别（锤子线、吞没、十字星等）

## 适用场景

- 短线选股：基于技术形态和资金流向
- 中线布局：基于基本面筛选和行业趋势
- 板块轮动：追踪热点板块和龙头股
- 自选股监控：定期生成持仓分析报告

## 目录结构

```
a-stock-master/
├── SKILL.md                         # 技能定义
├── references/
│   ├── flows/
│   │   └── analysis-flow.md        # 分析流程（市场→板块→个股→技术→买入）
│   └── guides/
│       └── technical-analysis-guide.md  # 技术分析准则（K线形态、均线、指标）
└── scripts/
    ├── stock_quotes.py             # 实时行情监控
    ├── stock_fund_flow.py          # 资金流向分析
    ├── stock_technical.py          # 技术指标计算
    ├── stock_sector.py             # 板块分析
    ├── stock_financial.py          # 基本面分析
    ├── stock_screener.py           # 智能选股器
    ├── stock_news.py               # 消息面分析
    ├── stock_analysis_report.py    # 综合分析报告
    └── tgb_spider.py               # 淘股吧爬虫
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