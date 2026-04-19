#!/usr/bin/env python3
"""
A股大盘指数行情
获取上证、深证、创业板等主要指数实时行情
"""

import argparse
import akshare as ak
import pandas as pd
from datetime import datetime


def get_index_data():
    """获取主要指数实时数据"""
    # 获取全市场股票
    df = ak.stock_zh_a_spot_em()

    # 计算大盘指标
    total_stocks = len(df)
    up_stocks = len(df[df['涨跌幅'] > 0])
    down_stocks = len(df[df['涨跌幅'] < 0])
    flat_stocks = len(df[df['涨跌幅'] == 0])
    limit_up = len(df[df['涨跌幅'] >= 9.5])
    limit_down = len(df[df['涨跌幅'] <= -9.5])
    avg_change = df['涨跌幅'].mean()
    total_volume = df['成交额'].sum()

    return {
        'total_stocks': total_stocks,
        'up_stocks': up_stocks,
        'down_stocks': down_stocks,
        'flat_stocks': flat_stocks,
        'limit_up': limit_up,
        'limit_down': limit_down,
        'avg_change': avg_change,
        'total_volume': total_volume
    }


def get_index_quote(symbol, name):
    """获取单个指数数据"""
    try:
        df = ak.stock_zh_index_spot_em(symbol=symbol)
        if df is not None and len(df) > 0:
            return {
                'name': name,
                'code': symbol,
                '最新价': df.iloc[0].get('最新价', 'N/A'),
                '涨跌幅': df.iloc[0].get('涨跌幅', 'N/A'),
                '涨跌额': df.iloc[0].get('涨跌额', 'N/A'),
                '成交量': df.iloc[0].get('成交量', 'N/A'),
                '成交额': df.iloc[0].get('成交额', 'N/A'),
                '最高': df.iloc[0].get('最高', 'N/A'),
                '最低': df.iloc[0].get('最低', 'N/A'),
                '今开': df.iloc[0].get('今开', 'N/A'),
                '昨收': df.iloc[0].get('昨收', 'N/A'),
            }
    except Exception as e:
        return {'name': name, 'code': symbol, 'error': str(e)}
    return None


def get_major_indices():
    """获取主要指数"""
    indices = [
        ('000001', '上证指数'),
        ('399001', '深证成指'),
        ('399006', '创业板指'),
        ('000300', '沪深300'),
        ('000016', '上证50'),
        ('000905', '中证500'),
        ('000688', '科创50'),
    ]
    return indices


def display_market_summary(data, indices, output_format=None):
    """展示大盘汇总"""
    if output_format == 'json':
        import json
        output = {
            'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'market_summary': data,
            'indices': indices
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return

    print(f"\n{'='*60}")
    print(f"  A股大盘行情 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")

    print(f"\n【市场概况】")
    print(f"  股票总数: {data['total_stocks']}")
    print(f"  上涨家数: {data['up_stocks']} ({data['up_stocks']/data['total_stocks']*100:.1f}%)")
    print(f"  下跌家数: {data['down_stocks']} ({data['down_stocks']/data['total_stocks']*100:.1f}%)")
    print(f"  平盘家数: {data['flat_stocks']}")
    print(f"  涨停家数: {data['limit_up']}")
    print(f"  跌停家数: {data['limit_down']}")
    print(f"  平均涨跌: {data['avg_change']:.2f}%")
    print(f"  总成交额: {data['total_volume']/1e8:.2f}亿")

    print(f"\n【主要指数】")
    print(f"{'='*60}")
    print(f"{'指数名称':<12} {'最新价':>12} {'涨跌幅':>10} {'涨跌额':>12}")
    print(f"{'-'*60}")

    for idx in indices:
        if idx.get('error'):
            print(f"{idx['name']:<12} {'数据获取失败':>12}")
        else:
            change = idx.get('涨跌幅', 0)
            if isinstance(change, (int, float)):
                change_str = f"{change:+.2f}%"
                arrow = "↑" if change > 0 else "↓" if change < 0 else "-"
            else:
                change_str = str(change)
                arrow = ""

            price = idx.get('最新价', 'N/A')
            if isinstance(price, (int, float)):
                price_str = f"{price:.2f}"
            else:
                price_str = str(price)

            change_amt = idx.get('涨跌额', 'N/A')
            if isinstance(change_amt, (int, float)):
                change_str2 = f"{change_amt:+.2f}"
            else:
                change_str2 = str(change_amt)

            print(f"{idx['name']:<12} {price_str:>12} {change_str:>10} {change_str2:>12}")

    print(f"{'='*60}")

    # 简单判断
    avg_change = data['avg_change']
    up_ratio = data['up_stocks'] / data['total_stocks'] * 100

    print(f"\n【市场情绪】")
    if avg_change > 1 and up_ratio > 60:
        print(f"  🟢 市场强势上涨，积极做多")
    elif avg_change > 0.5 and up_ratio > 50:
        print(f"  🟡 市场温和上涨，谨慎做多")
    elif avg_change < -1 and up_ratio < 40:
        print(f"  🔴 市场弱势下跌，控制风险")
    elif avg_change < -0.5 and up_ratio < 50:
        print(f"  🟠 市场小幅下跌，观望为主")
    else:
        print(f"  ⚪ 市场震荡，结构性机会")

    if data['limit_up'] >= 50:
        print(f"  ✅ 涨停家数 {data['limit_up']}，短线情绪活跃")
    elif data['limit_up'] < 20:
        print(f"  ⚠️ 涨停家数偏少，市场情绪低迷")


def main():
    parser = argparse.ArgumentParser(
        description='A股大盘指数行情',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python stock_index.py                    # 显示大盘行情
  python stock_index.py --json           # JSON格式输出
  python stock_index.py --indices         # 仅显示指数
  python stock_index.py --summary         # 仅显示市场概况
        """
    )
    parser.add_argument('--json', action='store_true', help='JSON格式输出')
    parser.add_argument('--indices', action='store_true', help='仅显示主要指数')
    parser.add_argument('--summary', action='store_true', help='仅显示市场概况')
    args = parser.parse_args()

    # 获取数据
    market_data = get_index_data()
    indices_data = []

    for symbol, name in get_major_indices():
        idx = get_index_quote(symbol, name)
        if idx:
            indices_data.append(idx)

    # 输出
    if args.indices:
        # 仅显示指数
        if args.json:
            import json
            print(json.dumps(indices_data, ensure_ascii=False, indent=2))
        else:
            display_market_summary(market_data, indices_data)
    elif args.summary:
        # 仅显示概况
        print(f"市场概况 ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
        print(f"上涨: {market_data['up_stocks']} ({market_data['up_stocks']/market_data['total_stocks']*100:.1f}%)")
        print(f"下跌: {market_data['down_stocks']} ({market_data['down_stocks']/market_data['total_stocks']*100:.1f}%)")
        print(f"涨停: {market_data['limit_up']}")
        print(f"跌停: {market_data['limit_down']}")
        print(f"平均涨跌: {market_data['avg_change']:.2f}%")
    else:
        # 完整显示
        display_market_summary(market_data, indices_data, 'json' if args.json else None)


if __name__ == "__main__":
    main()
