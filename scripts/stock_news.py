#!/usr/bin/env python3
"""
A股消息面分析
分析个股新闻、公告、龙虎榜原因等
"""

import akshare as ak
import pandas as pd
from datetime import datetime, timedelta


def get_stock_news(symbol):
    """
    获取个股新闻

    参数:
        symbol: 股票代码，如 "000001"
    """
    df = ak.stock_news_em(symbol=symbol)
    return df


def get_lhb_details(start_date, end_date):
    """
    获取龙虎榜详情

    参数:
        start_date: 开始日期，格式 YYYYMMDD
        end_date: 结束日期，格式 YYYYMMDD
    """
    df = ak.stock_lhb_detail_em(start_date=start_date, end_date=end_date)
    return df


def get_lhb_stock_statistics():
    """获取个股上榜统计"""
    df = ak.stock_lhb_stock_statistic_em()
    return df


def get_yjbb_report(date):
    """
    获取业绩报表

    参数:
        date: 报告期，格式 YYYYMMDD
    """
    df = ak.stock_yjbb_em(date=date)
    return df


def get_ipo_info():
    """获取IPO信息"""
    df = ak.stock_ipo_info_cninfo()
    return df


def get_stock_individual_info(symbol):
    """获取个股基本信息（包含所属行业等）"""
    df = ak.stock_individual_info_em(symbol=symbol)
    return df


def analyze_news_sentiment(symbol, days=7):
    """
    分析个股消息面情绪

    返回:
        news_list: 新闻列表
        sentiment: 情绪判断（正面/负面/中性）
    """
    # 获取新闻
    news = get_stock_news(symbol)

    if news is None or len(news) == 0:
        return None, "无数据"

    # 过滤近7天新闻
    cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    news_recent = news[news['发布时间'] >= cutoff_date] if '发布时间' in news.columns else news

    return news_recent, "分析中"


def find_lhb_stocks(start_date=None, end_date=None, top_n=20):
    """
    寻找龙虎榜股票

    参数:
        start_date: 开始日期，默认7天前
        end_date: 结束日期，默认今天
        top_n: 返回数量
    """
    if end_date is None:
        end_date = datetime.now().strftime('%Y%m%d')
    if start_date is None:
        start_date = (datetime.now() - timedelta(days=7)).strftime('%Y%m%d')

    df = get_lhb_details(start_date, end_date)

    if df is None or len(df) == 0:
        return None

    # 按上榜原因分类
    if '上榜原因' in df.columns:
        # 取净买入额最大的
        if '龙虎榜净买额' in df.columns:
            df = df.sort_values('龙虎榜净买额', ascending=False).head(top_n)

    return df


def analyze_lhb_reason(code):
    """
    分析个股龙虎榜原因

    返回近一个月龙虎榜记录及原因
    """
    end_date = datetime.now().strftime('%Y%m%d')
    start_date = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')

    df = get_lhb_details(start_date, end_date)

    if df is None or len(df) == 0:
        return None

    # 筛选该股票
    stock_df = df[df['代码'] == code]

    return stock_df


def screen_by_lhb_frequency(top_n=20):
    """
    筛选近期频繁上榜的股票

    参数:
        top_n: 返回数量
    """
    df = get_lhb_stock_statistics()

    if df is None or len(df) == 0:
        return None

    # 按上榜次数排序
    if '上榜次数' in df.columns:
        result = df.sort_values('上榜次数', ascending=False).head(top_n)
    else:
        result = df.head(top_n)

    return result


def get_market_news(days=3):
    """
    获取市场要闻

    参数:
        days: 最近几天
    """
    # 龙虎榜市场统计
    try:
        lhb = get_lhb_details(
            (datetime.now() - timedelta(days=days)).strftime('%Y%m%d'),
            datetime.now().strftime('%Y%m%d')
        )
    except:
        lhb = None

    # 业绩报表
    try:
        # 取最近一个季度
        current_date = datetime.now()
        if current_date.month <= 3:
            report_date = f"{current_date.year - 1}1231"
        else:
            month = ((current_date.month - 1) // 3) * 3
            report_date = f"{current_date.year}{month:02d}31"

        yjbb = get_yjbb_report(report_date)
    except:
        yjbb = None

    # IPO信息
    try:
        ipo = get_ipo_info()
    except:
        ipo = None

    return {
        'lhb': lhb,
        'yjbb': yjbb,
        'ipo': ipo
    }


def display_news_report(symbol):
    """展示个股消息分析报告"""
    print(f"\n{'='*70}")
    print(f"  {symbol} 消息面分析")
    print(f"{'='*70}\n")

    # 个股新闻
    print("【近期新闻】")
    news = get_stock_news(symbol)
    if news is not None and len(news) > 0:
        # 显示最新10条
        display_cols = ['发布时间', '新闻标题']
        available = [c for c in display_cols if c in news.columns]
        if available:
            print(news[available].head(10).to_string(index=False))
    else:
        print("  暂无新闻数据")

    print()

    # 龙虎榜
    print("【龙虎榜记录】")
    lhb_record = analyze_lhb_reason(symbol)
    if lhb_record is not None and len(lhb_record) > 0:
        print(f"  近30天共上榜 {len(lhb_record)} 次")
        if '上榜日' in lhb_record.columns and '上榜原因' in lhb_record.columns:
            print(lhb_record[['上榜日', '上榜原因']].head(5).to_string(index=False))
    else:
        print("  近30天无龙虎榜记录")

    print()

    # 基本信息（所属行业）
    print("【公司信息】")
    info = get_stock_individual_info(symbol)
    if info is not None:
        for _, row in info.iterrows():
            if row.get('item') in ['所属行业', '股票简称', '总股本', '流通股本']:
                print(f"  {row.get('item', 'N/A')}: {row.get('value', 'N/A')}")

    print(f"\n{'='*70}\n")


def display_market_news():
    """展示市场要闻"""
    print(f"\n{'='*70}")
    print(f"  市场消息面汇总")
    print(f"{'='*70}\n")

    data = get_market_news(days=3)

    # 龙虎榜
    if data['lhb'] is not None and len(data['lhb']) > 0:
        print("【近期龙虎榜】")
        cols = ['代码', '名称', '上榜日', '龙虎榜净买额', '上榜原因']
        available = [c for c in cols if c in data['lhb'].columns]
        print(data['lhb'][available].head(15).to_string(index=False))
        print()
    else:
        print("【近期龙虎榜】暂无数据\n")

    # 业绩报表
    if data['yjbb'] is not None and len(data['yjbb']) > 0:
        print("【业绩报表 TOP 20（按净利润）】")
        cols = ['股票代码', '股票简称', '基本每股收益', '归属净利润', '营业总收入']
        available = [c for c in cols if c in data['yjbb'].columns]
        print(data['yjbb'][available].head(20).to_string(index=False))
        print()
    else:
        print("【业绩报表】暂无数据\n")

    # IPO
    if data['ipo'] is not None and len(data['ipo']) > 0:
        print("【近期IPO】")
        cols = ['股票代码', '股票简称', '发行价格', '上市日期']
        available = [c for c in cols if c in data['ipo'].columns]
        print(data['ipo'][available].head(10).to_string(index=False))
        print()
    else:
        print("【近期IPO】暂无数据\n")

    print(f"{'='*70}\n")


def sentiment_keywords(news_df):
    """
    基于关键词判断消息情绪

    返回:
        positive: 正面词出现次数
        negative: 负面词出现次数
        neutral: 中性词出现次数
    """
    if news_df is None or len(news_df) == 0:
        return None

    positive_keywords = ['增长', '盈利', '突破', '创新', '合作', '利好', '获批', '签约']
    negative_keywords = ['亏损', '下跌', '风险', '警示', '处罚', '违规', '减持', '诉讼']
    neutral_keywords = ['公告', '会议', '报告', '审议']

    sentiment = {'positive': 0, 'negative': 0, 'neutral': 0}

    # 统计标题中的关键词
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


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        symbol = sys.argv[1]
        display_news_report(symbol)
    else:
        # 显示市场要闻
        display_market_news()

        print("\n" + "="*70 + "\n")

        # 显示近期龙虎榜频繁股票
        print("【龙虎榜频繁上榜股票 TOP 15】")
        lhb_stocks = screen_by_lhb_frequency(15)
        if lhb_stocks is not None:
            cols = ['代码', '名称', '上榜次数', '龙虎榜净买额']
            available = [c for c in cols if c in lhb_stocks.columns]
            print(lhb_stocks[available].to_string(index=False))