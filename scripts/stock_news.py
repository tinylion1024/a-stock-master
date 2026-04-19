#!/usr/bin/env python3
"""
A股消息面分析
分析个股新闻、公告、龙虎榜原因等
"""

import argparse
import akshare as ak
import pandas as pd
from datetime import datetime, timedelta


def get_stock_news(symbol):
    """获取个股新闻"""
    return ak.stock_news_em(symbol=symbol)


def get_lhb_details(start_date, end_date):
    """获取龙虎榜详情"""
    return ak.stock_lhb_detail_em(start_date=start_date, end_date=end_date)


def get_lhb_stock_statistics():
    """获取个股上榜统计"""
    return ak.stock_lhb_stock_statistic_em()


def get_yjbb_report(date):
    """获取业绩报表"""
    return ak.stock_yjbb_em(date=date)


def get_stock_individual_info(symbol):
    """获取个股基本信息"""
    return ak.stock_individual_info_em(symbol=symbol)


def find_lhb_stocks(start_date=None, end_date=None, top_n=20):
    """寻找龙虎榜股票"""
    if end_date is None:
        end_date = datetime.now().strftime('%Y%m%d')
    if start_date is None:
        start_date = (datetime.now() - timedelta(days=7)).strftime('%Y%m%d')

    df = get_lhb_details(start_date, end_date)
    if df is None or len(df) == 0:
        return None

    if '上榜原因' in df.columns and '龙虎榜净买额' in df.columns:
        df = df.sort_values('龙虎榜净买额', ascending=False).head(top_n)

    return df


def analyze_lhb_reason(code):
    """分析个股龙虎榜原因"""
    end_date = datetime.now().strftime('%Y%m%d')
    start_date = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')

    df = get_lhb_details(start_date, end_date)
    if df is None or len(df) == 0:
        return None

    stock_df = df[df['代码'] == code]
    return stock_df


def screen_by_lhb_frequency(top_n=20):
    """筛选近期频繁上榜的股票"""
    df = get_lhb_stock_statistics()
    if df is None or len(df) == 0:
        return None

    if '上榜次数' in df.columns:
        result = df.sort_values('上榜次数', ascending=False).head(top_n)
    else:
        result = df.head(top_n)

    return result


def sentiment_keywords(news_df):
    """基于关键词判断消息情绪"""
    if news_df is None or len(news_df) == 0:
        return None

    positive_keywords = ['增长', '盈利', '突破', '创新', '合作', '利好', '获批', '签约']
    negative_keywords = ['亏损', '下跌', '风险', '警示', '处罚', '违规', '减持', '诉讼']
    neutral_keywords = ['公告', '会议', '报告', '审议']

    sentiment = {'positive': 0, 'negative': 0, 'neutral': 0}

    if '新闻标题' in news_df.columns:
        for title in news_df['新闻标题']:
            for kw in positive_keywords:
                if kw in str(title):
                    sentiment['positive'] += 1
            for kw in negative_keywords:
                if kw in str(title):
                    sentiment['negative'] += 1
            for kw in neutral_keywords:
                if kw in str(title):
                    sentiment['neutral'] += 1

    return sentiment


def main():
    parser = argparse.ArgumentParser(
        description='A股消息面分析',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python stock_news.py                               # 显示市场要闻
  python stock_news.py 000001                        # 显示个股消息
  python stock_news.py 000001 --news                 # 仅显示新闻
  python stock_news.py --lhb                         # 显示龙虎榜
  python stock_news.py --lhb-freq                    # 龙虎榜频繁上榜股票
  python stock_news.py --days 7                      # 最近7天
  python stock_news.py --output json                 # JSON输出
        """
    )
    parser.add_argument('symbol', nargs='?', help='股票代码')
    parser.add_argument('--news', action='store_true', help='仅显示新闻')
    parser.add_argument('--lhb', action='store_true', help='显示龙虎榜')
    parser.add_argument('--lhb-freq', action='store_true', help='龙虎榜频繁上榜股票')
    parser.add_argument('--days', type=int, default=7, help='统计天数 (默认: 7)')
    parser.add_argument('--top', type=int, default=20, help='显示数量 (默认: 20)')
    parser.add_argument('--output', choices=['csv', 'json'], help='输出格式')
    args = parser.parse_args()

    print(f"=== A股消息面分析 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")

    if args.symbol:
        # 个股分析
        symbol = args.symbol

        if args.news:
            print(f"【{symbol} 近期新闻】")
            news = get_stock_news(symbol)
            if news is not None and len(news) > 0:
                display_cols = ['发布时间', '新闻标题']
                available = [c for c in display_cols if c in news.columns]
                if args.output == 'csv':
                    print(news[available].head(args.top).to_csv(index=False))
                elif args.output == 'json':
                    print(news[available].head(args.top).to_json(orient='records', force_ascii=False, indent=2))
                else:
                    print(news[available].head(10).to_string(index=False))
            else:
                print("暂无新闻数据")
            return

        # 显示完整消息分析
        print(f"【{symbol} 消息面分析】")

        # 新闻
        print("\n【近期新闻】")
        news = get_stock_news(symbol)
        if news is not None and len(news) > 0:
            display_cols = ['发布时间', '新闻标题']
            available = [c for c in display_cols if c in news.columns]
            print(news[available].head(10).to_string(index=False))

            # 情绪分析
            sentiment = sentiment_keywords(news)
            if sentiment:
                print(f"\n情绪分析: 正面{sentiment['positive']} 负面{sentiment['negative']} 中性{sentiment['neutral']}")
        else:
            print("暂无新闻数据")

        # 龙虎榜
        print("\n【龙虎榜记录】")
        lhb_record = analyze_lhb_reason(symbol)
        if lhb_record is not None and len(lhb_record) > 0:
            print(f"近30天共上榜 {len(lhb_record)} 次")
            cols = ['上榜日', '上榜原因', '龙虎榜净买额']
            available = [c for c in cols if c in lhb_record.columns]
            print(lhb_record[available].head(5).to_string(index=False))
        else:
            print("近30天无龙虎榜记录")

        # 公司信息
        print("\n【公司信息】")
        info = get_stock_individual_info(symbol)
        if info is not None:
            for _, row in info.iterrows():
                if row.get('item') in ['所属行业', '股票简称', '总股本', '流通股本']:
                    print(f"  {row.get('item', 'N/A')}: {row.get('value', 'N/A')}")
        return

    # 市场要闻
    start_date = (datetime.now() - timedelta(days=args.days)).strftime('%Y%m%d')
    end_date = datetime.now().strftime('%Y%m%d')

    if args.lhb:
        print(f"【近期龙虎榜 (近{args.days}天)】")
        df = find_lhb_stocks(start_date, end_date, args.top)
        if df is not None and len(df) > 0:
            cols = ['代码', '名称', '上榜日', '龙虎榜净买额', '上榜原因']
            available = [c for c in cols if c in df.columns]
            if args.output == 'csv':
                print(df[available].to_csv(index=False))
            elif args.output == 'json':
                print(df[available].to_json(orient='records', force_ascii=False, indent=2))
            else:
                print(df[available].to_string(index=False))
        else:
            print("暂无龙虎榜数据")
        return

    if args.lhb_freq:
        print("【龙虎榜频繁上榜股票】")
        df = screen_by_lhb_frequency(args.top)
        if df is not None:
            cols = ['代码', '名称', '上榜次数', '龙虎榜净买额']
            available = [c for c in cols if c in df.columns]
            if args.output == 'csv':
                print(df[available].to_csv(index=False))
            elif args.output == 'json':
                print(df[available].to_json(orient='records', force_ascii=False, indent=2))
            else:
                print(df[available].to_string(index=False))
        return

    # 默认显示市场要闻
    print("【近期龙虎榜】")
    df = find_lhb_stocks(start_date, end_date, 15)
    if df is not None and len(df) > 0:
        cols = ['代码', '名称', '上榜日', '龙虎榜净买额', '上榜原因']
        available = [c for c in cols if c in df.columns]
        print(df[available].to_string(index=False))

    print("\n【龙虎榜频繁上榜股票】")
    lhb_stocks = screen_by_lhb_frequency(15)
    if lhb_stocks is not None:
        cols = ['代码', '名称', '上榜次数', '龙虎榜净买额']
        available = [c for c in cols if c in lhb_stocks.columns]
        print(lhb_stocks[available].to_string(index=False))


if __name__ == "__main__":
    main()
