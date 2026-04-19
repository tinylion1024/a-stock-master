#!/usr/bin/env python3
"""
A股交易模式选择器
分析市场行情、情绪、消息，决定交易模式
"""

import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
from enum import Enum


class TradeMode(Enum):
    """交易模式枚举"""
    SENTIMENT = "情绪模式"      # 短线情绪驱动
    QUANTITATIVE = "量化模式"   # 系统化量化选股
    INSTITUTIONAL = "机构模式"  # 中长线机构跟随


# ------------------------------------------------------------------
# 市场行情分析
# ------------------------------------------------------------------
def analyze_market_quotes():
    """
    分析市场整体行情

    返回:
        market_status: {
            'index_status': '上升/下降/震荡',
            'volume_ratio': 成交量对比,
            'up_count': 上涨家数,
            'down_count': 下跌家数,
            'limit_up_count': 涨停家数,
            'limit_down_count': 跌停家数
        }
    """
    print("\n" + "="*60)
    print("  📊 市场行情分析")
    print("="*60 + "\n")

    try:
        # 获取全市场行情
        df = ak.stock_zh_a_spot_em()

        # 统计涨跌家数
        up_count = len(df[df['涨跌幅'] > 0])
        down_count = len(df[df['涨跌幅'] < 0])
        flat_count = len(df[df['涨跌幅'] == 0])

        # 涨停跌停
        limit_up = len(df[df['涨跌幅'] >= 9.5])
        limit_down = len(df[df['涨跌幅'] <= -9.5])

        # 计算平均涨跌
        avg_change = df['涨跌幅'].mean()

        # 成交额统计
        total_volume = df['成交额'].sum()
        avg_volume = df['成交量'].mean()

        print(f"上涨家数：{up_count} ({up_count/len(df)*100:.1f}%)")
        print(f"下跌家数：{down_count} ({down_count/len(df)*100:.1f}%)")
        print(f"平盘家数：{flat_count} ({flat_count/len(df)*100:.1f}%)")
        print(f"涨停家数：{limit_up}")
        print(f"跌停家数：{limit_down}")
        print(f"平均涨跌：{avg_change:.2f}%")
        print(f"总成交额：{total_volume/1e8:.2f}亿")

        return {
            'index_status': '上升' if avg_change > 1 else ('下降' if avg_change < -1 else '震荡'),
            'volume_ratio': 1.0,  # 需要历史对比
            'up_count': up_count,
            'down_count': down_count,
            'limit_up_count': limit_up,
            'limit_down_count': limit_down,
            'avg_change': avg_change
        }
    except Exception as e:
        print(f"行情分析失败: {e}")
        return None


# ------------------------------------------------------------------
# 情绪面分析
# ------------------------------------------------------------------
def analyze_sentiment():
    """
    分析市场情绪

    返回:
        sentiment_status: {
            'level': '高涨/活跃/中性/低迷',
            'risk_level': '高/中/低',
            'signals': []
        }
    """
    print("\n" + "="*60)
    print("  😊 市场情绪分析")
    print("="*60 + "\n")

    try:
        # 涨停家数（市场情绪指标）
        df = ak.stock_zh_a_spot_em()
        limit_up = len(df[df['涨跌幅'] >= 9.5])
        limit_down = len(df[df['涨跌幅'] <= -9.5])

        # 炸板率（需要历史数据，这里简化）
        # 实际应该用昨日涨停股今日表现

        # 情绪判断
        if limit_up >= 80:
            level = "极度高涨"
            risk = "高"
            signal = "市场情绪极度亢奋，警惕盛极而衰"
        elif limit_up >= 50:
            level = "高涨"
            risk = "中"
            signal = "短线情绪活跃，适合情绪模式"
        elif limit_up >= 30:
            level = "活跃"
            risk = "中"
            signal = "情绪一般，稳健操作"
        elif limit_up >= 10:
            level = "中性"
            risk = "低"
            signal = "情绪低迷，不宜追高"
        else:
            level = "极度低迷"
            risk = "高"
            signal = "市场冰点，等待反弹机会"

        # 跌停家数辅助判断
        if limit_down > 30:
            risk = "极高"
            signal = "恐慌情绪蔓延，建议空仓"
        elif limit_down > 20:
            risk = "高"
            signal = "亏钱效应明显，轻仓或空仓"

        print(f"涨停家数：{limit_up}")
        print(f"跌停家数：{limit_down}")
        print(f"情绪等级：{level}")
        print(f"风险等级：{risk}")
        print(f"信号：{signal}")

        return {
            'level': level,
            'risk_level': risk,
            'limit_up_count': limit_up,
            'limit_down_count': limit_down,
            'signals': [signal]
        }

    except Exception as e:
        print(f"情绪分析失败: {e}")
        return None


# ------------------------------------------------------------------
# 消息面分析
# ------------------------------------------------------------------
def analyze_news_sentiment():
    """
    分析消息面对市场的影响

    返回:
        news_status: {
            'overall': '利好/中性/利空',
            'topics': ['热点话题']
        }
    """
    print("\n" + "="*60)
    print("  📰 消息面分析")
    print("="*60 + "\n")

    # 简化实现：实际应接入实时新闻数据
    print("注：消息面分析需要接入实时新闻源")
    print("当前提供基础版本\n")

    # 北向资金（作为消息面参考）
    try:
        hsgt = ak.stock_hsgt_fund_flow_summary_em()
        if hsgt is not None and len(hsgt) > 0:
            print(f"北向资金：{hsgt.iloc[-1].get('名称', 'N/A')}")
    except:
        print("北向资金：暂无数据")

    return {
        'overall': '中性',
        'topics': ['等待消息面数据接入']
    }


# ------------------------------------------------------------------
# 模式推荐
# ------------------------------------------------------------------
def recommend_mode(market, sentiment, news):
    """
    根据市场分析推荐交易模式

    返回:
        recommendations: [(模式, 置信度, 仓位建议), ...]
    """
    print("\n" + "="*60)
    print("  🎯 模式推荐")
    print("="*60 + "\n")

    recommendations = []

    # 情绪模式条件
    if sentiment and sentiment['limit_up_count'] >= 30:
        conf = min(sentiment['limit_up_count'] / 100, 0.95)
        recommendations.append((TradeMode.SENTIMENT, conf, "30%"))

    # 量化模式条件（市场震荡）
    if market and market['index_status'] == '震荡':
        conf = 0.7
        recommendations.append((TradeMode.QUANTITATIVE, conf, "40%"))

    # 机构模式条件（上升趋势 + 资金流入）
    if market and market['index_status'] == '上升':
        conf = 0.75
        recommendations.append((TradeMode.INSTITUTIONAL, conf, "50%"))

    # 默认推荐（根据风险等级）
    if not recommendations:
        if sentiment and sentiment['risk_level'] == '低':
            recommendations.append((TradeMode.QUANTITATIVE, 0.6, "30%"))
        else:
            recommendations.append((TradeMode.INSTITUTIONAL, 0.5, "20%"))

    # 按置信度排序
    recommendations.sort(key=lambda x: x[1], reverse=True)

    print("推荐交易模式：\n")
    for mode, conf, position in recommendations:
        emoji = "🚀" if mode == TradeMode.SENTIMENT else "📊" if mode == TradeMode.QUANTITATIVE else "🏛️"
        print(f"  {emoji} {mode.value}: 置信度 {conf*100:.0f}%, 建议仓位 {position}")

    return recommendations


def get_mode_description(mode: TradeMode) -> str:
    """获取模式说明"""
    descriptions = {
        TradeMode.SENTIMENT: """
情绪模式：短线情绪驱动，抓龙头连板机会。
- 适用：情绪高涨，涨停>50家
- 特点：高风险高收益，严格止损
- 仓位：轻仓试错，10-20%
        """,
        TradeMode.QUANTITATIVE: """
量化模式：系统化多因子选股，震荡市利器。
- 适用：市场震荡，无明显趋势
- 特点：纪律性强，回撤可控
- 仓位：稳健布局，30-40%
        """,
        TradeMode.INSTITUTIONAL: """
机构模式：跟随主力资金，中长线布局。
- 适用：上升趋势，机构主导
- 特点：稳定收益，控制回撤
- 仓位：重仓持有，50-60%
        """
    }
    return descriptions.get(mode, "")


# ------------------------------------------------------------------
# 主程序
# ------------------------------------------------------------------
def run_market_analysis():
    """执行完整的市场分析"""
    print("\n" + "="*70)
    print(f"  A股市场分析报告 - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("="*70)

    # 1. 行情分析
    market = analyze_market_quotes()

    # 2. 情绪分析
    sentiment = analyze_sentiment()

    # 3. 消息面
    news = analyze_news_sentiment()

    # 4. 模式推荐
    recommendations = recommend_mode(market, sentiment, news)

    # 输出各模式详情
    print("\n" + "="*70)
    print("  📋 模式详情")
    print("="*70)

    for mode, conf, position in recommendations:
        print(get_mode_description(mode))

    return {
        'market': market,
        'sentiment': sentiment,
        'news': news,
        'recommendations': recommendations
    }


def select_mode(mode_name: str = None):
    """
    选择特定模式

    mode_name: '情绪' / '量化' / '机构'
    """
    if mode_name is None:
        # 自动选择
        result = run_market_analysis()
        return result

    # 手动选择
    mode_map = {
        '情绪': TradeMode.SENTIMENT,
        '量化': TradeMode.QUANTITATIVE,
        '机构': TradeMode.INSTITUTIONAL
    }

    mode = mode_map.get(mode_name)
    if mode:
        print(f"\n已选择模式：{mode.value}")
        print(get_mode_description(mode))

    return mode


if __name__ == "__main__":
    import sys

    mode_arg = sys.argv[1] if len(sys.argv) > 1 else None
    select_mode(mode_arg)