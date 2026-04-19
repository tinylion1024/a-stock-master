#!/usr/bin/env python3
"""
A股资金流向分析
分析个股、概念、行业资金流向，追踪主力动向
"""

import akshare as ak
import pandas as pd
from datetime import datetime


def get_individual_fund_flow(symbol="即时"):
    """
    获取个股资金流

    symbol:
        - "即时": 今日即时资金流
        - "3日排行": 近3日资金流排行
        - "5日排行": 近5日资金流排行
        - "10日排行": 近10日资金流排行
    """
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
    """
    寻找主力持续买入的股票
    筛选条件：近3日主力净流入排名前列
    """
    df = get_individual_fund_flow("3日排行")

    # 清洗数据，移除无效值
    df = df[df['股票代码'].str.len() == 6]
    df['资金流入净额'] = pd.to_numeric(df['资金流入净额'], errors='coerce')

    # 按净流入排序
    result = df.sort_values('资金流入净额', ascending=False).head(top_n)

    return result


def find_hot_sector_funds(top_n=10):
    """
    寻找资金大幅流入的热门板块
    """
    concept = get_concept_fund_flow("即时")
    concept = concept[concept['涨跌幅'] > 0]  # 只看上涨板块
    concept = concept.sort_values('资金流入净额', ascending=False).head(top_n)

    return concept


def display_fund_flow(df, title=""):
    """展示资金流数据"""
    if title:
        print(f"\n{'='*60}")
        print(f"  {title}")
        print(f"{'='*60}\n")

    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)

    # 单位转换
    if '资金流入净额' in df.columns:
        df_display = df.copy()
        df_display['净流入亿'] = df_display['资金流入净额'] / 1e8
        if '成交额' in df_display.columns:
            df_display['成交额亿'] = df_display['成交额'] / 1e8

        display_cols = [c for c in ['股票代码', '股票简称', '最新价', '涨跌幅',
                                     '资金流入净额', '净流入亿', '成交额亿'] if c in df_display.columns]
        print(df_display[display_cols].to_string(index=False))
    else:
        print(df.to_string(index=False))


if __name__ == "__main__":
    print(f"=== A股资金流向 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")

    # 大盘主力资金
    print("【大盘主力资金】")
    main_flow = get_main_fund_flow()
    print(main_flow)

    print("\n" + "="*60 + "\n")

    # 近3日主力净流入排行
    print("【近3日主力净流入 TOP 20】")
    top_stocks = find_main_money_stocks(20)
    display_fund_flow(top_stocks, "主力资金流向排行")

    print("\n" + "="*60 + "\n")

    # 热门板块资金流
    print("【今日概念板块资金流入 TOP 10】")
    hot_sector = find_hot_sector_funds(10)
    display_fund_flow(hot_sector, "热门板块")