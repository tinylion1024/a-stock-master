#!/usr/bin/env python3
"""
A股基本面分析
分析个股财务指标、估值、业绩等
"""

import akshare as ak
import pandas as pd
from datetime import datetime


def get_stock_info(symbol):
    """获取个股基本信息"""
    df = ak.stock_individual_info_em(symbol=symbol)
    return df


def get_financial_indicator(symbol, period="按报告期"):
    """
    获取财务分析指标

    参数:
        symbol: 股票代码(带后缀，如 "000001.SZ")
        period: "按报告期" 或 "按单季度"
    """
    df = ak.stock_financial_analysis_indicator_em(
        symbol=symbol,
        indicator=period
    )
    return df


def get_balance_sheet(date="20240331"):
    """
    获取资产负债表

    参数:
        date: 报告期，格式 YYYY0331/YYYY0630/YYYY0930/YYYY1231
    """
    df = ak.stock_zcfz_em(date=date)
    return df


def get_income_statement(date="20240331"):
    """获取利润表"""
    df = ak.stock_lrb_em(date=date)
    return df


def get_cash_flow(date="20240331"):
    """获取现金流量表"""
    df = ak.stock_xjll_em(date=date)
    return df


def get_market_pe_pb():
    """获取市场整体市盈率和市净率"""
    pe_df = ak.stock_a_ttm_lyr()
    pb_df = ak.stock_a_all_pb()
    return pe_df, pb_df


def evaluate_valuation(symbol):
    """
    估值评估
    对比个股与市场整体估值
    """
    # 获取个股信息
    info = get_stock_info(symbol)

    # 获取财务指标
    try:
        indicator = get_financial_indicator(symbol + ".SZ" if symbol.startswith("0") else symbol + ".SH")
    except:
        indicator = None

    # 获取市场估值
    market_pe, market_pb = get_market_pe_pb()

    result = {
        'symbol': symbol,
        'info': info,
        'indicator': indicator,
        'market_pe': market_pe,
        'market_pb': market_pb
    }

    return result


def screen_by_financial(df, conditions):
    """
    财务指标筛选

    conditions 参数:
        - min_pe: 最小市盈率
        - max_pe: 最大市盈率
        - min_pb: 最小市净率
        - max_pb: 最大市净率
        - min_roe: 最小净资产收益率
        - max_gross_margin: 最大毛利率
        - min_net_margin: 最小净利率
    """
    result = df.copy()

    if 'min_pe' in conditions and conditions['min_pe']:
        result = result[result['市盈率-动态'] >= conditions['min_pe']]

    if 'max_pe' in conditions and conditions['max_pe']:
        result = result[result['市盈率-动态'] <= conditions['max_pe']]

    if 'min_pb' in conditions and conditions['min_pb']:
        result = result[result['市净率'] >= conditions['min_pb']]

    if 'max_pb' in conditions and conditions['max_pb']:
        result = result[result['市净率'] <= conditions['max_pb']]

    # 市值筛选（单位：亿元）
    if 'min_market_cap' in conditions and conditions['min_market_cap']:
        result = result[result['总市值'] >= conditions['min_market_cap'] * 1e8]

    if 'max_market_cap' in conditions and conditions['max_market_cap']:
        result = result[result['总市值'] <= conditions['max_market_cap'] * 1e8]

    return result


def analyze_stock_financial(symbol):
    """
    综合财务分析

    分析维度：
    1. 盈利能力（毛利率、净利率、ROE）
    2. 成长性（营收增长、利润增长）
    3. 偿债能力（资产负债率）
    4. 运营效率（周转率）
    """
    try:
        # 获取财务指标
        indicator = get_financial_indicator(symbol, period="按报告期")

        if indicator is None or len(indicator) == 0:
            return None

        # 取最新数据
        latest = indicator.iloc[-1]
        previous = indicator.iloc[-2] if len(indicator) > 1 else latest

        # 分析各项指标
        analysis = {
            'symbol': symbol,
            'report_date': latest.get('REPORT_DATE', 'N/A'),
            '盈利能力': {
                '毛利率': latest.get('XSMLL', 'N/A'),
                '净利率': latest.get('XSJLL', 'N/A'),
                'ROE': latest.get('ROEJQ', 'N/A'),
                '每股收益': latest.get('EPSJB', 'N/A'),
            },
            '成长性': {
                '营收增长率': latest.get('YYSZRTB', 'N/A'),
                '利润增长率': latest.get('LRRTB', 'N/A'),
            },
            '财务结构': {
                '资产负债率': latest.get('ZCFZL', 'N/A'),
            },
            '运营效率': {
                '应收账款周转率': latest.get('YSTZKZZL', 'N/A'),
                '存货周转率': latest.get('CHZZL', 'N/A'),
            }
        }

        return analysis

    except Exception as e:
        print(f"获取 {symbol} 财务数据失败: {e}")
        return None


def display_financial_report(symbol):
    """展示财务分析报告"""
    analysis = analyze_stock_financial(symbol)

    if analysis is None:
        print(f"无法获取 {symbol} 的财务数据")
        return

    print(f"\n{'='*60}")
    print(f"  {symbol} 财务分析报告")
    print(f"  报告期: {analysis['report_date']}")
    print(f"{'='*60}")

    for category, items in analysis.items():
        if category in ['symbol', 'report_date']:
            continue

        print(f"\n【{category}】")
        for key, value in items.items():
            if value != 'N/A':
                try:
                    print(f"  {key}: {float(value):.2f}")
                except:
                    print(f"  {key}: {value}")
            else:
                print(f"  {key}: N/A")


if __name__ == "__main__":
    print(f"=== A股基本面分析 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")

    # 示例：分析平安银行
    display_financial_report("000001")

    print("\n" + "="*60 + "\n")

    # 市场估值
    print("【市场估值概览】")
    market_pe, market_pb = get_market_pe_pb()
    print(f"市场 TTM 市盈率: {market_pe.tail(1)['市盈率'].values[0]:.2f}")
    print(f"市场 市净率: {market_pb.tail(1)['市净率'].values[0]:.2f}")