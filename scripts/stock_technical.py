#!/usr/bin/env python3
"""
A股技术指标分析
计算 MACD、KDJ、均线等常用技术指标
"""

import akshare as ak
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


def get_kline_data(symbol, start_date=None, end_date=None, period="daily", adjust="qfq"):
    """
    获取K线数据

    参数:
        symbol: 股票代码，如 "000001"
        start_date: 开始日期，如 "20240101"
        end_date: 结束日期，如 "20250101"
        period: 日/周/月频率
        adjust: 复权方式 qfq=前复权, hfq=后复权
    """
    if start_date is None:
        start_date = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")
    if end_date is None:
        end_date = datetime.now().strftime("%Y%m%d")

    df = ak.stock_zh_a_hist(
        symbol=symbol,
        period=period,
        start_date=start_date,
        end_date=end_date,
        adjust=adjust
    )
    return df


def calculate_ma(df, windows=[5, 10, 20, 60]):
    """计算移动平均线"""
    result = df.copy()
    for w in windows:
        result[f'MA{w}'] = result['收盘'].rolling(window=w).mean()
    return result


def calculate_ema(df, windows=[12, 26]):
    """计算指数移动平均线"""
    result = df.copy()
    for w in windows:
        result[f'EMA{w}'] = result['收盘'].ewm(span=w, adjust=False).mean()
    return result


def calculate_macd(df, fast=12, slow=26, signal=9):
    """
    计算MACD指标

    返回:
        DIF: 快线
        DEA: 信号线
        MACD: 柱状图 (DIF - DEA) * 2
    """
    result = df.copy()

    # 计算EMA
    ema_fast = result['收盘'].ewm(span=fast, adjust=False).mean()
    ema_slow = result['收盘'].ewm(span=slow, adjust=False).mean()

    # DIF = EMA12 - EMA26
    result['DIF'] = ema_fast - ema_slow

    # DEA = DIF的9日EMA
    result['DEA'] = result['DIF'].ewm(span=signal, adjust=False).mean()

    # MACD柱 = (DIF - DEA) * 2
    result['MACD'] = (result['DIF'] - result['DEA']) * 2

    return result


def calculate_kdj(df, n=9, m1=3, m2=3):
    """
    计算KDJ指标

    参数:
        n: RSV计算周期
        m1: K信号平滑
        m2: D信号平滑
    """
    result = df.copy()

    # 计算RSV
    low_min = result['最低'].rolling(window=n, min_periods=1).min()
    high_max = result['最高'].rolling(window=n, min_periods=1).max()

    rsv = (result['收盘'] - low_min) / (high_max - low_min) * 100
    rsv = rsv.fillna(50)

    # 计算K、D、J
    result['K'] = rsv.ewm(com=m1-1, adjust=False).mean()
    result['D'] = result['K'].ewm(com=m2-1, adjust=False).mean()
    result['J'] = 3 * result['K'] - 2 * result['D']

    return result


def calculate_rsi(df, periods=[6, 12, 24]):
    """计算RSI指标"""
    result = df.copy()

    for p in periods:
        delta = result['收盘'].diff()
        gain = delta.where(delta > 0, 0).rolling(window=p).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=p).mean()

        rs = gain / loss
        result[f'RSI{p}'] = 100 - (100 / (1 + rs))

    return result


def detect_cross_ma(df, short_ma=5, long_ma=20):
    """
    检测均线金叉死叉

    返回:
        gold_cross: 金叉信号列表
        death_cross: 死叉信号列表
    """
    df = calculate_ma(df, windows=[short_ma, long_ma])

    gold_cross = []
    death_cross = []

    col_short = f'MA{short_ma}'
    col_long = f'MA{long_ma}'

    for i in range(1, len(df)):
        # 金叉：短期均线从下方穿越长期均线
        if df[col_short].iloc[i-1] < df[col_long].iloc[i-1] and \
           df[col_short].iloc[i] > df[col_long].iloc[i]:
            gold_cross.append({
                'date': df['日期'].iloc[i],
                'price': df['收盘'].iloc[i]
            })

        # 死叉：短期均线从上方穿越长期均线
        if df[col_short].iloc[i-1] > df[col_long].iloc[i-1] and \
           df[col_short].iloc[i] < df[col_long].iloc[i]:
            death_cross.append({
                'date': df['日期'].iloc[i],
                'price': df['收盘'].iloc[i]
            })

    return gold_cross, death_cross


def detect_macd_signal(df):
    """
    检测MACD信号

    返回:
        bull_market: MACD金叉（买入信号）
        bear_market: MACD死叉（卖出信号）
        divergence: 顶底背离
    """
    df = calculate_macd(df)

    signals = []

    for i in range(1, len(df)):
        # 金叉：DIF上穿DEA
        if df['DIF'].iloc[i-1] < df['DEA'].iloc[i-1] and \
           df['DIF'].iloc[i] > df['DEA'].iloc[i]:
            signals.append({
                'date': df['日期'].iloc[i],
                'type': '金叉',
                'dif': df['DIF'].iloc[i],
                'dea': df['DEA'].iloc[i],
                'macd': df['MACD'].iloc[i]
            })

        # 死叉：DIF下穿DEA
        if df['DIF'].iloc[i-1] > df['DEA'].iloc[i-1] and \
           df['DIF'].iloc[i] < df['DEA'].iloc[i]:
            signals.append({
                'date': df['日期'].iloc[i],
                'type': '死叉',
                'dif': df['DIF'].iloc[i],
                'dea': df['DEA'].iloc[i],
                'macd': df['MACD'].iloc[i]
            })

    return signals


def analyze_technical(symbol, start_date=None, end_date=None):
    """
    综合技术分析

    返回技术指标计算结果和信号
    """
    # 获取数据
    df = get_kline_data(symbol, start_date, end_date)

    # 计算各项指标
    df = calculate_ma(df)
    df = calculate_macd(df)
    df = calculate_kdj(df)
    df = calculate_rsi(df)

    # 检测信号
    ma_gold, ma_death = detect_cross_ma(df)
    macd_signals = detect_macd_signal(df)

    # 获取最新值
    latest = df.iloc[-1]

    # 解读
    signals = []

    # 均线解读
    if latest[f'MA5'] > latest[f'MA20']:
        signals.append(("均线多头", "看涨"))
    elif latest[f'MA5'] < latest[f'MA20']:
        signals.append(("均线空头", "看跌"))

    # MACD解读
    if latest['DIF'] > latest['DEA']:
        signals.append(("MACD多头", "看涨"))
    else:
        signals.append(("MACD空头", "看跌"))

    # KDJ解读
    if latest['K'] < 20:
        signals.append(("KDJ超卖", "可能反弹"))
    elif latest['K'] > 80:
        signals.append(("KDJ超买", "可能回调"))

    # RSI解读
    if latest['RSI6'] < 30:
        signals.append(("RSI超卖", "可能反弹"))
    elif latest['RSI6'] > 70:
        signals.append(("RSI超买", "可能回调"))

    return {
        'data': df,
        'latest': latest,
        'ma_signals': {'gold': ma_gold, 'death': ma_death},
        'macd_signals': macd_signals,
        'interpretation': signals
    }


def display_technical_report(symbol, start_date=None, end_date=None):
    """展示技术分析报告"""
    result = analyze_technical(symbol, start_date, end_date)
    latest = result['latest']

    print(f"=== {symbol} 技术分析报告 ===")
    print(f"日期: {latest['日期']}")
    print(f"最新价: {latest['收盘']:.2f}")
    print(f"涨跌幅: {latest['涨跌幅']:.2f}%")

    print("\n--- 均线系统 ---")
    for ma in [5, 10, 20, 60]:
        col = f'MA{ma}'
        trend = "↑" if latest[col] > latest['收盘'] else "↓"
        print(f"  MA{ma}: {latest[col]:.2f} {trend}")

    print("\n--- MACD ---")
    print(f"  DIF: {latest['DIF']:.3f}")
    print(f"  DEA: {latest['DEA']:.3f}")
    print(f"  MACD: {latest['MACD']:.3f}")

    print("\n--- KDJ ---")
    print(f"  K: {latest['K']:.2f}")
    print(f"  D: {latest['D']:.2f}")
    print(f"  J: {latest['J']:.2f}")

    print("\n--- RSI ---")
    print(f"  RSI6: {latest['RSI6']:.2f}")
    print(f"  RSI12: {latest['RSI12']:.2f}")
    print(f"  RSI24: {latest['RSI24']:.2f}")

    print("\n--- 信号解读 ---")
    for indicator, signal in result['interpretation']:
        print(f"  {indicator}: {signal}")


if __name__ == "__main__":
    # 示例：分析平安银行
    display_technical_report("000001", "20240101", "20250419")