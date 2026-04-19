#!/usr/bin/env python3
"""
A股全市场行情导出
获取并导出所有股票的实时行情数据
"""

import argparse
import akshare as ak
import pandas as pd
from datetime import datetime


def get_all_quotes():
    """获取沪深京A股全市场实时行情"""
    df = ak.stock_zh_a_spot_em()
    return df


def export_quotes(df, output_file=None, output_format='csv'):
    """导出行情数据"""
    if df is None or len(df) == 0:
        print("无数据可导出")
        return

    # 单位转换
    df_export = df.copy()
    df_export['总市值_亿'] = df_export['总市值'] / 1e8
    df_export['流通市值_亿'] = df_export['流通市值'] / 1e8
    df_export['成交额_亿'] = df_export['成交额'] / 1e8

    # 选择输出列
    output_cols = [
        '代码', '名称', '最新价', '涨跌幅', '涨跌额', '成交量', '成交额',
        '最高', '最低', '今开', '昨收', '换手率',
        '市盈率-动态', '市净率', '总市值', '流通市值',
        '总市值_亿', '流通市值_亿', '成交额_亿'
    ]
    # 只保留存在的列
    cols = [c for c in output_cols if c in df_export.columns]

    if output_format == 'csv':
        if output_file:
            df_export[cols].to_csv(output_file, index=False, encoding='utf-8-sig')
            print(f"已导出到: {output_file}")
        else:
            date_str = datetime.now().strftime('%Y%m%d')
            default_file = f"a-stock-{date_str}/data/market_{date_str}.csv"
            df_export[cols].to_csv(default_file, index=False, encoding='utf-8-sig')
            print(f"已导出到: {default_file}")
    elif output_format == 'json':
        if output_file:
            df_export[cols].to_json(output_file, orient='records', force_ascii=False, indent=2)
            print(f"已导出到: {output_file}")
        else:
            print(df_export[cols].to_json(orient='records', force_ascii=False, indent=2))
    elif output_format == 'excel':
        if output_file:
            df_export[cols].to_excel(output_file, index=False)
            print(f"已导出到: {output_file}")
        else:
            date_str = datetime.now().strftime('%Y%m%d')
            default_file = f"a-stock-{date_str}/data/market_{date_str}.xlsx"
            df_export[cols].to_excel(default_file, index=False)
            print(f"已导出到: {default_file}")


def display_summary(df):
    """显示数据概览"""
    if df is None or len(df) == 0:
        return

    print(f"\n{'='*60}")
    print(f"  全市场行情数据概览")
    print(f"{'='*60}")
    print(f"  获取时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  股票总数: {len(df)}")

    # 涨跌统计
    up = len(df[df['涨跌幅'] > 0])
    down = len(df[df['涨跌幅'] < 0])
    flat = len(df[df['涨跌幅'] == 0])
    print(f"\n  涨跌统计:")
    print(f"    上涨: {up} ({up/len(df)*100:.1f}%)")
    print(f"    下跌: {down} ({down/len(df)*100:.1f}%)")
    print(f"    平盘: {flat} ({flat/len(df)*100:.1f}%)")

    # 涨停跌停
    limit_up = len(df[df['涨跌幅'] >= 9.5])
    limit_down = len(df[df['涨跌幅'] <= -9.5])
    print(f"\n  涨停/跌停:")
    print(f"    涨停: {limit_up}")
    print(f"    跌停: {limit_down}")

    # 成交额统计
    total_vol = df['成交额'].sum() / 1e8
    avg_vol = df['成交额'].mean() / 1e8
    print(f"\n  成交额统计:")
    print(f"    总成交额: {total_vol:.2f}亿")
    print(f"    平均成交额: {avg_vol:.2f}亿")

    # 市盈率分布
    pe_valid = df[df['市盈率-动态'] > 0]['市盈率-动态']
    if len(pe_valid) > 0:
        print(f"\n  市盈率(动态)统计:")
        print(f"    有PE股票数: {len(pe_valid)}")
        print(f"    PE中位数: {pe_valid.median():.2f}")
        print(f"    PE均值: {pe_valid.mean():.2f}")

    print(f"{'='*60}")


def display_top(df, sort_by='涨跌幅', top_n=20, ascending=False):
    """显示TOP股票"""
    if df is None or len(df) == 0:
        return

    if sort_by not in df.columns:
        print(f"排序字段 {sort_by} 不存在")
        return

    df_sorted = df.sort_values(sort_by, ascending=ascending).head(top_n)

    display_cols = ['代码', '名称', '最新价', '涨跌幅', '成交量', '成交额', '市盈率-动态', '市净率']
    cols = [c for c in display_cols if c in df_sorted.columns]

    print(f"\n【按 {sort_by} 排序 TOP {top_n}】")
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    print(df_sorted[cols].to_string(index=False))


def main():
    parser = argparse.ArgumentParser(
        description='A股全市场行情导出',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python stock_quote_export.py                    # 显示数据概览
  python stock_quote_export.py --export          # 导出到CSV
  python stock_quote_export.py -o market.csv      # 导出到指定文件
  python stock_quote_export.py --json             # JSON格式输出
  python stock_quote_export.py --top-涨跌幅 30  # 显示涨跌幅TOP30
  python stock_quote_export.py --top-成交额     # 显示成交额TOP
  python stock_quote_export.py --pe-above 0      # 筛选有PE的股票
        """
    )
    parser.add_argument('-o', '--output', help='输出文件路径')
    parser.add_argument('--export', action='store_true', help='导出到CSV文件')
    parser.add_argument('--json', action='store_true', help='JSON格式输出')
    parser.add_argument('--excel', action='store_true', help='Excel格式输出')
    parser.add_argument('--summary', action='store_true', help='仅显示数据概览')
    parser.add_argument('--top', type=int, help='显示TOP N股票')
    parser.add_argument('--top-sort', default='涨跌幅', help='TOP排序字段 (默认: 涨跌幅)')
    parser.add_argument('--asc', action='store_true', help='升序排列')
    parser.add_argument('--pe-above', type=float, help='筛选市盈率大于该值')
    parser.add_argument('--pe-max', type=float, help='筛选市盈率小于该值')
    parser.add_argument('--pb-max', type=float, help='筛选市净率小于该值')
    parser.add_argument('--cap-min', type=float, help='筛选总市值大于该值(亿)')
    parser.add_argument('--cap-max', type=float, help='筛选总市值小于该值(亿)')
    args = parser.parse_args()

    print("正在获取全市场行情数据...")
    df = get_all_quotes()
    print(f"获取完成，共 {len(df)} 只股票\n")

    # 应用筛选
    if args.pe_above is not None:
        df = df[df['市盈率-动态'] > args.pe_above]
    if args.pe_max is not None:
        df = df[(df['市盈率-动态'] > 0) & (df['市盈率-动态'] <= args.pe_max)]
    if args.pb_max is not None:
        df = df[df['市净率'] <= args.pb_max]
    if args.cap_min is not None:
        df = df[df['总市值'] >= args.cap_min * 1e8]
    if args.cap_max is not None:
        df = df[df['总市值'] <= args.cap_max * 1e8]

    print(f"筛选后剩余 {len(df)} 只股票")

    # 确定输出格式
    if args.json:
        output_format = 'json'
    elif args.excel:
        output_format = 'excel'
    else:
        output_format = 'csv'

    # 确定输出文件
    output_file = args.output if args.output else None

    # 输出
    if args.summary:
        display_summary(df)
    elif args.top:
        display_top(df, sort_by=args.top_sort, top_n=args.top, ascending=args.asc)
    elif args.export or args.output or args.json or args.excel:
        export_quotes(df, output_file, output_format)
    else:
        # 默认显示概览
        display_summary(df)


if __name__ == "__main__":
    main()
