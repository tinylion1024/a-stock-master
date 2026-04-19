#!/usr/bin/env python3
"""
A股综合分析报告
生成个股的综合分析报告
"""

import argparse
import akshare as ak
import pandas as pd
import json
from datetime import datetime, timedelta


def get_stock_info(symbol):
    """获取个股基本信息"""
    try:
        return ak.stock_individual_info_em(symbol=symbol)
    except Exception:
        return None


def get_realtime_quote(symbol):
    """获取个股实时行情"""
    try:
        df = ak.stock_zh_a_spot_em()
        quote = df[df['代码'] == symbol]
        return quote.iloc[0] if len(quote) > 0 else None
    except Exception:
        return None


def get_kline_data(symbol, days=365):
    """获取K线数据"""
    try:
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y%m%d')
        return ak.stock_zh_a_hist(
            symbol=symbol, period="daily",
            start_date=start_date, end_date=end_date, adjust="qfq"
        )
    except Exception:
        return None


def get_fund_flow(symbol):
    """获取资金流向"""
    try:
        df = ak.stock_fund_flow_individual(symbol="即时")
        flow = df[df['股票代码'] == symbol]
        return flow.iloc[0] if len(flow) > 0 else None
    except Exception:
        return None


def calculate_technical(df):
    """计算技术指标"""
    if df is None or len(df) < 30:
        return None

    result = df.copy()

    for ma in [5, 10, 20, 60, 120, 250]:
        result[f'MA{ma}'] = result['收盘'].rolling(window=ma).mean()

    ema12 = result['收盘'].ewm(span=12, adjust=False).mean()
    ema26 = result['收盘'].ewm(span=26, adjust=False).mean()
    result['DIF'] = ema12 - ema26
    result['DEA'] = result['DIF'].ewm(span=9, adjust=False).mean()
    result['MACD'] = (result['DIF'] - result['DEA']) * 2

    low_min = result['最低'].rolling(window=9, min_periods=1).min()
    high_max = result['最高'].rolling(window=9, min_periods=1).max()
    rsv = (result['收盘'] - low_min) / (high_max - low_min) * 100
    result['K'] = rsv.ewm(com=2, adjust=False).mean()
    result['D'] = result['K'].ewm(com=2, adjust=False).mean()
    result['J'] = 3 * result['K'] - 2 * result['D']

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

    change_5d = (latest['收盘'] / df['收盘'].iloc[-6] - 1) * 100 if len(df) > 5 else 0
    change_20d = (latest['收盘'] / ma20 - 1) * 100 if ma20 else 0

    ma_position = "MA5上方" if latest['收盘'] > ma5 else "MA5下方" if ma5 else "N/A"

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


def generate_report(symbol, days=365, output_format=None):
    """生成综合分析报告"""
    output = []

    if output_format != 'json':
        output.append(f"\n{'='*70}")
        output.append(f"  A股综合分析报告 - {symbol}")
        output.append(f"{'='*70}")
        output.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # 1. 基本信息
    if output_format != 'json':
        output.append("【基本信息】")
    info = get_stock_info(symbol)
    info_dict = {}
    if info is not None:
        for _, row in info.iterrows():
            item = row.get('item', '')
            value = row.get('value', 'N/A')
            info_dict[item] = value
            if output_format != 'json':
                output.append(f"  {item}: {value}")

    # 2. 实时行情
    if output_format != 'json':
        output.append("\n【实时行情】")
    quote = get_realtime_quote(symbol)
    quote_dict = {}
    if quote is not None:
        fields = [('最新价', '最新价'), ('涨跌幅', '涨跌幅'), ('成交量', '成交量'),
                   ('成交额', '成交额'), ('市盈率-动态', '市盈率'), ('市净率', '市净率'),
                   ('总市值', '总市值'), ('流通市值', '流通市值')]
        for src, dst in fields:
            val = quote.get(src)
            if val:
                if src in ['成交额', '总市值', '流通市值']:
                    quote_dict[dst] = f"{val/1e8:.2f}亿"
                    if output_format != 'json':
                        output.append(f"  {dst}: {val/1e8:.2f}亿")
                else:
                    quote_dict[dst] = val
                    if output_format != 'json':
                        output.append(f"  {dst}: {val}")

    # 3. 资金流向
    if output_format != 'json':
        output.append("\n【资金流向】")
    flow = get_fund_flow(symbol)
    flow_dict = {}
    if flow is not None:
        flow_fields = [('资金流入净额', '主力净流入'), ('超大单净流入', '超大单净流入'),
                       ('大单净流入', '大单净流入')]
        for src, dst in flow_fields:
            val = flow.get(src)
            if val:
                flow_dict[dst] = f"{val/1e8:.2f}亿"
                if output_format != 'json':
                    output.append(f"  {dst}: {val/1e8:.2f}亿")

    # 4. 技术分析
    if output_format != 'json':
        output.append("\n【技术分析】")
    df = get_kline_data(symbol, days)
    tech_dict = {}
    if df is not None and len(df) > 0:
        df = calculate_technical(df)
        stats = calculate_basic_stats(df)
        latest = df.iloc[-1]

        if output_format != 'json':
            output.append("  均线系统:")
        ma_dict = {}
        for ma in [5, 10, 20, 60]:
            col = f'MA{ma}'
            if col in df.columns:
                ma_val = latest[col]
                price = latest['收盘']
                pos = "↑" if price > ma_val else "↓"
                ma_dict[f'MA{ma}'] = {'value': float(ma_val), 'position': pos}
                if output_format != 'json':
                    output.append(f"    MA{ma}: {ma_val:.2f} ({pos})")

        macd_dict = {
            'dif': float(latest['DIF']),
            'dea': float(latest['DEA']),
            'macd': float(latest['MACD'])
        }
        if output_format != 'json':
            output.append(f"\n  MACD:")
            output.append(f"    DIF: {latest['DIF']:.3f}")
            output.append(f"    DEA: {latest['DEA']:.3f}")
            macd_bar = "红柱" if latest['MACD'] > 0 else "绿柱"
            output.append(f"    柱: {macd_bar} ({latest['MACD']:.3f})")

        kdj_dict = {
            'k': float(latest['K']),
            'd': float(latest['D']),
            'j': float(latest['J'])
        }
        if output_format != 'json':
            output.append(f"\n  KDJ:")
            output.append(f"    K: {latest['K']:.2f}")
            output.append(f"    D: {latest['D']:.2f}")
            output.append(f"    J: {latest['J']:.2f}")

        rsi_dict = {
            'rsi6': float(latest['RSI6']),
            'rsi12': float(latest['RSI12']),
            'rsi24': float(latest['RSI24'])
        }
        if output_format != 'json':
            output.append(f"\n  RSI:")
            output.append(f"    RSI6: {latest['RSI6']:.2f}")
            output.append(f"    RSI12: {latest['RSI12']:.2f}")
            output.append(f"    RSI24: {latest['RSI24']:.2f}")

        if stats and output_format != 'json':
            output.append(f"\n  近期统计:")
            output.append(f"    5日涨跌: {stats['change_5d']:.2f}%")
            output.append(f"    20日涨跌: {stats['change_20d']:.2f}%")
            output.append(f"    均线位置: {stats['ma_position']}")
            output.append(f"    量比: {stats['volume_ratio']:.2f}")
            output.append(f"    52周最高: {stats['high_52w']:.2f}")
            output.append(f"    52周最低: {stats['low_52w']:.2f}")

        # 信号总结
        signals = []
        if output_format != 'json':
            output.append(f"\n  【信号总结】")

        if 'MA5' in df.columns and 'MA20' in df.columns:
            if latest['MA5'] > latest['MA20']:
                signals.append("✓ 均线多头排列")
            else:
                signals.append("✗ 均线空头排列")

        if latest['DIF'] > latest['DEA']:
            signals.append("✓ MACD金叉")
        else:
            signals.append("✗ MACD死叉")

        if latest['K'] < 20:
            signals.append("⚠ KDJ超卖")
        elif latest['K'] > 80:
            signals.append("⚠ KDJ超买")

        if latest['RSI6'] < 30:
            signals.append("⚠ RSI超卖")
        elif latest['RSI6'] > 70:
            signals.append("⚠ RSI超买")

        if output_format != 'json':
            for s in signals:
                output.append(f"    {s}")

    if output_format == 'json':
        data = {
            'symbol': symbol,
            'report_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'info': info_dict,
            'quote': quote_dict,
            'fund_flow': flow_dict,
            'technical': {
                'ma': ma_dict,
                'macd': macd_dict,
                'kdj': kdj_dict,
                'rsi': rsi_dict,
            },
            'signals': signals
        }
        return json.dumps(data, ensure_ascii=False, indent=2)
    else:
        output.append(f"\n{'='*70}")
        output.append("  风险提示：本报告仅供参考，不构成投资建议")
        output.append(f"{'='*70}\n")
        return '\n'.join(output)


def main():
    parser = argparse.ArgumentParser(
        description='A股综合分析报告',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python stock_analysis_report.py 000001                    # 分析平安银行
  python stock_analysis_report.py 000001 --json            # JSON格式输出
  python stock_analysis_report.py 000001 --days 180        # 近半年数据
  python stock_analysis_report.py 000001 > report.txt      # 保存到文件
        """
    )
    parser.add_argument('symbol', nargs='?', default='000001', help='股票代码 (默认: 000001)')
    parser.add_argument('--days', type=int, default=365, help='K线数据天数 (默认: 365)')
    parser.add_argument('--json', action='store_true', help='JSON格式输出')
    args = parser.parse_args()

    print(f"=== A股综合分析报告 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===")

    result = generate_report(args.symbol, args.days, 'json' if args.json else None)
    print(result)


if __name__ == "__main__":
    main()
