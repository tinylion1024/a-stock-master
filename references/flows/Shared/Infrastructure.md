# A股量化投研・共享基础设施

本文件定义跨策略、跨周期共享的机制、规则与数据结构，适用于 AI 辅助选股、策略回测、实盘跟踪与风控体系。

---

## 一、每日工作区规则（自动创建）

### 核心规则

- 每天自动创建：以当日日期命名的独立工作区
- 路径固定：所有策略、数据、计划、日志统一存放
- 不跨天混用：当日策略 → 当日目录，干净可追溯

### 目录命名格式

```
workspace/
└── stock-YYYYMMDD/      👈 每天自动生成

示例：
workspace/stock-20251229
```

### 自动创建逻辑

1. 工具启动时自动检查当日目录是否存在
2. 不存在 → 立即创建
3. 存在 → 直接进入当日工作区
4. 所有当日产出强制写入当日目录

---

## 二、每日工作区内部结构

```
workspace/stock-YYYYMMDD/
├── 00-策略大纲.md           # 当日策略总纲
├── 01-标的观察池.md         # 关注股票列表
├── trading-plan.json       👈 当日交易计划
├── backtest/               👈 回测结果目录
├── logs/                   👈 运行日志目录
└── 标的分析/               👈 股票分析记录
    ├── 600000-某某股份.md
    └── 000001-平安银行.md
```

---

## 三、稳健盈利四原则（纯金融版）

| 原则 | 说明 | 操作要求 |
|------|------|----------|
| **趋势驱动** | 只做顺势结构，不逆势抄底摸顶 | 均线多头才买，空头排则卖 |
| **盈亏波动** | 控制最大回撤，赚大亏小 | 单笔亏损 ≤ 2%，单笔盈利 ≥ 5% |
| **信号记忆** | 关键形态/指标形成可复现入场信号 | 记录每次入场理由，形成信号库 |
| **关键节点** | 每段行情必须有突破/回踩/反转/止盈节点 | 每个持仓必须有明确出场计划 |

---

## 四、用户偏好系统

### 存储文件

`workspace/user-preferences.json`（全局唯一，不按天创建）

### 数据结构

```json
{
  "version": 2,
  "updatedAt": "2025-12-29",
  "preferences": {
    "favoriteMarkets": ["A股主板", "创业板", "科创板"],
    "preferredIndicators": ["MA20", "MACD", "KDJ", "量比"],
    "preferredStyle": "趋势/波段/短线",
    "preferredTimeframe": "日线/60分钟/30分钟",
    "riskLevel": "保守/稳健/激进",
    "maxSinglePosition": 0.3,
    "maxDrawdownLimit": 0.15,
    "holdDays": 5,
    "blacklistStocks": [],
    "whitelistIndustries": [],
    "strategyHistory": []
  }
}
```

### 偏好更新规则

| 时机 | 行为 |
|------|------|
| 每完成一个阶段 | 静默同步 |
| 用户说"记住偏好" | 全量保存 |
| 用户说"忘记 XX" | 清除指定项 |
| 用户说"重置偏好" | 清空恢复默认 |
| 策略/回测完成 | 写入历史 |

---

## 五、交易计划系统

### 存储文件

`workspace/stock-YYYYMMDD/trading-plan.json`

### 作用

- 当日标的状态跟踪
- 策略模式记录
- 关键节点（突破/回踩/止损/止盈）记录
- 中断续跑
- 最终校验依据

### JSON 结构

```json
{
  "version": 3,
  "strategyName": "当日策略",
  "workspace": "./workspace/stock-YYYYMMDD",
  "totalStocks": 10,
  "createdAt": "2025-12-29T10:00:00Z",
  "status": "planning",
  "tradingMode": "single-batch",
  "coreSetting": {
    "style": "波段",
    "timeframe": "日线",
    "indicators": ["MA20", "MACD"]
  },
  "stocks": [
    {
      "code": "600000",
      "name": "浦发银行",
      "industry": "银行",
      "status": "pending",
      "entryPrice": null,
      "stopLossPrice": null,
      "takeProfitPrice": null,
      "keyNode": "突破/回踩",
      "retryCount": 0
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

## 六、仓位与风控脚本

### 仓位计算

```python
# 仓位计算公式
单票仓位 = 账户总资产 × 风险占比 ÷ 单股风险金额

# 示例
账户：100,000 元
风险占比：2%（单票最大亏损）
入场价：12.50
止损价：12.00（-4%）
每股风险：0.50 元

单票仓位 = 100000 × 0.02 / 0.50 = 4000 股
买入金额 = 4000 × 12.50 = 50,000 元
仓位占比 = 50%
```

### 风控检查

```python
风控检查清单 = [
    ('单票仓位 > 30%', '超仓，降仓'),
    ('总仓位 > 80%', '仓位过重，谨慎'),
    ('行业集中度 > 50%', '集中风险，分散'),
    ('持仓 > 10只', '过于分散，减少'),
    ('回撤 > 15%', '触发风控，暂停策略'),
]
```

### 运行命令

```bash
# 检查单只股票
python check_position_risk.py ./workspace/stock-20251229/600000.json

# 检查当日全部
python check_position_risk.py --all ./workspace/stock-20251229/
```

---

## 七、盈利信号类型速查

| 信号类型 | 适用场景 | 核心特征 |
|----------|----------|----------|
| 突破信号 | 放量突破平台 | 放量 + 站稳均线 + 创近期新高 |
| 回踩信号 | 回踩不破支撑 | 价格回踩 + 缩量 + 获支撑 |
| 反转信号 | 底部背离、资金回流 | 指标背离 + 资金净流入 |
| 趋势信号 | 均线多头排列 | MA5 > MA20 > MA60 |
| 量能信号 | 量价配合、资金进场 | 价格上涨 + 成交量放大 |

---

## 八、信号判断公式

```
突破信号：放量突破 + 站稳均线
  → 条件1：成交量 > 均量1.5倍
  → 条件2：收盘价 > 20日均线
  → 条件3：突破前高

回踩信号：回踩不破支撑 + 缩量
  → 条件1：价格回撤至支撑位
  → 条件2：成交量 < 5日均量
  → 条件3：止跌回升

反转信号：指标背离 + 资金回流
  → 条件1：价格创新低，指标未创新低
  → 条件2：资金净流入
  → 条件3：K线出现止跌形态

趋势信号：均线多头排列
  → 条件1：MA5 > MA20
  → 条件2：MA20 > MA60
  → 条件3：价格在各均线上方

量能信号：量价配合、资金进场
  → 条件1：价格涨 + 成交量涨
  → 条件2：资金净流入 > 0
  → 条件3：换手率 > 3%
```

---

## 九、核心选股框架

### 趋势型

```
沿20日线 → 回踩企稳 → 放量突破
  步骤1：股价在MA20上方
  步骤2：回踩MA20获支撑
  步骤3：放量阳线突破前高
  步骤4：回踩不破MA20买入
```

### 短线型

```
超跌 → 金叉 → 量能放大
  步骤1：KDJ J值 < 20（超跌）
  步骤2：KDJ K值从下往上穿越D值（金叉）
  步骤3：成交量放大至均量2倍
  步骤4：次日开盘买入
```

### 波段型

```
平台整理 → 突破 → 回踩确认
  步骤1：股价在20-30%区间震荡
  步骤2：放量突破区间高点
  步骤3：回踩不破区间高点
  步骤4：缩量确认后买入
```

---

## 十、AI 投研 10 阶段流程

```
Phase 0 → Phase 1 → Phase 2 → Phase 3 → Phase 4
初始化   市场分析  风格确定  标的池    参数配置
    │                                       │
    └───────────────────────────────────────┘
    ↓
Phase 9 ← Phase 8 ← Phase 7 ← Phase 6 ← Phase 5
校验完成  退出规划  风控优化  回测验证  交易计划
```

| 阶段 | 名称 | 输出 |
|------|------|------|
| Phase 0 | 初始化 | 创建当日工作区，加载用户偏好 |
| Phase 1 | 市场分析 | 判市结果（安全等级/仓位建议） |
| Phase 2 | 风格确定 | 确定交易模式（激进/稳健/长线） |
| Phase 3 | 标的池 | 选股结果（重点关注池） |
| Phase 4 | 参数配置 | 入场/止损/止盈参数设定 |
| Phase 5 | 交易计划 | 生成 trading-plan.json |
| Phase 6 | 回测验证 | 历史数据验证策略有效性 |
| Phase 7 | 风控优化 | 调整仓位和止损参数 |
| Phase 8 | 退出规划 | 制定止盈止损路径 |
| Phase 9 | 校验完成 | 最终确认，输出执行 |

---

## 十一、策略执行模式

| 模式 | 说明 | 适用场景 |
|------|------|----------|
| `single-batch` | 单线程逐只筛选（默认） | 少量标的，精确分析 |
| `parallel-scan` | 多标的并行扫描 | 快速筛选大量股票 |
| `ai-team` | 多 AI 分工协作 | 复杂任务，团队作战 |

### 执行模式切换

```python
# 在 trading-plan.json 中设置
"tradingMode": "single-batch"  # 或 "parallel-scan" 或 "ai-team"
```

---

## 十二、数据接口规范

### 实时行情获取

```python
import akshare as ak

def get_realtime_quotes():
    """获取沪深京A股实时行情"""
    return ak.stock_zh_a_spot_em()

def get_limit_up_stocks():
    """获取涨停股票"""
    df = get_realtime_quotes()
    return df[df['涨跌幅'] >= 9.5]
```

### 资金流向获取

```python
def get_hsgt_fund():
    """获取北向资金"""
    return ak.stock_hsgt_fund_flow_summary_em()

def get_main_fund():
    """获取主力资金"""
    return ak.stock_main_fund_flow()

def get_individual_fund(symbol="即时"):
    """获取个股资金流"""
    return ak.stock_fund_flow_individual(symbol=symbol)
```

### 历史数据获取

```python
def get_kline_data(symbol, start_date, end_date, adjust="qfq"):
    """获取K线数据"""
    return ak.stock_zh_a_hist(
        symbol=symbol,
        period="daily",
        start_date=start_date,
        end_date=end_date,
        adjust=adjust
    )
```

---

## 十三、日志规范

### 日志级别

| 级别 | 用途 | 颜色标识 |
|------|------|----------|
| INFO | 正常流程信息 | 白色 |
| WARNING | 需要关注但不阻塞 | 黄色 |
| ERROR | 操作失败 | 红色 |
| SUCCESS | 操作成功 | 绿色 |

### 日志格式

```
[YYYY-MM-DD HH:mm:ss] [LEVEL] [模块] 消息内容

示例：
[2025-12-29 14:30:15] [INFO] [选股] 完成筛选，共23只股票符合条件
[2025-12-29 14:30:18] [WARNING] [风控] 单票仓位25%超过建议值
[2025-12-29 14:30:20] [ERROR] [数据] 获取600000行情失败
[2025-12-29 14:30:25] [SUCCESS] [交易] 买入平安银行，成本价12.50
```

### 日志文件

```
workspace/stock-YYYYMMDD/logs/
├── run.log          # 运行日志
├── trade.log        # 交易日志
└── error.log        # 错误日志
```

---

## 十四、异常处理规范

### 异常类型

```python
class DataFetchError(Exception):
    """数据获取异常"""
    pass

class ValidationError(Exception):
    """数据校验异常"""
    pass

class PositionError(Exception):
    """仓位异常"""
    pass

class RiskControlError(Exception):
    """风控触发异常"""
    pass
```

### 安全获取数据

```python
def safe_get_data(func, fallback=None, error_msg="获取数据失败"):
    """安全获取数据"""
    try:
        return func()
    except Exception as e:
        logging.error(f"{error_msg}: {e}")
        return fallback
```

---

## 十五、版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v1 | 2025-01-01 | 初始版本 |
| v2 | 2025-06-01 | 增加用户偏好系统 |
| v3 | 2025-12-29 | 增加交易计划系统，扩展风控规则 |