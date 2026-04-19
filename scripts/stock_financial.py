#!/usr/bin/env python3
"""
A股基本面分析
分析个股财务指标、估值、业绩等
"""

import argparse
import akshare as ak
import pandas as pd
from datetime import datetime


def get_stock_info(symbol):
    """获取个股基本信息"""
    return ak.stock_individual_info_em(symbol=symbol)


def get_financial_indicator(symbol, period="按报告期"):
    """获取财务分析指标"""
    return ak.stock_financial_analysis_indicator_em(
        symbol=symbol,
        indicator=period
    )


def get_balance_sheet(date="20240331"):
    """获取资产负债表"""
    return ak.stock_zcfz_em(date=date)


def get_income_statement(date="20240331"):
    """获取利润表"""
    return ak.stock_lrb_em(date=date)


def get_market_pe_pb():
    """获取市场整体市盈率和市净率"""
    pe_df = ak.stock_a_ttm_lyr()
    pb_df = ak.stock_a_all_pb()
    return pe_df, pb_df


def analyze_stock_financial(symbol):
    """综合财务分析"""
    try:
        indicator = get_financial_indicator(symbol, period="按报告期")
        if indicator is None or len(indicator) == 0:
            return None

        latest = indicator.iloc[-1]
        previous = indicator.iloc[-2] if len(indicator) > 1 else latest

        analysis = {
            'symbol': symbol,
            'report_date': str(latest.get('REPORT_DATE', 'N/A')),
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


def display_financial_report(symbol, output_format=None):
    """展示财务分析报告"""
    analysis = analyze_stock_financial(symbol)

    if analysis is None:
        print(f"无法获取 {symbol} 的财务数据")
        return

    if output_format == 'json':
        import json
        # 转换所有值为可JSON序列化
        data = {
            'symbol': analysis['symbol'],
            'report_date': analysis['report_date'],
        }
        for category, items in analysis.items():
            if category in ['symbol', 'report_date']:
                continue
            data[category] = {}
            for key, value in items.items():
                if value != 'N/A':
                    try:
                        data[category][key] = float(value)
                    except:
                        data[category][key] = str(value)
                else:
                    data[category][key] = None
        print(json.dumps(data, ensure_ascii=False, indent=2))
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


def main():
    parser = argparse.ArgumentParser(
        description='A股基本面分析',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python stock_financial.py 000001                    # 分析平安银行
  python stock_financial.py 000001 --json          # JSON格式输出
  python stock_financial.py 000001 --period 季度     # 按单季度
  python stock_financial.py --market-pe            # 显示市场整体估值
        """
    )
    parser.add_argument('symbol', nargs='?', help='股票代码')
    parser.add_argument('--json', action='store_true', help='JSON格式输出')
    parser.add_argument('--period', choices=['报告期', '季度'], default='报告期',
                        help='财务周期 (默认: 报告期)')
    parser.add_argument('--market-pe', action='store_true', help='显示市场整体估值')
    parser.add_argument('--balance-sheet', help='显示资产负债表 (日期 YYYYMM格式)')
    parser.add_argument('--income', help='显示利润表 (日期 YYYYMM格式)')
    args = parser.parse_args()

    print(f"=== A股基本面分析 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")

    if args.market_pe:
        print("【市场估值概览】")
        market_pe, market_pb = get_market_pe_pb()
        if market_pe is not None and len(market_pe) > 0:
            pe_val = market_pe.tail(1)['市盈率'].values[0]
            print(f"市场 TTM 市盈率: {pe_val:.2f}")
        if market_pb is not None and len(market_pb) > 0:
            pb_val = market_pb.tail(1)['市净率'].values[0]
            print(f"市场 市净率: {pb_val:.2f}")
        return

    if args.balance_sheet:
        print(f"【资产负债表 {args.balance_sheet}】")
        df = get_balance_sheet(args.balance_sheet)
        if df is not None:
            display_cols = ['股票代码', '股票简称', '资产-总资产', '负债-总负债', '资产负债率']
            available = [c for c in display_cols if c in df.columns]
            print(df[available].head(20).to_string(index=False))
        return

    if args.income:
        print(f"【利润表 {args.income}】")
        df = get_income_statement(args.income)
        if df is not None:
            display_cols = ['股票代码', '股票简称', '营业总收入', '归属净利润', '基本每股收益']
            available = [c for c in display_cols if c in df.columns]
            print(df[available].head(20).to_string(index=False))
        return

    if args.symbol:
        period = "按单季度" if args.period == '季度' else "按报告期"
        print(f"【{args.symbol} 财务分析 (周期: {period})】")
        display_financial_report(args.symbol, 'json' if args.json else None)
        return

    # 默认显示市场估值
    print("【市场估值概览】")
    market_pe, market_pb = get_market_pe_pb()
    if market_pe is not None and len(market_pe) > 0:
        pe_val = market_pe.tail(1)['市盈率'].values[0]
        print(f"市场 TTM 市盈率: {pe_val:.2f}")
    if market_pb is not None and len(market_pb) > 0:
        pb_val = market_pb.tail(1)['市净率'].values[0]
        print(f"市场 市净率: {pb_val:.2f}")


if __name__ == "__main__":
    main()
