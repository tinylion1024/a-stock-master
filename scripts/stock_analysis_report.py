#!/usr/bin/env python3
"""
A股综合分析报告
生成个股的综合分析报告
"""

import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
import sys


def get_stock_info(symbol):
    """获取个股基本信息"""
    try:
        df = ak.stock_individual_info_em(symbol=symbol)
        return df
    except Exception as e:
        print(f"获取基本信息失败: {e}")
        return None


def get_realtime_quote(symbol):
    """获取个股实时行情"""
    try:
        df = ak.stock_zh_a_spot_em()
        quote = df[df['代码'] == symbol]
        return quote.iloc[0] if len(quote) > 0 else None
    except Exception as e:
        print(f"获取实时行情失败: {e}")
        return None


def get_kline_data(symbol, days=365):
    """获取K线数据"""
    try:
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y%m%d')

        df = ak.stock_zh_a_hist(
            symbol=symbol,
            period="daily",
            start_date=start_date,
            end_date=end_date,
            adjust="qfq"
        )
        return df
    except Exception as e:
        print(f"获取K线数据失败: {e}")
        return None


def get_fund_flow(symbol):
    """获取资金流向"""
    try:
        df = ak.stock_fund_flow_individual(symbol="即时")
        flow = df[df['股票代码'] == symbol]
        return flow.iloc[0] if len(flow) > 0 else None
    except Exception as e:
        return None


def calculate_technical(df):
    """计算技术指标"""
    if df is None or len(df) < 30:
        return None

    result = df.copy()

    # 均线
    for ma in [5, 10, 20, 60, 120, 250]:
        result[f'MA{ma}'] = result['收盘'].rolling(window=ma).mean()

    # MACD
    ema12 = result['收盘'].ewm(span=12, adjust=False).mean()
    ema26 = result['收盘'].ewm(span=26, adjust=False).mean()
    result['DIF'] = ema12 - ema26
    result['DEA'] = result['DIF'].ewm(span=9, adjust=False).mean()
    result['MACD'] = (result['DIF'] - result['DEA']) * 2

    # KDJ
    low_min = result['最低'].rolling(window=9, min_periods=1).min()
    high_max = result['最高'].rolling(window=9, min_periods=1).max()
    rsv = (result['收盘'] - low_min) / (high_max - low_min) * 100
    result['K'] = rsv.ewm(com=2, adjust=False).mean()
    result['D'] = result['K'].ewm(com=2, adjust=False).mean()
    result['J'] = 3 * result['K'] - 2 * result['D']

    # RSI
    for period in [6, 12, 24]:
        delta = result['收盘'].diff()
        gain = delta.where(delta > 0, 0).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        result[f'RSI{period}'] = 100 - (100 / (1 + rs))

    return result


def calculate_basic_stats(df):
    """计算基本统计"""
    if df is None or len(df) < 30:
        return None

    latest = df.iloc[-1]
    ma5 = df['MA5'].iloc[-1] if 'MA5' in df.columns else None
    ma20 = df['MA20'].iloc[-1] if 'MA20' in df.columns else None

    # 计算近期涨跌幅
    change_5d = (latest['收盘'] / df['收盘'].iloc[-6] - 1) * 100 if len(df) > 5 else 0
    change_20d = (latest['收盘'] / df['MA20'].iloc[-20] - 1) * 100 if len(df) > 20 else 0

    # 均线位置
    ma_position = "MA5上方" if latest['收盘'] > ma5 else "MA5下方" if ma5 else "N/A"

    # 成交量变化
    avg_volume_5d = df['成交量'].iloc[-5:].mean()
    today_volume = latest['成交量']
    volume_ratio = today_volume / avg_volume_5d if avg_volume_5d > 0 else 0

    return {
        'latest_price': latest['收盘'],
        'change_5d': change_5d,
        'change_20d': change_20d,
        'ma_position': ma_position,
        'volume_ratio': volume_ratio,
        'high_52w': df['最高'].max(),
        'low_52w': df['最低'].min(),
    }


def generate_report(symbol):
    """生成综合分析报告"""
    print(f"\n{'='*70}")
    print(f"  A股综合分析报告 - {symbol}")
    print(f"{'='*70}")
    print(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # 1. 基本信息
    print("【基本信息】")
    info = get_stock_info(symbol)
    if info is not None:
        for _, row in info.iterrows():
            print(f"  {row.get('item', 'N/A')}: {row.get('value', 'N/A')}")
    else:
        print("  暂无数据")

    print()

    # 2. 实时行情
    print("【实时行情】")
    quote = get_realtime_quote(symbol)
    if quote is not None:
        print(f"  最新价: {quote.get('最新价', 'N/A')}")
        print(f"  涨跌幅: {quote.get('涨跌幅', 'N/A')}%")
        print(f"  成交量: {quote.get('成交量', 'N/A')}")
        print(f"  成交额: {quote.get('成交额', 'N/A')/1e8:.2f}亿" if quote.get('成交额') else "  成交额: N/A")
        print(f"  市盈率: {quote.get('市盈率-动态', 'N/A')}")
        print(f"  市净率: {quote.get('市净率', 'N/A')}")
        print(f"  总市值: {quote.get('总市值', 'N/A')/1e8:.2f}亿" if quote.get('总市值') else "  总市值: N/A")
        print(f"  流通市值: {quote.get('流通市值', 'N/A')/1e8:.2f}亿" if quote.get('流通市值') else "  流通市值: N/A")
    else:
        print("  暂无数据")

    print()

    # 3. 资金流向
    print("【资金流向】")
    flow = get_fund_flow(symbol)
    if flow is not None:
        print(f"  今日主力净流入: {flow.get('资金流入净额', 'N/A')/1e8:.2f}亿" if flow.get('资金流入净额') else "  主力净流入: N/A")
        print(f"  今日超大单净流入: {flow.get('超大单净流入', 'N/A')/1e8:.2f}亿" if flow.get('超大单净流入') else "  超大单净流入: N/A")
        print(f"  今日大单净流入: {flow.get('大单净流入', 'N/A')/1e8:.2f}亿" if flow.get('大单净流入') else "  大单净流入: N/A")
    else:
        print("  暂无数据")

    print()

    # 4. 技术分析
    print("【技术分析】")
    df = get_kline_data(symbol)
    if df is not None and len(df) > 0:
        df = calculate_technical(df)
        stats = calculate_basic_stats(df)

        latest = df.iloc[-1]

        print(f"  均线系统:")
        for ma in [5, 10, 20, 60]:
            col = f'MA{ma}'
            if col in df.columns:
                ma_val = latest[col]
                price = latest['收盘']
                pos = "↑" if price > ma_val else "↓"
                print(f"    MA{ma}: {ma_val:.2f} ({pos})")

        print(f"\n  MACD:")
        print(f"    DIF: {latest['DIF']:.3f}")
        print(f"    DEA: {latest['DEA']:.3f}")
        macd_bar = "红柱" if latest['MACD'] > 0 else "绿柱"
        print(f"    柱: {macd_bar} ({latest['MACD']:.3f})")

        print(f"\n  KDJ:")
        print(f"    K: {latest['K']:.2f}")
        print(f"    D: {latest['D']:.2f}")
        print(f"    J: {latest['J']:.2f}")

        print(f"\n  RSI:")
        print(f"    RSI6: {latest['RSI6']:.2f}")
        print(f"    RSI12: {latest['RSI12']:.2f}")
        print(f"    RSI24: {latest['RSI24']:.2f}")

        if stats:
            print(f"\n  近期统计:")
            print(f"    5日涨跌: {stats['change_5d']:.2f}%")
            print(f"    20日涨跌: {stats['change_20d']:.2f}%")
            print(f"    均线位置: {stats['ma_position']}")
            print(f"    量比: {stats['volume_ratio']:.2f}")
            print(f"    52周最高: {stats['high_52w']:.2f}")
            print(f"    52周最低: {stats['low_52w']:.2f}")

        # 信号总结
        print(f"\n  【信号总结】")
        signals = []

        # 均线信号
        if 'MA5' in df.columns and 'MA20' in df.columns:
            if latest['MA5'] > latest['MA20']:
                signals.append("✓ 均线多头排列")
            else:
                signals.append("✗ 均线空头排列")

        # MACD信号
        if latest['DIF'] > latest['DEA']:
            signals.append("✓ MACD金叉")
        else:
            signals.append("✗ MACD死叉")

        # KDJ信号
        if latest['K'] < 20:
            signals.append("⚠ KDJ超卖")
        elif latest['K'] > 80:
            signals.append("⚠ KDJ超买")

        # RSI信号
        if latest['RSI6'] < 30:
            signals.append("⚠ RSI超卖")
        elif latest['RSI6'] > 70:
            signals.append("⚠ RSI超买")

        for s in signals:
            print(f"    {s}")
    else:
        print("  暂无数据")

    print(f"\n{'='*70}")
    print("  风险提示：本报告仅供参考，不构成投资建议")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        symbol = sys.argv[1]
    else:
        symbol = "000001"  # 默认分析平安银行

    generate_report(symbol)