# Shared_Infrastructure 通用基础设施

三种模式共用的核心数据接口和工具函数。

## 1. 数据获取接口

### 1.1 实时行情

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

### 1.2 资金流向

```python
def get_fund_flow(symbol="即时"):
    """获取资金流向"""
    return ak.stock_fund_flow_individual(symbol=symbol)

def get_main_fund():
    """获取主力资金"""
    return ak.stock_main_fund_flow()

def get_hsgt_fund():
    """获取北向资金"""
    return ak.stock_hsgt_fund_flow_summary_em()
```

### 1.3 板块数据

```python
def get_concept_boards():
    """获取概念板块"""
    return ak.stock_board_concept_spot_em()

def get_industry_boards():
    """获取行业板块"""
    return ak.stock_board_industry_spot_em()
```

### 1.4 龙虎榜

```python
def get_lhb_details(start_date, end_date):
    """获取龙虎榜详情"""
    return ak.stock_lhb_detail_em(start_date, end_date)
```

## 2. 通用函数

### 2.1 数据清洗

```python
def clean_stock_data(df):
    """清洗股票数据"""
    df = df[df['市盈率-动态'] > 0]  # 排除负PE
    df = df[df['总市值'] > 10e8]    # 排除小市值
    df = df[~df['名称'].str.contains('ST')]  # 排除ST
    return df

def calculate_change_percent(current, previous):
    """计算涨跌幅"""
    return (current - previous) / previous * 100
```

### 2.2 技术指标

```python
def calculate_ma(series, window):
    """计算移动平均线"""
    return series.rolling(window=window).mean()

def calculate_macd(prices, fast=12, slow=26, signal=9):
    """计算MACD"""
    ema_fast = prices.ewm(span=fast).mean()
    ema_slow = prices.ewm(span=slow).mean()
    dif = ema_fast - ema_slow
    dea = dif.ewm(span=signal).mean()
    macd = (dif - dea) * 2
    return dif, dea, macd

def calculate_kdj(high, low, close, n=9, m1=3, m2=3):
    """计算KDJ"""
    low_n = low.rolling(window=n).min()
    high_n = high.rolling(window=n).max()
    rsv = (close - low_n) / (high_n - low_n) * 100
    k = rsv.ewm(com=m1-1).mean()
    d = k.ewm(com=m2-1).mean()
    j = 3 * k - 2 * d
    return k, d, j
```

### 2.3 评分计算

```python
def normalize_score(series, higher_is_better=True):
    """因子标准化（0-100分）"""
    min_val = series.min()
    max_val = series.max()
    if higher_is_better:
        return (series - min_val) / (max_val - min_val) * 100
    else:
        return (max_val - series) / (max_val - min_val) * 100

def calculate_weighted_score(factors_dict, weights_dict):
    """计算加权得分"""
    total_score = 0
    total_weight = 0
    for factor, weight in weights_dict.items():
        if factor in factors_dict:
            total_score += factors_dict[factor] * weight
            total_weight += weight
    return total_score / total_weight if total_weight > 0 else 0
```

### 2.4 风险计算

```python
def calculate_position_size(account, risk_percent, entry, stop_loss):
    """计算仓位"""
    risk_amount = account * risk_percent
    risk_per_share = abs(entry - stop_loss)
    shares = int(risk_amount / risk_per_share)
    position_value = shares * entry
    position_percent = position_value / account * 100
    return shares, position_value, position_percent

def calculate_odds(entry, target, stop_loss):
    """计算赔率"""
    potential_profit = target - entry
    potential_loss = entry - stop_loss
    return potential_profit / potential_loss if potential_loss > 0 else 0
```

## 3. 配置文件

### 3.1 默认参数

```python
# 交易参数默认值
DEFAULT_PARAMS = {
    # 仓位
    'max_position_per_stock': 25,  # 单票最大仓位%
    'max_total_position': 80,      # 总仓位上限%
    'max_sector_concentration': 40, # 行业集中度上限%

    # 止损
    'sentiment_stop_loss': -5,      # 情绪模式止损%
    'quantitative_stop_loss': -6,    # 量化模式止损%
    'institutional_stop_loss': -10,  # 机构模式止损%

    # 止盈
    'sentiment_take_profit': 10,    # 情绪模式止盈%
    'quantitative_take_profit': 18,  # 量化模式止盈%
    'institutional_take_profit': 25, # 机构模式止盈%

    # 风控
    'risk_per_trade': 0.02,         # 单笔风险比例
    'max_drawdown': 0.15,           # 最大回撤
}

# 因子权重
DEFAULT_FACTOR_WEIGHTS = {
    '价值': 0.25,
    '成长': 0.25,
    '技术': 0.25,
    '量价': 0.25,
}
```

### 3.2 模式参数

```python
MODE_PARAMS = {
    'Fast': {
        'min_limit_up': 30,
        'max_position': 30,
        'stop_loss': -5,
        'take_profit': 10,
        'holding_period': '日内',
    },
    'Pro': {
        'min_score': 60,
        'max_position': 40,
        'stop_loss': -6,
        'take_profit': 18,
        'holding_period': '1-4周',
    },
    'Ind': {
        'min_score': 70,
        'min_fund_days': 3,
        'max_position': 60,
        'stop_loss': -10,
        'take_profit': 25,
        'holding_period': '1-6月',
    }
}
```

## 4. 输出格式

### 4.1 选股结果格式

```python
STOCK_RESULT_TEMPLATE = """
【{mode}模式选股结果】

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🥇 第一名：{name} ({code})
  综合评分：{score}/100
  模式评分：{mode_score}/100
  赔率：{odds}:1

  {details}

  交易策略：
  ├── 入场：{entry_type}（{entry_price}）
  ├── 仓位：{position}%
  ├── 止损：{stop_loss}%
  └── 目标：{take_profit}%

  风险等级：{risk_level}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
```

### 4.2 每日报告格式

```python
DAILY_REPORT_TEMPLATE = """
【{date} A股市场分析报告】

市场状态：
├── 指数：{index}（{change}%）
├── 涨跌停：{limit_up}/{limit_down}
├── 成交额：{volume}亿
└── 情绪：{sentiment}

资金状态：
├── 北向：{hsgt}亿
├── 主力：{main_fund}亿
└── 热点：{hot_sector}

模式推荐：
├── 首选：{primary_mode}（置信度{conf1}%）
└── 备选：{backup_mode}（置信度{conf2}%）

推荐仓位：{total_position}%
"""}
```

## 5. 日志配置

```python
import logging

def setup_logging(log_file='a_stock.log'):
    """配置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)
```

## 6. 异常处理

```python
def safe_get_data(func, fallback=None, error_msg="获取数据失败"):
    """安全获取数据"""
    try:
        result = func()
        return result
    except Exception as e:
        logging.error(f"{error_msg}: {e}")
        return fallback

class DataFetchError(Exception):
    """数据获取异常"""
    pass

def validate_data(df, required_cols):
    """验证数据完整性"""
    if df is None or len(df) == 0:
        raise DataFetchError("数据为空")
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise DataFetchError(f"缺少字段: {missing}")
    return True
```