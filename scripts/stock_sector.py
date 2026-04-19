#!/usr/bin/env python3
"""
A股板块分析
分析概念板块和行业板块的涨跌、资金流向
"""

import akshare as ak
import pandas as pd
from datetime import datetime


def get_concept_boards():
    """获取概念板块实时行情"""
    df = ak.stock_board_concept_spot_em()
    return df


def get_industry_boards():
    """获取行业板块实时行情"""
    df = ak.stock_board_industry_spot_em()
    return df


def get_concept_hist(symbol, start_date, end_date):
    """获取概念板块历史走势"""
    df = ak.stock_board_concept_hist_em(
        symbol=symbol,
        start_date=start_date,
        end_date=end_date
    )
    return df


def get_concept_stocks(symbol):
    """获取概念板块内个股"""
    df = ak.stock_board_concept_cons_em(symbol=symbol)
    return df


def find_hot_concepts(top_n=10, sort_by='涨跌幅'):
    """
    寻找热门概念板块

    sort_by: '涨跌幅' / '资金流入净额' / '成交额'
    """
    df = get_concept_boards()

    # 清洗数据
    df['涨跌幅'] = pd.to_numeric(df['涨跌幅'], errors='coerce')
    df['成交额'] = pd.to_numeric(df['成交额'], errors='coerce')

    # 排序
    result = df.sort_values(sort_by, ascending=False).head(top_n)

    return result


def find_strong_industry(top_n=10):
    """
    寻找强势行业板块
    条件：上涨且有资金流入
    """
    df = get_industry_boards()

    df['涨跌幅'] = pd.to_numeric(df['涨跌幅'], errors='coerce')
    df['资金流入'] = pd.to_numeric(df['资金流入'], errors='coerce')

    # 筛选上涨且有资金流入的板块
    result = df[(df['涨跌幅'] > 0) & (df['资金流入'] > 0)]
    result = result.sort_values('涨跌幅', ascending=False).head(top_n)

    return result


def compare_sector_performance(boards_df):
    """
    对比板块表现
    计算今日涨跌家数比、资金流入等
    """
    stats = {
        'total': len(boards_df),
        'up': len(boards_df[boards_df['涨跌幅'] > 0]),
        'down': len(boards_df[boards_df['涨跌幅'] < 0]),
        'flat': len(boards_df[boards_df['涨跌幅'] == 0]),
        'avg_inflow': boards_df['资金流入'].mean() if '资金流入' in boards_df.columns else 0
    }

    stats['up_ratio'] = stats['up'] / stats['total'] * 100 if stats['total'] > 0 else 0

    return stats


def sector_rotation_analysis(concept_list=None, days=5):
    """
    板块轮动分析
    追踪近期强势板块的持续性
    """
    if concept_list is None:
        # 取涨幅前20的概念板块
        df = get_concept_boards()
        concept_list = df.nlargest(20, '涨跌幅')['板块名称'].tolist()

    results = []

    for concept in concept_list:
        try:
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - pd.Timedelta(days=days)).strftime('%Y%m%d')

            hist = get_concept_hist(concept, start_date, end_date)

            if len(hist) > 0:
                # 计算累计涨跌幅
                first_close = hist['收盘'].iloc[0]
                last_close = hist['收盘'].iloc[-1]
                change_pct = (last_close / first_close - 1) * 100

                results.append({
                    'concept': concept,
                    'days': days,
                    'change_pct': change_pct,
                    'avg_volume': hist['成交量'].mean()
                })
        except Exception as e:
            continue

    # 按涨幅排序
    results = sorted(results, key=lambda x: x['change_pct'], reverse=True)

    return results


def display_board_analysis(df, title, columns=None):
    """展示板块分析结果"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

    if columns is None:
        columns = ['板块名称', '涨跌幅', '上涨家数', '下跌家数', '成交额', '资金流入']

    available_cols = [c for c in columns if c in df.columns]
    print(df[available_cols].to_string(index=False))


if __name__ == "__main__":
    print(f"=== A股板块分析 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")

    # 概念板块涨幅排行
    print("【概念板块涨幅 TOP 15】")
    hot_concepts = find_hot_concepts(15, sort_by='涨跌幅')
    display_board_analysis(hot_concepts, "概念板块涨幅排行")

    print("\n" + "="*60 + "\n")

    # 概念板块资金流入排行
    print("【概念板块资金流入 TOP 10】")
    concepts_by_money = find_hot_concepts(10, sort_by='资金流入净额')
    display_board_analysis(concepts_by_money, "概念板块资金流入排行")

    print("\n" + "="*60 + "\n")

    # 行业板块分析
    print("【行业板块强势排行】")
    strong_industry = find_strong_industry(15)
    display_board_analysis(strong_industry, "强势行业板块")

    print("\n" + "="*60 + "\n")

    # 板块轮动追踪
    print("【近期板块轮动（近5日）】")
    rotation = sector_rotation_analysis(days=5)
    if rotation:
        rotation_df = pd.DataFrame(rotation)
        print(rotation_df.to_string(index=False))