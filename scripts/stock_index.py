#!/usr/bin/env python3
"""
A股大盘指数行情
获取上证、深证、创业板等主要指数实时行情
使用 stock_zh_ah_spot 接口（腾讯财经，A+H股数据）
"""

import argparse
import akshare as ak
import pandas as pd
from datetime import datetime


def get_index_data():
    """获取指数数据（新浪指数实时行情，带缓存）"""
    if not hasattr(get_index_data, '_cache') or get_index_data._cache is None:
        get_index_data._cache = ak.stock_zh_index_spot_sina()
    return get_index_data._cache


def clear_index_cache():
    """清除指数数据缓存"""
    if hasattr(get_index_data, '_cache'):
        get_index_data._cache = None


def get_ah_stock_data():
    """获取A+H股数据用于市场情绪分析（腾讯财经）"""
    try:
        df = ak.stock_zh_ah_spot()
        return df
    except Exception:
        return None


def get_major_indices():
    """获取主要指数列表（新浪代码格式）"""
    return [
        ('sh000001', '上证指数'),
        ('sz399001', '深证成指'),
        ('sz399006', '创业板指'),
        ('sh000300', '沪深300'),
        ('sh000016', '上证50'),
        ('sh000905', '中证500'),
        ('sh000688', '科创50'),
    ]


def find_index_in_sina(index_code):
    """在新浪指数数据中查找指数"""
    df = get_index_data()
    if df is None or len(df) == 0:
        return None

    # 新浪指数代码格式: sh000001, sz399001 等
    match = df[df['代码'] == index_code]
    if len(match) > 0:
        row = match.iloc[0]
        return {
            'code': str(row['代码']),
            'name': str(row['名称']),
            'price': float(row['最新价']) if pd.notna(row['最新价']) else None,
            'change_pct': float(row['涨跌幅']) if pd.notna(row['涨跌幅']) else None,
            'change_amt': float(row['涨跌额']) if pd.notna(row['涨跌额']) else None,
            'volume': int(row['成交量']) if pd.notna(row['成交量']) else None,
            'amount': int(row['成交额']) if pd.notna(row['成交额']) else None,
            'open': float(row['今开']) if pd.notna(row['今开']) else None,
            'prev_close': float(row['昨收']) if pd.notna(row['昨收']) else None,
            'high': float(row['最高']) if pd.notna(row['最高']) else None,
            'low': float(row['最低']) if pd.notna(row['最低']) else None,
        }

    return None


def display_market_summary(indices_data, output_format=None):
    """展示大盘汇总"""
    if output_format == 'json':
        import json
        output = {
            'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'indices': indices_data
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return

    print(f"\n{'='*70}")
    print(f"  A股大盘行情 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}")

    print(f"\n【主要指数】")
    print(f"{'='*70}")
    print(f"{'指数名称':<12} {'最新价':>12} {'涨跌幅':>10} {'涨跌额':>12}")
    print(f"{'-'*70}")

    for idx in indices_data:
        if idx.get('error'):
            print(f"{idx.get('name', 'N/A'):<12} {'数据获取失败':>12}")
        else:
            change = idx.get('change_pct', 0)
            if isinstance(change, (int, float)):
                change_str = f"{change:+.2f}%"
                arrow = "↑" if change > 0 else "↓" if change < 0 else "-"
            else:
                change_str = str(change)
                arrow = ""

            price = idx.get('price', 'N/A')
            if isinstance(price, (int, float)):
                price_str = f"{price:.2f}"
            else:
                price_str = str(price)

            change_amt = idx.get('change_amt', 'N/A')
            if isinstance(change_amt, (int, float)):
                change_str2 = f"{change_amt:+.3f}"
            else:
                change_str2 = str(change_amt)

            name = idx.get('name', 'N/A')
            print(f"{name:<12} {price_str:>12} {change_str:>10} {change_str2:>12}")

    print(f"{'='*70}")


def display_market_sentiment(df):
    """展示市场情绪"""
    if df is None or len(df) == 0:
        return

    # 涨跌统计
    up = len(df[df['涨跌幅'] > 0])
    down = len(df[df['涨跌幅'] < 0])
    flat = len(df[df['涨跌幅'] == 0])
    total = len(df)

    limit_up = len(df[df['涨跌幅'] >= 9.5])
    limit_down = len(df[df['涨跌幅'] <= -9.5])

    avg_change = df['涨跌幅'].mean()
    total_amount = df['成交额'].sum()

    print(f"\n【市场概况】")
    print(f"  股票总数: {total}")
    print(f"  上涨: {up} ({up/total*100:.1f}%)")
    print(f"  下跌: {down} ({down/total*100:.1f}%)")
    print(f"  平盘: {flat}")
    print(f"  涨停: {limit_up}")
    print(f"  跌停: {limit_down}")
    print(f"  平均涨跌: {avg_change:+.2f}%")
    print(f"  总成交额: {total_amount/1e8:.2f}亿")

    print(f"\n【市场情绪】")
    if avg_change > 1 and up/total > 0.6:
        print(f"  🟢 市场强势上涨，积极做多")
    elif avg_change > 0.5 and up/total > 0.5:
        print(f"  🟡 市场温和上涨，谨慎做多")
    elif avg_change < -1 and up/total < 0.4:
        print(f"  🔴 市场弱势下跌，控制风险")
    elif avg_change < -0.5 and up/total < 0.5:
        print(f"  🟠 市场小幅下跌，观望为主")
    else:
        print(f"  ⚪ 市场震荡，结构性机会")

    if limit_up >= 50:
        print(f"  ✅ 涨停家数 {limit_up}，短线情绪活跃")
    elif limit_up < 20:
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

    print("正在获取市场数据...")

    # 清除缓存确保获取最新数据
    clear_index_cache()

    # 获取指数数据
    indices_data = []
    for symbol, name in get_major_indices():
        idx = find_index_in_sina(symbol)
        if idx:
            idx['name'] = name  # 使用标准名称
            indices_data.append(idx)
        else:
            indices_data.append({'name': name, 'error': '未找到'})

    # 获取完整数据用于情绪分析
    try:
        df = get_ah_stock_data()
    except Exception as e:
        print(f"获取市场数据失败: {e}")
        df = None

    # 输出
    if args.indices:
        # 仅显示指数
        display_market_summary(indices_data, 'json' if args.json else None)
    elif args.summary:
        # 仅显示概况
        if df is not None:
            display_market_sentiment(df)
        else:
            print("无法获取市场数据")
    else:
        # 完整显示
        display_market_summary(indices_data, 'json' if args.json else None)
        if df is not None:
            display_market_sentiment(df)


if __name__ == "__main__":
    main()
