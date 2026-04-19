# A股量化投研・共享基础设施

本文件定义跨策略、跨周期共享的机制、规则与数据结构。

---

## 一、每日工作区

### 目录结构

```
workspace/stock-YYYYMMDD/
├── 00-大盘上下文.md         # 当日市场大盘、新闻、情绪
├── 01-策略大纲.md           # 当日策略总纲
├── 02-标的观察池.md         # 关注股票列表
├── trading-plan.json       👈 当日交易计划
├── backtest/               👈 回测结果目录
├── logs/                   👈 运行日志
└── 标的分析/               👈 股票分析记录
    ├── 600000-某某股份.md
    └── 000001-平安银行.md
```

### 大盘上下文内容

```markdown
# 大盘上下文 - 20251229

## 指数状态
- 上证：XXXX（+X%）
- 深证：XXXX（+X%）
- 创业板：XXXX（+X%）

## 市场情绪
- 涨停：XX家 / 跌停：XX家
- 炸板率：XX%
- 情绪等级：🟢高涨 / 🟡一般 / 🔴低迷

## 资金动向
- 北向：+XX亿（净买入/净卖出）
- 主力：+XX亿
- 热点板块：XXX、XXX

## 重要新闻
1. [政策] XXXXXXXXX
2. [行业] XXXXXXXXX
3. [公司] XXXXXXXXX

## 明日展望
- 情绪预期：延续/退潮
- 重点关注：XXX板块
- 风险提示：XXXXXX
```

---

## 二、稳健盈利四原则

| 原则 | 说明 |
|------|------|
| **趋势驱动** | 只做顺势结构，不逆势 |
| **盈亏波动** | 控制单笔亏损，赚大亏小 |
| **信号记忆** | 关键形态形成可复现入场信号 |
| **关键节点** | 每段行情有突破/回踩/止盈节点 |

---

## 三、用户偏好系统

### 存储文件

`workspace/user-preferences.json`

```json
{
  "preferences": {
    "favoriteMarkets": ["A股主板", "创业板"],
    "preferredIndicators": ["MA20", "MACD", "KDJ"],
    "preferredStyle": "趋势/波段/短线",
    "riskLevel": "保守/稳健/激进",
    "maxSinglePosition": 0.3,
    "holdDays": 5,
    "blacklistStocks": [],
    "whitelistIndustries": []
  }
}
```

### 更新规则

| 时机 | 行为 |
|------|------|
| 每完成一个阶段 | 静默同步 |
| 用户说"记住偏好" | 全量保存 |
| 用户说"忘记 XX" | 清除指定项 |
| 用户说"重置偏好" | 清空恢复默认 |

---

## 四、交易计划系统

### 文件

`workspace/stock-YYYYMMDD/trading-plan.json`

```json
{
  "version": 1,
  "date": "20251229",
  "status": "planning",
  "style": "波段",
  "stocks": [
    {
      "code": "600000",
      "name": "某某股份",
      "status": "pending",
      "entryPrice": null,
      "stopLossPrice": null,
      "takeProfitPrice": null,
      "keyNode": "突破/回踩"
    }
  ]
}
```

### 状态流转

```
planning → scanning → positioning → monitoring → closed
                              ↓
                           failed（最多重试3次）
```

---

## 五、风控规则

### 仓位公式

```
单票仓位 = 账户 × 风险占比 ÷ 单股风险金额

示例：账户10万，风险2%，止损4%
→ 单票仓位 = 100000 × 0.02 / 0.04 = 50000元（50%）
```

### 风控红线

| 规则 | 处理 |
|------|------|
| 单票仓位 > 30% | 降仓 |
| 总仓位 > 80% | 谨慎 |
| 行业集中度 > 50% | 分散 |
| 持仓 > 10只 | 减少 |

---

## 六、信号类型

| 信号 | 条件 |
|------|------|
| 突破 | 放量 + 站稳均线 + 创新高 |
| 回踩 | 价格回撤 + 缩量 + 获支撑 |
| 反转 | 指标背离 + 资金净流入 |
| 趋势 | 均线多头（MA5>MA20>MA60） |
| 量能 | 价涨量增 + 换手率>3% |

---

## 七、选股框架

```
趋势型：沿MA20 → 回踩企稳 → 放量突破
短线型：超跌(KDJ J<20) → 金叉 → 量能放大
波段型：平台整理 → 突破 → 回踩确认
```

---

## 八、数据接口

```python
import akshare as ak

# 实时行情
ak.stock_zh_a_spot_em()

# 资金流向
ak.stock_hsgt_fund_flow_summary_em()  # 北向
ak.stock_main_fund_flow()              # 主力

# K线数据
ak.stock_zh_a_hist(symbol, period="daily", start_date, end_date, adjust="qfq")
```

---

## 九、日志规范

```bash
# 日志格式
[YYYY-MM-DD HH:mm:ss] [LEVEL] [模块] 消息

# 日志文件
workspace/stock-YYYYMMDD/logs/
├── run.log    # 运行日志
├── trade.log  # 交易日志
└── error.log  # 错误日志
```