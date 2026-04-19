#!/usr/bin/env python3
"""
A股交易模式选择器
分析市场行情、情绪、消息，决定交易模式
支持数据准备 Tag 机制和记忆系统
"""

import os
import json
import time
import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
from enum import Enum


class DateEncoder(json.JSONEncoder):
    """处理 date/datetime 类型的 JSON encoder"""
    def default(self, obj):
        if isinstance(obj, (datetime, pd.Timestamp)):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        if isinstance(obj, (pd.Timedelta, timedelta)):
            return str(obj)
        return super().default(obj)


class TradeMode(Enum):
    """交易模式枚举"""
    SENTIMENT = "情绪模式"      # 短线情绪驱动
    QUANTITATIVE = "量化模式"   # 系统化量化选股
    INSTITUTIONAL = "机构模式"  # 中长线机构跟随


# ------------------------------------------------------------------
# 数据准备状态检查
# ------------------------------------------------------------------
def check_data_ready():
    """
    检查数据准备状态

    返回:
        'ready': 数据已就绪（存在 DATA_SUCCESS Tag）
        'degraded': 降级数据（存在 DATA_DEGRADED Tag）
        'need_prepare': 需要准备数据
    """
    date_str = datetime.now().strftime('%Y%m%d')
    workspace = f"a-stock-{date_str}"

    # 检查目录是否存在
    if not os.path.exists(workspace):
        return 'need_prepare'

    # 检查 Tag 文件
    if os.path.exists(f"{workspace}/DATA_SUCCESS"):
        return 'ready'

    if os.path.exists(f"{workspace}/DATA_DEGRADED"):
        return 'degraded'

    return 'need_prepare'


def create_degraded_tag(workspace, error_msg):
    """创建降级 Tag 文件"""
    degraded_file = f"{workspace}/DATA_DEGRADED"
    content = f"""# 数据准备降级报告 - {datetime.now().strftime('%Y%m%d')}

## 状态：DATA_DEGRADED

## 失败原因
{error_msg}

## 生成时间
{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 后续处理
1. 明确告知用户数据缺失情况
2. 在分析和结论中标注"数据来源：[降级]"
3. 增加风险提示
"""
    with open(degraded_file, 'w', encoding='utf-8') as f:
        f.write(content)


# ------------------------------------------------------------------
# 数据获取函数
# ------------------------------------------------------------------
def fetch_market_data(date_str):
    """获取市场行情数据"""
    print("  📊 获取市场行情数据...")
    try:
        # 全市场实时行情
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

        # 保存到 CSV
        csv_file = f"a-stock-{date_str}/data/market_{date_str}.csv"
        df.to_csv(csv_file, index=False, encoding='utf-8')

        return {
            'up_count': up_count,
            'down_count': down_count,
            'flat_count': flat_count,
            'limit_up': limit_up,
            'limit_down': limit_down,
            'avg_change': avg_change,
            'total_volume': total_volume,
            'total_stocks': len(df)
        }
    except Exception as e:
        print(f"  ❌ 行情数据获取失败: {e}")
        raise


def fetch_sentiment_data(date_str):
    """获取情绪数据"""
    print("  😊 获取情绪数据...")
    try:
        # 全市场实时行情
        df = ak.stock_zh_a_spot_em()

        limit_up = len(df[df['涨跌幅'] >= 9.5])
        limit_down = len(df[df['涨跌幅'] <= -9.5])

        sentiment = {
            'limit_up': limit_up,
            'limit_down': limit_down,
            'limit_up_level': '极度亢奋' if limit_up >= 80 else ('高涨' if limit_up >= 50 else ('一般' if limit_up >= 30 else '低迷')),
            'limit_down_level': '极度恐慌' if limit_down > 40 else ('恐慌' if limit_down > 20 else ('谨慎' if limit_down > 10 else '安全'))
        }

        # 保存到 JSON
        json_file = f"a-stock-{date_str}/data/sentiment_{date_str}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(sentiment, f, ensure_ascii=False, indent=2, cls=DateEncoder)

        return sentiment
    except Exception as e:
        print(f"  ❌ 情绪数据获取失败: {e}")
        raise


def fetch_fund_data(date_str):
    """获取资金流向数据"""
    print("  💰 获取资金流向数据...")
    try:
        fund_data = {}

        # 北向资金
        try:
            hsgt = ak.stock_hsgt_fund_flow_summary_em()
            if hsgt is not None and len(hsgt) > 0:
                fund_data['hsgt'] = hsgt.to_dict()
        except Exception as e:
            print(f"    ⚠️ 北向资金获取失败: {e}")
            fund_data['hsgt'] = None

        # 主力资金
        try:
            main_fund = ak.stock_main_fund_flow()
            if main_fund is not None:
                fund_data['main_fund'] = main_fund.to_dict()
        except Exception as e:
            print(f"    ⚠️ 主力资金获取失败: {e}")
            fund_data['main_fund'] = None

        # 板块资金流
        try:
            sector = ak.stock_board_industry_spot_em()
            if sector is not None:
                fund_data['sector'] = sector.to_dict()
        except Exception as e:
            print(f"    ⚠️ 板块资金获取失败: {e}")
            fund_data['sector'] = None

        # 保存到 JSON
        json_file = f"a-stock-{date_str}/data/fund_flow_{date_str}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(fund_data, f, ensure_ascii=False, indent=2, cls=DateEncoder)

        return fund_data
    except Exception as e:
        print(f"  ❌ 资金数据获取失败: {e}")
        raise


def fetch_sector_data(date_str):
    """获取板块排行数据"""
    print("  📈 获取板块排行数据...")
    try:
        # 概念板块
        concept = ak.stock_board_concept_spot_em()

        # 行业板块
        industry = ak.stock_board_industry_spot_em()

        sector_data = {
            'concept': concept.to_dict() if concept is not None else None,
            'industry': industry.to_dict() if industry is not None else None
        }

        # 保存到 JSON
        json_file = f"a-stock-{date_str}/data/sector_rank_{date_str}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(sector_data, f, ensure_ascii=False, indent=2, cls=DateEncoder)

        return sector_data
    except Exception as e:
        print(f"  ❌ 板块数据获取失败: {e}")
        raise


def fetch_news_data(date_str):
    """获取新闻数据（简化版）"""
    print("  📰 获取新闻数据...")
    try:
        # 获取龙虎榜数据作为新闻线索
        lhb = ak.stock_lhb_detail_em(
            start_date=(datetime.now() - timedelta(days=7)).strftime('%Y%m%d'),
            end_date=datetime.now().strftime('%Y%m%d')
        )

        news_data = {
            'lhb': lhb.to_dict() if lhb is not None else None,
            'fetch_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'note': '新闻数据需要 AI 进一步分析整理'
        }

        # 保存到 JSON
        json_file = f"a-stock-{date_str}/data/news_{date_str}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(news_data, f, ensure_ascii=False, indent=2, cls=DateEncoder)

        return news_data
    except Exception as e:
        print(f"  ❌ 新闻数据获取失败: {e}")
        raise


def fetch_tgb_data(date_str):
    """获取淘股吧数据"""
    print("  💬 获取淘股吧数据...")
    try:
        # 尝试运行 tgb_spider.py
        tgb_corpus_file = f"a-stock-{date_str}/data/tgb_{date_str}_corpus.txt"
        tgb_list_file = f"a-stock-{date_str}/data/tgb_list_{date_str}.txt"

        # 检查文件是否存在
        if os.path.exists(tgb_corpus_file):
            print(f"    ✅ 淘股吧语料已存在: {tgb_corpus_file}")
            return {'status': 'exists'}
        else:
            print(f"    ⚠️ 淘股吧语料不存在，请先运行 tgb_spider.py")
            return {'status': 'not_found'}
    except Exception as e:
        print(f"  ❌ 淘股吧数据检查失败: {e}")
        return {'status': 'error', 'error': str(e)}


# ------------------------------------------------------------------
# 执行数据准备
# ------------------------------------------------------------------
def execute_data_preparation():
    """执行完整的数据准备流程"""
    date_str = datetime.now().strftime('%Y%m%d')
    workspace = f"a-stock-{date_str}"

    print(f"\n{'='*60}")
    print(f"  📥 数据准备 - {date_str}")
    print(f"{'='*60}\n")

    success_count = 0
    total_count = 5
    market_success = False
    sentiment_success = False

    # 1. 行情数据
    try:
        fetch_market_data(date_str)
        success_count += 1
        market_success = True
    except:
        pass

    # 2. 情绪数据
    try:
        fetch_sentiment_data(date_str)
        success_count += 1
        sentiment_success = True
    except:
        pass

    # 3. 资金数据
    try:
        fetch_fund_data(date_str)
        success_count += 1
    except:
        pass

    # 4. 板块数据
    try:
        fetch_sector_data(date_str)
        success_count += 1
    except:
        pass

    # 5. 新闻数据
    try:
        fetch_news_data(date_str)
        success_count += 1
    except:
        pass

    # 6. 淘股吧数据（可选，不计入成功率）
    try:
        fetch_tgb_data(date_str)
    except:
        pass

    print(f"\n  数据获取完成: {success_count}/{total_count} 项成功")

    # 生成记忆文件
    print("\n  🧠 生成记忆文件...")
    try:
        generate_short_term_memory()
        generate_long_term_memory()
    except Exception as e:
        print(f"    ⚠️ 记忆生成失败: {e}")

    # 至少需要行情和情绪数据都成功才算成功
    return market_success and sentiment_success


# ------------------------------------------------------------------
# 数据准备入口（带重试）
# ------------------------------------------------------------------
def prepare_data_with_retry(max_retries=3):
    """
    数据准备流程（带重试）

    返回:
        'ready': 数据已就绪
        'degraded': 降级数据
    """
    date_str = datetime.now().strftime('%Y%m%d')
    workspace = f"a-stock-{date_str}"

    status = check_data_ready()

    if status == 'ready':
        print(f"\n✅ 数据已就绪（DATA_SUCCESS），跳过数据准备")
        return 'ready'

    if status == 'degraded':
        print(f"\n⚠️ 存在降级数据（DATA_DEGRADED），继续使用")
        return 'degraded'

    # 需要准备，执行数据准备
    for attempt in range(1, max_retries + 1):
        try:
            print(f"\n📥 开始数据准备（第 {attempt}/{max_retries} 次尝试）...")

            # 创建目录结构
            os.makedirs(workspace, exist_ok=True)
            os.makedirs(f"{workspace}/data", exist_ok=True)
            os.makedirs(f"{workspace}/logs", exist_ok=True)
            os.makedirs(f"{workspace}/标的分析", exist_ok=True)

            # 执行数据准备
            success = execute_data_preparation()

            if success:
                # 创建成功 Tag
                tag_file = f"{workspace}/DATA_SUCCESS"
                with open(tag_file, 'w') as f:
                    f.write(f"数据准备完成: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                print(f"\n✅ 数据准备成功（DATA_SUCCESS 已创建）")
                return 'ready'

        except Exception as e:
            print(f"\n❌ 第 {attempt} 次失败: {e}")
            if attempt >= max_retries:
                # 重试 3 次后仍失败，降级
                create_degraded_tag(workspace, error_msg=str(e))
                print(f"\n⚠️ 数据准备降级（DATA_DEGRADED 已创建）")
                return 'degraded'

        # 重试前等待
        if attempt < max_retries:
            print("  等待 2 秒后重试...")
            time.sleep(2)

    # 所有重试都失败，创建降级 Tag
    create_degraded_tag(workspace, error_msg="所有重试均失败：行情和情绪数据获取失败")
    print(f"\n⚠️ 数据准备降级（DATA_DEGRADED 已创建）")
    return 'degraded'


# ------------------------------------------------------------------
# 记忆系统
# ------------------------------------------------------------------
def generate_short_term_memory():
    """生成短期记忆并持久化为 md（近 1 周）"""
    today = datetime.now()
    date_str = today.strftime('%Y%m%d')
    workspace = f"a-stock-{date_str}"

    week_data = []
    for i in range(1, 8):  # 近 7 天
        date = (today - timedelta(days=i)).strftime('%Y%m%d')
        historical_workspace = f"a-stock-{date}"

        # 读取历史情绪数据
        sentiment_file = f"{historical_workspace}/data/sentiment_{date}.json"
        fund_file = f"{historical_workspace}/data/fund_flow_{date}.json"

        item = {'date': date}

        if os.path.exists(sentiment_file):
            try:
                with open(sentiment_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    item['涨停家数'] = data.get('limit_up', 'N/A')
                    item['跌停家数'] = data.get('limit_down', 'N/A')
                    item['情绪等级'] = data.get('limit_up_level', 'N/A')
            except:
                item['涨停家数'] = 'N/A'
                item['跌停家数'] = 'N/A'
                item['情绪等级'] = 'N/A'
        else:
            item['涨停家数'] = 'N/A'
            item['跌停家数'] = 'N/A'
            item['情绪等级'] = 'N/A'

        week_data.append(item)

    # 持久化为 md 文件
    md_content = "# 短期记忆（近 1 周）\n\n"
    md_content += f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"

    for item in week_data:
        md_content += f"## {item['date']}\n"
        md_content += f"- 涨停家数: {item['涨停家数']}\n"
        md_content += f"- 跌停家数: {item['跌停家数']}\n"
        md_content += f"- 情绪等级: {item['情绪等级']}\n\n"

    short_term_file = f"{workspace}/short_term_memory.md"
    with open(short_term_file, 'w', encoding='utf-8') as f:
        f.write(md_content)

    print(f"    ✅ 短期记忆已生成: {short_term_file}")
    return week_data


def generate_long_term_memory():
    """生成长期记忆并持久化为 md（近 1 月）"""
    today = datetime.now()
    date_str = today.strftime('%Y%m%d')
    workspace = f"a-stock-{date_str}"

    month_data = []
    for i in range(1, 31):  # 近 30 天
        date = (today - timedelta(days=i)).strftime('%Y%m%d')
        historical_workspace = f"a-stock-{date}"

        # 读取大盘上下文
        context_file = f"{historical_workspace}/00-大盘上下文.md"

        item = {'date': date}

        if os.path.exists(context_file):
            try:
                with open(context_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # 简单提取关键信息
                    if '安全等级' in content:
                        item['安全等级'] = content.split('安全等级')[1].split('\n')[0] if '安全等级' in content else 'N/A'
                    else:
                        item['安全等级'] = 'N/A'
            except:
                item['安全等级'] = 'N/A'
        else:
            item['安全等级'] = 'N/A'

        month_data.append(item)

    # 持久化为 md 文件
    md_content = "# 长期记忆（近 1 月）\n\n"
    md_content += f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"

    for item in month_data:
        md_content += f"## {item['date']}\n"
        md_content += f"- 安全等级: {item.get('安全等级', 'N/A')}\n\n"

    long_term_file = f"{workspace}/long_term_memory.md"
    with open(long_term_file, 'w', encoding='utf-8') as f:
        f.write(md_content)

    print(f"    ✅ 长期记忆已生成: {long_term_file}")
    return month_data


def load_memory():
    """加载记忆（优先从 md 文件读取）"""
    today = datetime.now()
    date_str = today.strftime('%Y%m%d')
    workspace = f"a-stock-{date_str}"

    short_term_file = f"{workspace}/short_term_memory.md"
    long_term_file = f"{workspace}/long_term_memory.md"

    short_term = []
    long_term = []

    # 读取短期记忆
    if os.path.exists(short_term_file):
        try:
            with open(short_term_file, 'r', encoding='utf-8') as f:
                short_term = f.read()
        except:
            short_term = ""

    # 读取长期记忆
    if os.path.exists(long_term_file):
        try:
            with open(long_term_file, 'r', encoding='utf-8') as f:
                long_term = f.read()
        except:
            long_term = ""

    return short_term, long_term


# ------------------------------------------------------------------
# 市场行情分析
# ------------------------------------------------------------------
def analyze_market_quotes():
    """
    分析市场整体行情

    返回:
        market_status: dict
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
        sentiment_status: dict
    """
    print("\n" + "="*60)
    print("  😊 市场情绪分析")
    print("="*60 + "\n")

    try:
        # 涨停家数（市场情绪指标）
        df = ak.stock_zh_a_spot_em()
        limit_up = len(df[df['涨跌幅'] >= 9.5])
        limit_down = len(df[df['涨跌幅'] <= -9.5])

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
        news_status: dict
    """
    print("\n" + "="*60)
    print("  📰 消息面分析")
    print("="*60 + "\n")

    # 读取已获取的新闻数据
    date_str = datetime.now().strftime('%Y%m%d')
    news_file = f"a-stock-{date_str}/data/news_{date_str}.json"

    if os.path.exists(news_file):
        try:
            with open(news_file, 'r', encoding='utf-8') as f:
                news_data = json.load(f)
            print(f"已加载新闻数据")
        except:
            news_data = {}
    else:
        news_data = {}

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

    # 5. 加载记忆
    print("\n" + "="*70)
    print("  🧠 记忆加载")
    print("="*70)

    short_term, long_term = load_memory()
    if short_term:
        print(f"  ✅ 短期记忆已加载 ({len(short_term)} 字符)")
    if long_term:
        print(f"  ✅ 长期记忆已加载 ({len(long_term)} 字符)")

    return {
        'market': market,
        'sentiment': sentiment,
        'news': news,
        'recommendations': recommendations,
        'short_term_memory': short_term,
        'long_term_memory': long_term
    }


def select_mode(mode_name: str = None, force_prepare: bool = False):
    """
    选择特定模式

    mode_name: '情绪' / '量化' / '机构'
    force_prepare: 是否强制重新准备数据
    """
    # 如果强制重新准备，先清理 Tag
    if force_prepare:
        date_str = datetime.now().strftime('%Y%m%d')
        workspace = f"a-stock-{date_str}"
        success_tag = f"{workspace}/DATA_SUCCESS"
        degraded_tag = f"{workspace}/DATA_DEGRADED"
        if os.path.exists(success_tag):
            os.remove(success_tag)
            print(f"已清理 DATA_SUCCESS Tag")
        if os.path.exists(degraded_tag):
            os.remove(degraded_tag)
            print(f"已清理 DATA_DEGRADED Tag")

    # Step 0: 数据准备
    print("\n" + "="*70)
    print("  Step 0: 数据准备检查")
    print("="*70)

    status = prepare_data_with_retry(max_retries=3)

    if status == 'degraded':
        print("\n⚠️ 数据处于降级状态，分析置信度将降低")

    if mode_name is None:
        # 自动选择：执行完整分析
        result = run_market_analysis()
        return result

    # 手动选择模式
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

    args = sys.argv[1:]

    if '--help' in args or '-h' in args:
        print("""
A股交易模式选择器

用法:
  python mode_selector.py              # 自动分析
  python mode_selector.py 情绪         # 选择情绪模式
  python mode_selector.py 量化         # 选择量化模式
  python mode_selector.py 机构         # 选择机构模式
  python mode_selector.py --prepare    # 仅执行数据准备
  python mode_selector.py --force      # 强制重新准备数据
  python mode_selector.py --help       # 显示帮助

示例:
  python mode_selector.py              # 执行完整市场分析
  python mode_selector.py --force     # 强制重新获取数据
  python mode_selector.py 情绪 --force # 选择情绪模式并强制刷新数据
        """)
        sys.exit(0)

    if '--prepare' in args:
        prepare_data_with_retry(max_retries=3)
        sys.exit(0)

    force_prepare = '--force' in args

    # 提取模式参数
    mode_arg = None
    for arg in args:
        if arg in ['情绪', '量化', '机构']:
            mode_arg = arg

    select_mode(mode_arg, force_prepare=force_prepare)
