#!/usr/bin/env python3
"""
A股选股器
综合多维度条件筛选股票
"""

import argparse
import akshare as ak
import pandas as pd
from datetime import datetime


def get_all_stocks():
    """获取全市场股票"""
    return ak.stock_zh_a_spot_em()


def screen_stocks(df, conditions):
    """
    多维度选股
    """
    result = df.copy()

    if 'min_price' in conditions and conditions['min_price']:
        result = result[result['最新价'] >= conditions['min_price']]
    if 'max_price' in conditions and conditions['max_price']:
        result = result[result['最新价'] <= conditions['max_price']]

    if 'min_pe' in conditions and conditions['min_pe']:
        result = result[result['市盈率-动态'] >= conditions['min_pe']]
    if 'max_pe' in conditions and conditions['max_pe']:
        pe_valid = (result['市盈率-动态'] > 0) & (result['市盈率-动态'] <= conditions['max_pe'])
        result = result[pe_valid]

    if 'min_pb' in conditions and conditions['min_pb']:
        result = result[result['市净率'] >= conditions['min_pb']]
    if 'max_pb' in conditions and conditions['max_pb']:
        result = result[result['市净率'] <= conditions['max_pb']]

    if 'min_market_cap' in conditions and conditions['min_market_cap']:
        result = result[result['总市值'] >= conditions['min_market_cap'] * 1e8]
    if 'max_market_cap' in conditions and conditions['max_market_cap']:
        result = result[result['总市值'] <= conditions['max_market_cap'] * 1e8]

    if 'min_change' in conditions and conditions['min_change']:
        result = result[result['涨跌幅'] >= conditions['min_change']]
    if 'max_change' in conditions and conditions['max_change']:
        result = result[result['涨跌幅'] <= conditions['max_change']]

    if 'min_turnover' in conditions and conditions['min_turnover']:
        result = result[result['换手率'] >= conditions['min_turnover']]
    if 'max_turnover' in conditions and conditions['max_turnover']:
        result = result[result['换手率'] <= conditions['max_turnover']]

    if conditions.get('up_limit_only'):
        result = result[abs(result['涨跌幅']) >= 9.5]
    if conditions.get('down_limit_only'):
        result = result[abs(result['涨跌幅']) >= 9.5]
    if conditions.get('st_only'):
        result = result[result['名称'].str.contains('ST|.*st', na=False)]
    if conditions.get('low_pe'):
        pe_valid = (result['市盈率-动态'] > 0) & (result['市盈率-动态'] <= 20)
        result = result[pe_valid]
    if conditions.get('value_stock'):
        pe_valid = (result['市盈率-动态'] > 0) & (result['市盈率-动态'] < 15)
        pb_valid = result['市净率'] < 2
        result = result[pe_valid & pb_valid]

    return result


def sort_stocks(df, sort_by='涨跌幅', ascending=False, top_n=None):
    """排序并限制结果数量"""
    result = df.sort_values(sort_by, ascending=ascending)
    if top_n:
        result = result.head(top_n)
    return result


def preset_screens():
    """预设选股方案"""
    return {
        "低估值蓝筹": {
            'max_pe': 15, 'max_pb': 2, 'min_market_cap': 500,
            'min_change': -5, 'max_change': 9,
        },
        "短线热点": {
            'min_change': 3, 'min_turnover': 5, 'max_pe': 50,
        },
        "超跌反弹": {
            'min_change': -8, 'max_change': -3, 'min_turnover': 3,
        },
        "低价股": {
            'min_price': 2, 'max_price': 10, 'min_market_cap': 50,
        },
    }


def display_screen_result(df, screen_name="筛选结果", output_format=None):
    """展示选股结果"""
    if len(df) == 0:
        print("未找到符合条件的股票")
        return

    print(f"\n共筛选出 {len(df)} 只股票\n")

    df_display = df.copy()
    df_display['市值亿'] = df_display['总市值'] / 1e8
    df_display['流通市值亿'] = df_display['流通市值'] / 1e8

    display_cols = ['代码', '名称', '最新价', '涨跌幅', '换手率',
                    '市盈率-动态', '市净率', '市值亿']
    available = [c for c in display_cols if c in df_display.columns]

    if output_format == 'csv':
        print(df_display[available].to_csv(index=False))
    elif output_format == 'json':
        print(df_display[available].to_json(orient='records', force_ascii=False, indent=2))
    else:
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', None)
        print(df_display[available].to_string(index=False))


def main():
    parser = argparse.ArgumentParser(
        description='A股智能选股',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python stock_screener.py                            # 显示所有预设方案
  python stock_screener.py --preset 低估值蓝筹        # 使用预设方案
  python stock_screener.py --pe-max 15 --pb-max 2   # 自定义条件
  python stock_screener.py --change-min 5           # 涨跌幅筛选
  python stock_screener.py --turnover-min 5          # 换手率筛选
  python stock_screener.py --cap-min 100             # 市值筛选
  python stock_screener.py --sort 市盈率-动态        # 按PE排序
  python stock_screener.py --top 50                   # 显示TOP50
  python stock_screener.py --output json             # JSON输出
  python stock_screener.py --list-presets            # 列出所有预设方案
        """
    )
    parser.add_argument('--preset', choices=['低估值蓝筹', '短线热点', '超跌反弹', '低价股'],
                        help='使用预设选股方案')
    parser.add_argument('--pe-min', type=float, help='最小市盈率')
    parser.add_argument('--pe-max', type=float, help='最大市盈率')
    parser.add_argument('--pb-min', type=float, help='最小市净率')
    parser.add_argument('--pb-max', type=float, help='最大市净率')
    parser.add_argument('--price-min', type=float, help='最低价')
    parser.add_argument('--price-max', type=float, help='最高价')
    parser.add_argument('--cap-min', type=float, help='最小市值(亿元)')
    parser.add_argument('--cap-max', type=float, help='最大市值(亿元)')
    parser.add_argument('--change-min', type=float, help='最小涨跌幅(%%)')
    parser.add_argument('--change-max', type=float, help='最大涨跌幅(%%)')
    parser.add_argument('--turnover-min', type=float, help='最小换手率(%%)')
    parser.add_argument('--turnover-max', type=float, help='最大换手率(%%)')
    parser.add_argument('--sort', default='涨跌幅', help='排序字段 (默认: 涨跌幅)')
    parser.add_argument('--asc', action='store_true', help='升序排列')
    parser.add_argument('--top', type=int, default=20, help='显示数量 (默认: 20)')
    parser.add_argument('--output', choices=['csv', 'json'], help='输出格式')
    parser.add_argument('--limit-up', action='store_true', help='仅涨停股')
    parser.add_argument('--limit-down', action='store_true', help='仅跌停股')
    parser.add_argument('--st-only', action='store_true', help='仅ST股')
    parser.add_argument('--low-pe', action='store_true', help='低市盈率股 (PE<20)')
    parser.add_argument('--value-stock', action='store_true', help='低估值股 (PE<15, PB<2)')
    parser.add_argument('--list-presets', action='store_true', help='列出所有预设方案')
    args = parser.parse_args()

    print(f"=== A股智能选股 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")

    if args.list_presets:
        presets = preset_screens()
        print("【预设选股方案】")
        for name, conditions in presets.items():
            print(f"\n{name}:")
            for k, v in conditions.items():
                print(f"  {k}: {v}")
        return

    # 获取全市场数据
    print("正在获取全市场数据...")
    all_stocks = get_all_stocks()
    print(f"共获取 {len(all_stocks)} 只股票\n")

    # 构建筛选条件
    conditions = {}

    if args.preset:
        presets = preset_screens()
        if args.preset in presets:
            conditions.update(presets[args.preset])

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
    if args.change_min:
        conditions['min_change'] = args.change_min
    if args.change_max:
        conditions['max_change'] = args.change_max
    if args.turnover_min:
        conditions['min_turnover'] = args.turnover_min
    if args.turnover_max:
        conditions['max_turnover'] = args.turnover_max
    if args.limit_up:
        conditions['up_limit_only'] = True
    if args.limit_down:
        conditions['down_limit_only'] = True
    if args.st_only:
        conditions['st_only'] = True
    if args.low_pe:
        conditions['low_pe'] = True
    if args.value_stock:
        conditions['value_stock'] = True

    # 筛选
    if conditions:
        result = screen_stocks(all_stocks, conditions)
        result = sort_stocks(result, args.sort, args.asc, args.top)
        screen_name = args.preset if args.preset else "自定义筛选"
        display_screen_result(result, f"{screen_name} (TOP {args.top})", args.output)
    else:
        # 显示所有预设方案
        presets = preset_screens()
        for name, preset_conditions in presets.items():
            result = screen_stocks(all_stocks, preset_conditions)
            result = sort_stocks(result, '涨跌幅', False, 10)
            display_screen_result(result, f"{name} (TOP 10)")
            print("\n" + "-"*80 + "\n")


if __name__ == "__main__":
    main()
