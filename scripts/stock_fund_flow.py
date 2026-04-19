#!/usr/bin/env python3
"""
A股资金流向分析
分析个股、概念、行业资金流向，追踪主力动向
"""

import argparse
import akshare as ak
import pandas as pd
from datetime import datetime


def get_individual_fund_flow(symbol="即时"):
    """获取个股资金流"""
    df = ak.stock_fund_flow_individual(symbol=symbol)
    return df


def get_concept_fund_flow(symbol="即时"):
    """获取概念板块资金流"""
    df = ak.stock_fund_flow_concept(symbol=symbol)
    return df


def get_industry_fund_flow(symbol="即时"):
    """获取行业板块资金流"""
    df = ak.stock_fund_flow_industry(symbol=symbol)
    return df


def get_main_fund_flow():
    """获取主力资金流（大盘）"""
    df = ak.stock_main_fund_flow()
    return df


def find_main_money_stocks(top_n=20):
    """寻找主力持续买入的股票"""
    df = get_individual_fund_flow("3日排行")
    if df is None:
        return None
    df = df[df['股票代码'].str.len() == 6]
    df['资金流入净额'] = pd.to_numeric(df['资金流入净额'], errors='coerce')
    result = df.sort_values('资金流入净额', ascending=False).head(top_n)
    return result


def find_hot_sector_funds(top_n=10):
    """寻找资金大幅流入的热门板块"""
    concept = get_concept_fund_flow("即时")
    if concept is None:
        return None
    concept = concept[concept['涨跌幅'] > 0]
    concept = concept.sort_values('资金流入净额', ascending=False).head(top_n)
    return concept


def display_fund_flow(df, title="", output_format=None):
    """展示资金流数据"""
    if title:
        print(f"\n{'='*60}")
        print(f"  {title}")
        print(f"{'='*60}\n")

    if df is None or len(df) == 0:
        print("暂无数据")
        return

    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)

    if '资金流入净额' in df.columns:
        df_display = df.copy()
        df_display['净流入亿'] = df_display['资金流入净额'] / 1e8
        if '成交额' in df_display.columns:
            df_display['成交额亿'] = df_display['成交额'] / 1e8

        display_cols = [c for c in ['股票代码', '股票简称', '最新价', '涨跌幅',
                                     '资金流入净额', '净流入亿', '成交额亿'] if c in df_display.columns]

        if output_format == 'csv':
            print(df_display[display_cols].to_csv(index=False))
        elif output_format == 'json':
            print(df_display[display_cols].to_json(orient='records', force_ascii=False, indent=2))
        else:
            print(df_display[display_cols].to_string(index=False))
    else:
        if output_format == 'csv':
            print(df.to_csv(index=False))
        elif output_format == 'json':
            print(df.to_json(orient='records', force_ascii=False, indent=2))
        else:
            print(df.to_string(index=False))


def main():
    parser = argparse.ArgumentParser(
        description='A股资金流向分析',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python stock_fund_flow.py                          # 显示主力资金和热点板块
  python stock_fund_flow.py --main-flow              # 仅显示大盘主力资金
  python stock_fund_flow.py --rank-3d                # 近3日资金净流入排行
  python stock_fund_flow.py --hot-sector            # 热门板块资金流
  python stock_fund_flow.py --top 30                # 显示TOP30
  python stock_fund_flow.py --output csv            # 输出为CSV
        """
    )
    parser.add_argument('--main-flow', action='store_true', help='显示大盘主力资金')
    parser.add_argument('--rank-3d', action='store_true', help='近3日资金净流入排行')
    parser.add_argument('--rank-5d', action='store_true', help='近5日资金净流入排行')
    parser.add_argument('--rank-10d', action='store_true', help='近10日资金净流入排行')
    parser.add_argument('--hot-sector', action='store_true', help='热门板块资金流')
    parser.add_argument('--top', type=int, default=20, help='显示数量 (默认: 20)')
    parser.add_argument('--output', choices=['csv', 'json'], help='输出格式')
    args = parser.parse_args()

    print(f"=== A股资金流向 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")

    # 根据参数决定显示内容
    if args.main_flow:
        print("【大盘主力资金】")
        main_flow = get_main_fund_flow()
        if main_flow is not None:
            print(main_flow.to_string(index=False))
        return

    if args.rank_3d:
        print(f"【近3日主力净流入 TOP {args.top}】")
        top_stocks = find_main_money_stocks(args.top)
        display_fund_flow(top_stocks, "主力资金流向排行", args.output)
        return

    if args.rank_5d:
        print(f"【近5日主力净流入 TOP {args.top}】")
        df = get_individual_fund_flow("5日排行")
        if df is not None:
            df = df[df['股票代码'].str.len() == 6]
            df['资金流入净额'] = pd.to_numeric(df['资金流入净额'], errors='coerce')
            top_stocks = df.sort_values('资金流入净额', ascending=False).head(args.top)
            display_fund_flow(top_stocks, "5日资金流向排行", args.output)
        return

    if args.rank_10d:
        print(f"【近10日主力净流入 TOP {args.top}】")
        df = get_individual_fund_flow("10日排行")
        if df is not None:
            df = df[df['股票代码'].str.len() == 6]
            df['资金流入净额'] = pd.to_numeric(df['资金流入净额'], errors='coerce')
            top_stocks = df.sort_values('资金流入净额', ascending=False).head(args.top)
            display_fund_flow(top_stocks, "10日资金流向排行", args.output)
        return

    if args.hot_sector:
        print(f"【热门板块资金流入 TOP {args.top}】")
        hot_sector = find_hot_sector_funds(args.top)
        display_fund_flow(hot_sector, "热门板块", args.output)
        return

    # 默认显示所有
    print("【大盘主力资金】")
    main_flow = get_main_fund_flow()
    if main_flow is not None:
        print(main_flow.to_string(index=False))

    print("\n" + "="*60 + "\n")

    print(f"【近3日主力净流入 TOP {args.top}】")
    top_stocks = find_main_money_stocks(args.top)
    display_fund_flow(top_stocks, "主力资金流向排行", args.output)

    print("\n" + "="*60 + "\n")

    print(f"【今日概念板块资金流入 TOP {args.top}】")
    hot_sector = find_hot_sector_funds(args.top)
    display_fund_flow(hot_sector, "热门板块", args.output)


if __name__ == "__main__":
    main()
