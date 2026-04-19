#!/usr/bin/env python3
"""
A股技术指标分析
计算 MACD、KDJ、均线等常用技术指标
"""

import argparse
import akshare as ak
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


def get_kline_data(symbol, start_date=None, end_date=None, period="daily", adjust="qfq"):
    """获取K线数据"""
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


def calculate_macd(df, fast=12, slow=26, signal=9):
    """计算MACD指标"""
    result = df.copy()
    ema_fast = result['收盘'].ewm(span=fast, adjust=False).mean()
    ema_slow = result['收盘'].ewm(span=slow, adjust=False).mean()
    result['DIF'] = ema_fast - ema_slow
    result['DEA'] = result['DIF'].ewm(span=signal, adjust=False).mean()
    result['MACD'] = (result['DIF'] - result['DEA']) * 2
    return result


def calculate_kdj(df, n=9, m1=3, m2=3):
    """计算KDJ指标"""
    result = df.copy()
    low_min = result['最低'].rolling(window=n, min_periods=1).min()
    high_max = result['最高'].rolling(window=n, min_periods=1).max()
    rsv = (result['收盘'] - low_min) / (high_max - low_min) * 100
    rsv = rsv.fillna(50)
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


def analyze_technical(symbol, start_date=None, end_date=None):
    """综合技术分析"""
    df = get_kline_data(symbol, start_date, end_date)
    df = calculate_ma(df)
    df = calculate_macd(df)
    df = calculate_kdj(df)
    df = calculate_rsi(df)
    latest = df.iloc[-1]

    signals = []
    if latest[f'MA5'] > latest[f'MA20']:
        signals.append(("均线多头", "看涨"))
    elif latest[f'MA5'] < latest[f'MA20']:
        signals.append(("均线空头", "看跌"))

    if latest['DIF'] > latest['DEA']:
        signals.append(("MACD多头", "看涨"))
    else:
        signals.append(("MACD空头", "看跌"))

    if latest['K'] < 20:
        signals.append(("KDJ超卖", "可能反弹"))
    elif latest['K'] > 80:
        signals.append(("KDJ超买", "可能回调"))

    if latest['RSI6'] < 30:
        signals.append(("RSI超卖", "可能反弹"))
    elif latest['RSI6'] > 70:
        signals.append(("RSI超买", "可能回调"))

    return {
        'data': df,
        'latest': latest,
        'interpretation': signals
    }


def display_technical_report(symbol, start_date=None, end_date=None, output_format=None):
    """展示技术分析报告"""
    result = analyze_technical(symbol, start_date, end_date)
    latest = result['latest']

    output = []
    output.append(f"=== {symbol} 技术分析报告 ===")
    output.append(f"日期: {latest['日期']}")
    output.append(f"最新价: {latest['收盘']:.2f}")
    output.append(f"涨跌幅: {latest['涨跌幅']:.2f}%")

    output.append("\n--- 均线系统 ---")
    for ma in [5, 10, 20, 60]:
        col = f'MA{ma}'
        trend = "↑" if latest[col] > latest['收盘'] else "↓"
        output.append(f"  MA{ma}: {latest[col]:.2f} {trend}")

    output.append("\n--- MACD ---")
    output.append(f"  DIF: {latest['DIF']:.3f}")
    output.append(f"  DEA: {latest['DEA']:.3f}")
    output.append(f"  MACD: {latest['MACD']:.3f}")

    output.append("\n--- KDJ ---")
    output.append(f"  K: {latest['K']:.2f}")
    output.append(f"  D: {latest['D']:.2f}")
    output.append(f"  J: {latest['J']:.2f}")

    output.append("\n--- RSI ---")
    output.append(f"  RSI6: {latest['RSI6']:.2f}")
    output.append(f"  RSI12: {latest['RSI12']:.2f}")
    output.append(f"  RSI24: {latest['RSI24']:.2f}")

    output.append("\n--- 信号解读 ---")
    for indicator, signal in result['interpretation']:
        output.append(f"  {indicator}: {signal}")

    if output_format == 'json':
        # 输出为JSON格式
        import json
        data = {
            'symbol': symbol,
            'date': str(latest['日期']),
            'close': float(latest['收盘']),
            'change_pct': float(latest['涨跌幅']),
            'ma': {f'MA{ma}': float(latest[f'MA{ma}']) for ma in [5, 10, 20, 60]},
            'macd': {
                'dif': float(latest['DIF']),
                'dea': float(latest['DEA']),
                'macd': float(latest['MACD'])
            },
            'kdj': {
                'k': float(latest['K']),
                'd': float(latest['D']),
                'j': float(latest['J'])
            },
            'rsi': {
                'rsi6': float(latest['RSI6']),
                'rsi12': float(latest['RSI12']),
                'rsi24': float(latest['RSI24'])
            },
            'signals': result['interpretation']
        }
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print('\n'.join(output))


def main():
    parser = argparse.ArgumentParser(
        description='A股技术指标分析',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python stock_technical.py 000001                    # 分析平安银行
  python stock_technical.py 000001 --start 20240101      # 指定开始日期
  python stock_technical.py 000001 --end 20241231        # 指定结束日期
  python stock_technical.py 000001 --json               # JSON格式输出
  python stock_technical.py 000001 --period weekly      # 周线数据
        """
    )
    parser.add_argument('symbol', nargs='?', default='000001', help='股票代码 (默认: 000001)')
    parser.add_argument('--start', help='开始日期 YYYYMMDD')
    parser.add_argument('--end', help='结束日期 YYYYMMDD')
    parser.add_argument('--period', choices=['daily', 'weekly', 'monthly'], default='daily', help='K线周期')
    parser.add_argument('--adjust', choices=['qfq', 'hfq', ''], default='qfq', help='复权方式')
    parser.add_argument('--json', action='store_true', help='JSON格式输出')
    args = parser.parse_args()

    print(f"=== A股技术指标分析 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")

    display_technical_report(args.symbol, args.start, args.end, 'json' if args.json else None)


if __name__ == "__main__":
    main()
