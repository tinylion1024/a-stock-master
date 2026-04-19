#!/usr/bin/env python3
"""
A股实时行情监控
获取沪深京A股实时行情，支持筛选和排序
"""

import argparse
import akshare as ak
import pandas as pd
from datetime import datetime


def get_realtime_quotes():
    """获取沪深京A股实时行情"""
    df = ak.stock_zh_a_spot_em()
    return df


def filter_stocks(df, conditions):
    """
    筛选股票

    conditions 参数:
        - min_price: 最低价
        - max_price: 最高价
        - min_pe: 最小市盈率
        - max_pe: 最大市盈率
        - min_pb: 最小市净率
        - max_pb: 最大市净率
        - min_market_cap: 最小市值(亿元)
        - max_market_cap: 最大市值(亿元)
        - up_limit_only: 仅涨停股
        - down_limit_only: 仅跌停股
        - st_only: 仅ST股
    """
    result = df.copy()

    if 'min_price' in conditions and conditions['min_price']:
        result = result[result['最新价'] >= conditions['min_price']]

    if 'max_price' in conditions and conditions['max_price']:
        result = result[result['最新价'] <= conditions['max_price']]

    if 'min_pe' in conditions and conditions['min_pe']:
        result = result[result['市盈率-动态'] >= conditions['min_pe']]

    if 'max_pe' in conditions and conditions['max_pe']:
        pe_mask = (result['市盈率-动态'] > 0) & (result['市盈率-动态'] <= conditions['max_pe'])
        result = result[pe_mask]

    if 'min_pb' in conditions and conditions['min_pb']:
        result = result[result['市净率'] >= conditions['min_pb']]

    if 'max_pb' in conditions and conditions['max_pb']:
        result = result[result['市净率'] <= conditions['max_pb']]

    if 'min_market_cap' in conditions and conditions['min_market_cap']:
        result = result[result['总市值'] >= conditions['min_market_cap'] * 1e8]

    if 'max_market_cap' in conditions and conditions['max_market_cap']:
        result = result[result['总市值'] <= conditions['max_market_cap'] * 1e8]

    if conditions.get('up_limit_only'):
        result = result[abs(result['涨跌幅']) >= 9.5]

    if conditions.get('down_limit_only'):
        result = result[abs(result['涨跌幅']) >= 9.5]

    if conditions.get('st_only'):
        result = result[result['名称'].str.contains('ST|.*st', na=False)]

    return result


def sort_stocks(df, sort_by='涨跌幅', ascending=False):
    """排序股票"""
    return df.sort_values(sort_by, ascending=ascending)


def display_quotes(df, columns=None, top_n=None):
    """展示行情数据"""
    if columns:
        df = df[columns]

    if top_n:
        df = df.head(top_n)

    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    print(df.to_string(index=False))


def main():
    parser = argparse.ArgumentParser(
        description='A股实时行情监控',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python stock_quotes.py                          # 显示低估值股票TOP20和涨停股
  python stock_quotes.py --limit-up              # 显示涨停股
  python stock_quotes.py --limit-down            # 显示跌停股
  python stock_quotes.py --pe-max 20 --cap-min 100  # 自定义筛选条件
  python stock_quotes.py --top 50                # 显示TOP50
  python stock_quotes.py --output csv            # 输出为CSV
        """
    )
    parser.add_argument('--limit-up', action='store_true', help='仅显示涨停股')
    parser.add_argument('--limit-down', action='store_true', help='仅显示跌停股')
    parser.add_argument('--st-only', action='store_true', help='仅显示ST股')
    parser.add_argument('--pe-min', type=float, help='最小市盈率')
    parser.add_argument('--pe-max', type=float, help='最大市盈率')
    parser.add_argument('--pb-min', type=float, help='最小市净率')
    parser.add_argument('--pb-max', type=float, help='最大市净率')
    parser.add_argument('--price-min', type=float, help='最低价')
    parser.add_argument('--price-max', type=float, help='最高价')
    parser.add_argument('--cap-min', type=float, help='最小市值(亿元)')
    parser.add_argument('--cap-max', type=float, help='最大市值(亿元)')
    parser.add_argument('--turnover-min', type=float, help='最小换手率(%%)')
    parser.add_argument('--sort', default='涨跌幅', help='排序字段 (默认: 涨跌幅)')
    parser.add_argument('--asc', action='store_true', help='升序排列')
    parser.add_argument('--top', type=int, default=20, help='显示数量 (默认: 20)')
    parser.add_argument('--output', choices=['csv', 'json'], help='输出格式')
    parser.add_argument('--no-header', action='store_true', help='不显示表头')
    args = parser.parse_args()

    print(f"=== A股实时行情 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")

    # 获取全市场行情
    print("正在获取全市场数据...")
    df = get_realtime_quotes()
    print(f"共获取 {len(df)} 只股票\n")

    # 构建筛选条件
    conditions = {}
    if args.limit_up:
        conditions['up_limit_only'] = True
    if args.limit_down:
        conditions['down_limit_only'] = True
    if args.st_only:
        conditions['st_only'] = True
    if args.pe_min:
        conditions['min_pe'] = args.pe_min
    if args.pe_max:
        conditions['max_pe'] = args.pe_max
    if args.pb_min:
        conditions['min_pb'] = args.pb_min
    if args.pb_max:
        conditions['max_pb'] = args.pb_max
    if args.price_min:
        conditions['min_price'] = args.price_min
    if args.price_max:
        conditions['max_price'] = args.price_max
    if args.cap_min:
        conditions['min_market_cap'] = args.cap_min
    if args.cap_max:
        conditions['max_market_cap'] = args.cap_max
    if args.turnover_min:
        conditions['min_turnover'] = args.turnover_min

    # 筛选
    if conditions:
        filtered = filter_stocks(df, conditions)
    else:
        filtered = df

    # 排序
    if args.sort in filtered.columns:
        sorted_df = sort_stocks(filtered, args.sort, args.asc)
    else:
        sorted_df = filtered

    # 限制数量
    result_df = sorted_df.head(args.top)

    # 输出
    if args.output == 'csv':
        print(result_df.to_csv(index=False))
    elif args.output == 'json':
        print(result_df.to_json(orient='records', force_ascii=False, indent=2))
    else:
        display_cols = ['代码', '名称', '最新价', '涨跌幅', '成交量', '成交额',
                        '市盈率-动态', '市净率', '换手率', '总市值']
        available = [c for c in display_cols if c in result_df.columns]
        display_quotes(result_df, available)


if __name__ == "__main__":
    main()
