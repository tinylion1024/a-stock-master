#!/usr/bin/env python3
"""
A股板块分析
分析概念板块和行业板块的涨跌，资金流向
"""

import argparse
import akshare as ak
import pandas as pd
from datetime import datetime


def get_concept_boards():
    """获取概念板块实时行情"""
    return ak.stock_board_concept_spot_em()


def get_industry_boards():
    """获取行业板块实时行情"""
    return ak.stock_board_industry_spot_em()


def get_concept_hist(symbol, start_date, end_date):
    """获取概念板块历史走势"""
    return ak.stock_board_concept_hist_em(
        symbol=symbol,
        start_date=start_date,
        end_date=end_date
    )


def get_concept_stocks(symbol):
    """获取概念板块内个股"""
    return ak.stock_board_concept_cons_em(symbol=symbol)


def find_hot_concepts(top_n=10, sort_by='涨跌幅'):
    """寻找热门概念板块"""
    df = get_concept_boards()
    if df is None:
        return None
    df['涨跌幅'] = pd.to_numeric(df['涨跌幅'], errors='coerce')
    df['成交额'] = pd.to_numeric(df['成交额'], errors='coerce')
    result = df.sort_values(sort_by, ascending=False).head(top_n)
    return result


def find_strong_industry(top_n=10):
    """寻找强势行业板块"""
    df = get_industry_boards()
    if df is None:
        return None
    df['涨跌幅'] = pd.to_numeric(df['涨跌幅'], errors='coerce')
    df['资金流入'] = pd.to_numeric(df['资金流入'], errors='coerce')
    result = df[(df['涨跌幅'] > 0) & (df['资金流入'] > 0)]
    result = result.sort_values('涨跌幅', ascending=False).head(top_n)
    return result


def sector_rotation_analysis(concept_list=None, days=5):
    """板块轮动分析"""
    if concept_list is None:
        df = get_concept_boards()
        concept_list = df.nlargest(20, '涨跌幅')['板块名称'].tolist()

    results = []
    for concept in concept_list:
        try:
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - pd.Timedelta(days=days)).strftime('%Y%m%d')
            hist = get_concept_hist(concept, start_date, end_date)

            if len(hist) > 0:
                first_close = hist['收盘'].iloc[0]
                last_close = hist['收盘'].iloc[-1]
                change_pct = (last_close / first_close - 1) * 100
                results.append({
                    'concept': concept,
                    'days': days,
                    'change_pct': change_pct,
                    'avg_volume': hist['成交量'].mean()
                })
        except Exception:
            continue

    results = sorted(results, key=lambda x: x['change_pct'], reverse=True)
    return results


def display_board_analysis(df, title, output_format=None):
    """展示板块分析结果"""
    if df is None or len(df) == 0:
        print("暂无数据")
        return

    columns = ['板块名称', '涨跌幅', '上涨家数', '下跌家数', '成交额', '资金流入']
    available_cols = [c for c in columns if c in df.columns]

    if output_format == 'csv':
        print(df[available_cols].to_csv(index=False))
    elif output_format == 'json':
        print(df[available_cols].to_json(orient='records', force_ascii=False, indent=2))
    else:
        print(f"\n{'='*60}")
        print(f"  {title}")
        print(f"{'='*60}\n")
        print(df[available_cols].to_string(index=False))


def main():
    parser = argparse.ArgumentParser(
        description='A股板块分析',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python stock_sector.py                              # 显示所有板块分析
  python stock_sector.py --concept-top 15             # 概念板块涨幅TOP15
  python stock_sector.py --money-rank                 # 按资金流入排序
  python stock_sector.py --industry                    # 行业板块
  python stock_sector.py --rotation --days 5           # 板块轮动分析
  python stock_sector.py --concept-name 人工智能       # 查看概念板块内个股
  python stock_sector.py --output json                # JSON输出
        """
    )
    parser.add_argument('--concept-top', type=int, default=10, help='概念板块TOPN (默认: 10)')
    parser.add_argument('--industry-top', type=int, default=10, help='行业板块TOPN (默认: 10)')
    parser.add_argument('--money-rank', action='store_true', help='按资金流入排序')
    parser.add_argument('--concept', action='store_true', help='显示概念板块')
    parser.add_argument('--industry', action='store_true', help='显示行业板块')
    parser.add_argument('--rotation', action='store_true', help='板块轮动分析')
    parser.add_argument('--days', type=int, default=5, help='轮动分析天数 (默认: 5)')
    parser.add_argument('--concept-name', help='查看特定概念板块内个股')
    parser.add_argument('--output', choices=['csv', 'json'], help='输出格式')
    args = parser.parse_args()

    print(f"=== A股板块分析 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")

    sort_by = '资金流入净额' if args.money_rank else '涨跌幅'

    if args.concept_name:
        # 查看特定概念板块内个股
        print(f"【{args.concept_name} 板块内个股】")
        df = get_concept_stocks(args.concept_name)
        if df is not None:
            display_cols = ['代码', '名称', '涨跌幅', '成交量', '成交额']
            available = [c for c in display_cols if c in df.columns]
            if args.output == 'csv':
                print(df[available].to_csv(index=False))
            elif args.output == 'json':
                print(df[available].to_json(orient='records', force_ascii=False, indent=2))
            else:
                print(df[available].head(20).to_string(index=False))
        return

    if args.concept:
        print(f"【概念板块涨幅 TOP {args.concept_top}】")
        hot_concepts = find_hot_concepts(args.concept_top, sort_by)
        display_board_analysis(hot_concepts, "概念板块排行", args.output)
        return

    if args.industry:
        print(f"【行业板块强势 TOP {args.industry_top}】")
        strong_industry = find_strong_industry(args.industry_top)
        display_board_analysis(strong_industry, "强势行业板块", args.output)
        return

    if args.rotation:
        print(f"【近期板块轮动（近{args.days}日）】")
        rotation = sector_rotation_analysis(days=args.days)
        if rotation:
            rotation_df = pd.DataFrame(rotation)
            if args.output == 'csv':
                print(rotation_df.to_csv(index=False))
            elif args.output == 'json':
                print(rotation_df.to_json(orient='records', force_ascii=False, indent=2))
            else:
                print(rotation_df.to_string(index=False))
        return

    # 默认显示所有
    print(f"【概念板块涨幅 TOP {args.concept_top}】")
    hot_concepts = find_hot_concepts(args.concept_top)
    display_board_analysis(hot_concepts, "概念板块涨幅排行")

    print("\n" + "="*60 + "\n")

    print(f"【概念板块资金流入 TOP {args.concept_top}】")
    concepts_by_money = find_hot_concepts(args.concept_top, '资金流入净额')
    display_board_analysis(concepts_by_money, "概念板块资金流入排行")

    print("\n" + "="*60 + "\n")

    print(f"【行业板块强势 TOP {args.industry_top}】")
    strong_industry = find_strong_industry(args.industry_top)
    display_board_analysis(strong_industry, "强势行业板块")


if __name__ == "__main__":
    main()
