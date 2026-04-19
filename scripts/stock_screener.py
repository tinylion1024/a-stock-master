#!/usr/bin/env python3
"""
A股选股器
综合多维度条件筛选股票
"""

import akshare as ak
import pandas as pd
from datetime import datetime


def get_all_stocks():
    """获取全市场股票"""
    df = ak.stock_zh_a_spot_em()
    return df


def screen_stocks(df, conditions):
    """
    多维度选股

    conditions 参数:
        ---- 价格类 ----
        - min_price: 最低价
        - max_price: 最高价

        ---- 市盈率 ----
        - min_pe: 最小市盈率
        - max_pe: 最大市盈率

        ---- 市净率 ----
        - min_pb: 最小市净率
        - max_pb: 最大市净率

        ---- 市值类 ----
        - min_market_cap: 最小市值(亿元)
        - max_market_cap: 最大市值(亿元)

        ---- 涨跌幅 ----
        - min_change: 最小涨跌幅(%)
        - max_change: 最大涨跌幅(%)

        ---- 成交量 ----
        - min_volume: 最小成交量
        - max_volume: 最大成交量

        ---- 换手率 ----
        - min_turnover: 最小换手率(%)
        - max_turnover: 最大换手率(%)

        ---- 特殊筛选 ----
        - up_limit_only: 仅涨停股
        - down_limit_only: 仅跌停股
        - st_only: 仅ST股
        - new_stock_only: 仅新股（上市30天内）
        - low_pe: 低市盈率 (PE 0-20)
        - value_stock: 低估值 (PE<15, PB<2)
    """
    result = df.copy()

    # 价格筛选
    if 'min_price' in conditions and conditions['min_price']:
        result = result[result['最新价'] >= conditions['min_price']]
    if 'max_price' in conditions and conditions['max_price']:
        result = result[result['最新价'] <= conditions['max_price']]

    # 市盈率筛选
    if 'min_pe' in conditions and conditions['min_pe']:
        result = result[result['市盈率-动态'] >= conditions['min_pe']]
    if 'max_pe' in conditions and conditions['max_pe']:
        pe_valid = (result['市盈率-动态'] > 0) & (result['市盈率-动态'] <= conditions['max_pe'])
        result = result[pe_valid]

    # 市净率筛选
    if 'min_pb' in conditions and conditions['min_pb']:
        result = result[result['市净率'] >= conditions['min_pb']]
    if 'max_pb' in conditions and conditions['max_pb']:
        result = result[result['市净率'] <= conditions['max_pb']]

    # 市值筛选
    if 'min_market_cap' in conditions and conditions['min_market_cap']:
        result = result[result['总市值'] >= conditions['min_market_cap'] * 1e8]
    if 'max_market_cap' in conditions and conditions['max_market_cap']:
        result = result[result['总市值'] <= conditions['max_market_cap'] * 1e8]

    # 涨跌幅筛选
    if 'min_change' in conditions and conditions['min_change']:
        result = result[result['涨跌幅'] >= conditions['min_change']]
    if 'max_change' in conditions and conditions['max_change']:
        result = result[result['涨跌幅'] <= conditions['max_change']]

    # 换手率筛选
    if 'min_turnover' in conditions and conditions['min_turnover']:
        result = result[result['换手率'] >= conditions['min_turnover']]
    if 'max_turnover' in conditions and conditions['max_turnover']:
        result = result[result['换手率'] <= conditions['max_turnover']]

    # 成交量筛选
    if 'min_volume' in conditions and conditions['min_volume']:
        result = result[result['成交量'] >= conditions['min_volume']]
    if 'max_volume' in conditions and conditions['max_volume']:
        result = result[result['成交量'] <= conditions['max_volume']]

    # 特殊筛选
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
    """
    预设选股方案

    返回预设条件组合
    """
    presets = {
        "低估值蓝筹": {
            'max_pe': 15,
            'max_pb': 2,
            'min_market_cap': 500,  # 500亿以上
            'min_change': -5,
            'max_change': 9,
        },
        "短线热点": {
            'min_change': 3,
            'min_turnover': 5,
            'max_pe': 50,
        },
        "超跌反弹": {
            'min_change': -8,
            'max_change': -3,
            'min_turnover': 3,
        },
        "低价股": {
            'min_price': 2,
            'max_price': 10,
            'min_market_cap': 50,
        },
        "次新股": {
            'min_turnover': 10,
            'max_change': 20,
        },
        "ST摘帽预期": {
            'st_only': True,
            'min_change': -5,
        }
    }

    return presets


def display_screen_result(df, screen_name="筛选结果"):
    """展示选股结果"""
    print(f"\n{'='*80}")
    print(f"  {screen_name}")
    print(f"{'='*80}\n")

    if len(df) == 0:
        print("未找到符合条件的股票")
        return

    print(f"共筛选出 {len(df)} 只股票\n")

    # 单位转换
    df_display = df.copy()
    df_display['市值亿'] = df_display['总市值'] / 1e8
    df_display['流通市值亿'] = df_display['流通市值'] / 1e8

    display_cols = ['代码', '名称', '最新价', '涨跌幅', '换手率',
                    '市盈率-动态', '市净率', '市值亿']

    available = [c for c in display_cols if c in df_display.columns]
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)

    print(df_display[available].to_string(index=False))


if __name__ == "__main__":
    print(f"=== A股智能选股 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")

    # 获取全市场数据
    print("正在获取全市场数据...")
    all_stocks = get_all_stocks()
    print(f"共获取 {len(all_stocks)} 只股票\n")

    # 预设方案
    presets = preset_screens()

    # 演示各预设方案
    for name, conditions in presets.items():
        result = screen_stocks(all_stocks, conditions)
        result = sort_stocks(result, '涨跌幅', ascending=False, top_n=10)
        display_screen_result(result, f"{name} (TOP 10)")

        print("\n" + "-"*80 + "\n")