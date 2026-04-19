#!/usr/bin/env python3
"""
A股实时行情监控
获取沪深京A股实时行情，支持筛选和排序
"""

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


if __name__ == "__main__":
    print(f"=== A股实时行情 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")

    # 获取全市场行情
    df = get_realtime_quotes()

    # 示例：筛选低估值股票
    print("【低估值股票 TOP 20】(PE<15, PB<2, 市值>100亿)")
    filtered = filter_stocks(df, {
        'min_pe': 0.1,
        'max_pe': 15,
        'max_pb': 2,
        'min_market_cap': 100
    })
    sorted_df = sort_stocks(filtered, '市盈率-动态')
    display_quotes(sorted_df, [
        '代码', '名称', '最新价', '涨跌幅', '市盈率-动态', '市净率', '总市值'
    ], top_n=20)

    print("\n" + "="*60 + "\n")

    # 示例：今日涨停股
    print("【今日涨停股】")
    limit_up = filter_stocks(df, {'up_limit_only': True})
    display_quotes(limit_up, [
        '代码', '名称', '最新价', '涨跌幅', '成交量', '成交额'
    ], top_n=20)