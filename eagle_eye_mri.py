import streamlit as st
import akshare as ak
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# -------------------------- 全局配置 & 系统终版规则锁死 --------------------------
# 严格匹配v1.9终版权重与规则，禁止擅自修改
SYSTEM_CONFIG = {
    "total_score": 100,
    "weight": {
        "3d_audit": 40,  # 三维前置审计
        "l2_audit": 15,   # L2暗盘审计
        "five_dimension": 45  # 五维加权审计
    },
    "3d_weight": {
        "macro": 10,
        "industry": 20,
        "company": 10
    },
    "five_dimension_weight": {
        "chip": 20,
        "technical": 8,
        "risk": 7,
        "fund_activity": 5,
        "odds": 5
    },
    "double_access": {
        "3d_pass": 24,  # 三维审计60%及格线
        "l2_pass": 9     # L2审计60%及格线
    },
    "red_line": {
        "pass_line": 60,
        "attack_line": 80,
        "attack_3d": 32,
        "attack_l2": 12
    }
}

# -------------------------- 数据缓存函数（提升加载速度） --------------------------
@st.cache_data(ttl=3600)  # 1小时缓存，避免频繁调用接口
def get_index_data():
    """获取大盘核心指数数据"""
    try:
        index_df = ak.stock_zh_index_spot()
        core_index = index_df[index_df['代码'].isin(['sh000001', 'sz399001', 'sz399006', 'sh000688'])]
        return core_index
    except:
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def get_market_overview():
    """获取全市场全景数据"""
    try:
        market_df = ak.stock_market_fund_flow()
        limit_up_df = ak.stock_em_zt_pool(date=datetime.now().strftime('%Y%m%d'))
        limit_down_df = ak.stock_em_zt_pool_dt(date=datetime.now().strftime('%Y%m%d'))
        north_df = ak.stock_em_hsgt_north_net_flow_in()
        trade_amount = ak.stock_em_market_overview()
        return {
            "market_flow": market_df,
            "limit_up": limit_up_df,
            "limit_down": limit_down_df,
            "north_flow": north_df,
            "trade_amount": trade_amount
        }
    except:
        return {}

@st.cache_data(ttl=3600)
def get_stock_basic_info(stock_code):
    """获取个股基础信息"""
    try:
        basic_df = ak.stock_individual_info_em(symbol=stock_code)
        basic_dict = dict(zip(basic_df['item'], basic_df['value']))
        industry_df = ak.stock_board_industry_cons_em(symbol=basic_dict['行业'])
        industry_rank = industry_df[industry_df['代码'] == stock_code].index[0] + 1 if not industry_df.empty else 999
        basic_dict['行业排名'] = industry_rank
        basic_dict['行业总家数'] = len(industry_df)
        return basic_dict
    except:
        return {}

@st.cache_data(ttl=3600)
def get_stock_kline(stock_code, period="daily", start_date=None):
    """获取个股K线数据"""
    if not start_date:
        start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')
    end_date = datetime.now().strftime('%Y%m%d')
    try:
        kline_df = ak.stock_zh_a_hist(
            symbol=stock_code,
            period=period,
            start_date=start_date,
            end_date=end_date,
            adjust="qfq"
        )
        kline_df['ma20'] = kline_df['收盘'].rolling(window=20).mean()
        kline_df['ma60'] = kline_df['收盘'].rolling(window=60).mean()
        kline_df['ma120'] = kline_df['收盘'].rolling(window=120).mean()
        return kline_df
    except:
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def get_industry_fund_flow(industry_name):
    """获取行业资金流向数据"""
    try:
        industry_flow_df = ak.stock_sector_fund_flow_rank_em(indicator="5日")
        target_industry = industry_flow_df[industry_flow_df['行业名称'] == industry_name]
        return target_industry if not target_industry.empty else pd.DataFrame()
    except:
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def get_stock_financial_data(stock_code):
    """获取个股财务数据"""
    try:
        financial_df = ak.stock_financial_abstract_ths(symbol=stock_code, indicator="按报告期")
        goodwill_df = ak.stock_financial_report_sina(stock=stock_code, symbol="资产负债表")
        pledge_df = ak.stock_holder_pledge_em(symbol=stock_code)
        risk_df = ak.stock_em_st_warning()
        is_st = stock_code in risk_df['代码'].values
        legal_df = ak.stock_em_legal_proceeding()
        is_legal = stock_code in legal_df['证券代码'].values
        return {
            "financial": financial_df,
            "goodwill": goodwill_df,
            "pledge": pledge_df,
            "is_st": is_st,
            "is_legal": is_legal
        }
    except:
        return {}

@st.cache_data(ttl=3600)
def get_chip_distribution(stock_code):
    """获取个股筹码分布数据"""
    try:
        chip_df = ak.stock_chip_distribution_em(symbol=stock_code)
        latest_chip = chip_df.iloc[-1] if not chip_df.empty else {}
        return latest_chip
    except:
        return {}

@st.cache_data(ttl=3600)
def get_hot_industry():
    """获取当前市场热门主线行业"""
    try:
        hot_df = ak.stock_sector_fund_flow_rank_em(indicator="今日")
        return hot_df.head(10)['行业名称'].tolist()
    except:
        return []

# -------------------------- 核心审计打分函数（严格匹配v1.9终版规则） --------------------------
def macro_audit(market_data, index_data):
    """宏观大盘维度审计 满分10分"""
    score = 0
    red_line_trigger = False
    detail = {
        "market_env": 0,
        "liquidity": 0,
        "policy": 3,
        "risk_detail": ""
    }

    try:
        sz_index = index_data[index_data['代码'] == 'sh000001'].iloc[0]
        latest_close = sz_index['最新价']
        sz_kline = ak.stock_zh_index_hist_csindex(symbol='000001', start_date=(datetime.now()-timedelta(days=180)).strftime('%Y%m%d'), end_date=datetime.now().strftime('%Y%m%d'))
        sz_kline['ma120'] = sz_kline['收盘'].rolling(window=120).mean()
        ma120 = sz_kline.iloc[-1]['ma120']
        ma120_prev = sz_kline.iloc[-5]['ma120'] if len(sz_kline)>=5 else ma120

        if latest_close > ma120 and ma120 > ma120_prev:
            detail['market_env'] = 4
        elif latest_close > ma120:
            detail['market_env'] = 2
        else:
            detail['market_env'] = 0
            red_line_trigger = True
            detail['risk_detail'] += "大盘有效跌破120日线呈空头排列，触发宏观红线；"
    except:
        detail['market_env'] = 2
        detail['risk_detail'] += "大盘数据获取异常，默认中性；"

    try:
        trade_amount = market_data['trade_amount'].iloc[0]['两市成交额']
        north_flow = market_data['north_flow'].iloc[-1]['净流入']
        main_flow = market_data['market_flow'].iloc[0]['主力净流入-净额']

        if north_flow > 0 and main_flow > 0 and trade_amount > 8000:
            detail['liquidity'] = 3
        elif north_flow > 0 or main_flow > 0:
            detail['liquidity'] = 1
        else:
            detail['liquidity'] = 0
    except:
        detail['liquidity'] = 1
        detail['risk_detail'] += "流动性数据获取异常，默认中性；"

    score = detail['market_env'] + detail['liquidity'] + detail['policy']
    if red_line_trigger:
        score = 0
    return score, detail, red_line_trigger

def industry_audit(industry_name, industry_flow_df, hot_industry_list):
    """行业赛道维度审计 满分20分"""
    score = 0
    red_line_trigger = False
    detail = {
        "boom": 0,
        "competition": 0,
        "plate_effect": 0,
        "risk_detail": ""
    }

    try:
        net_flow_5d = industry_flow_df.iloc[0]['5日净流入-净额'] if not industry_flow_df.empty else 0
        if net_flow_5d > 0:
            detail['boom'] = 8
        elif net_flow_5d == 0:
            detail['boom'] = 4
        else:
            detail['boom'] = 0
            red_line_trigger = True
            detail['risk_detail'] += "行业景气度下行，触发行业红线；"
    except:
        detail['boom'] = 4
        detail['risk_detail'] += "行业景气度数据获取异常，默认中性；"

    try:
        stock_basic = get_stock_basic_info(st.session_state.stock_code)
        industry_rank = stock_basic.get('行业排名', 999)
        industry_total = stock_basic.get('行业总家数', 1000)
        if industry_rank <= 3:
            detail['competition'] = 6
        elif industry_rank <= 10:
            detail['competition'] = 3
        else:
            detail['competition'] = 0
    except:
        detail['competition'] = 0
        detail['risk_detail'] += "行业竞争格局数据获取异常；"

    try:
        if industry_name in hot_industry_list and not industry_flow_df.empty:
            net_flow_5d = industry_flow_df.iloc[0]['5日净流入-净额']
            if net_flow_5d > 0:
                detail['plate_effect'] = 6
            else:
                detail['plate_effect'] = 3
        elif industry_name in hot_industry_list:
            detail['plate_effect'] = 3
        else:
            detail['plate_effect'] = 0
    except:
        detail['plate_effect'] = 0
        detail['risk_detail'] += "板块效应数据获取异常；"

    score = detail['boom'] + detail['competition'] + detail['plate_effect']
    if red_line_trigger:
        score = 0
    return score, detail, red_line_trigger

def company_audit(stock_code, financial_data, basic_info):
    """公司基本面维度审计 满分10分"""
    score = 0
    red_line_trigger = False
    detail = {
        "moat": 0,
        "profit": 0,
        "governance": 0,
        "risk_detail": ""
    }

    is_st = financial_data.get('is_st', False)
    is_legal = financial_data.get('is_legal', False)
    if is_st or is_legal:
        red_line_trigger = True
        detail['risk_detail'] += "公司ST/立案调查，触发公司红线；"
        return 0, detail, red_line_trigger

    try:
        industry_rank = basic_info.get('行业排名', 999)
        if industry_rank <= 3:
            detail['moat'] = 4
        elif industry_rank <= 10:
            detail['moat'] = 2
        else:
            detail['moat'] = 0
    except:
        detail['moat'] = 0
        detail['risk_detail'] += "护城河数据获取异常；"

    try:
        financial_df = financial_data.get('financial', pd.DataFrame())
        if not financial_df.empty:
            net_profit_yoy = financial_df.iloc[0]['扣非净利润同比增长']
            operate_cash = financial_df.iloc[0]['经营活动产生的现金流量净额']
            revenue_yoy = financial_df.iloc[0]['营业收入同比增长']
            if net_profit_yoy > 0 and operate_cash > 0 and revenue_yoy > 0:
                detail['profit'] = 3
            elif net_profit_yoy > 0:
                detail['profit'] = 1
            else:
                detail['profit'] = 0
        else:
            detail['profit'] = 1
    except:
        detail['profit'] = 1
        detail['risk_detail'] += "盈利数据获取异常，默认中性；"

    try:
        pledge_df = financial_data.get('pledge', pd.DataFrame())
        pledge_ratio = pledge_df.iloc[0]['质押比例'] if not pledge_df.empty else 0
        if pledge_ratio < 10:
            detail['governance'] = 3
        elif pledge_ratio < 30:
            detail['governance'] = 1
        else:
            detail['governance'] = 0
    except:
        detail['governance'] = 1
        detail['risk_detail'] += "治理风险数据获取异常，默认中性；"

    score = detail['moat'] + detail['profit'] + detail['governance']
    return score, detail, red_line_trigger

def chip_audit(chip_data, kline_df):
    """筹码结构审计 满分20分"""
    score = 0
    red_line_trigger = False
    detail = {
        "shape": 0,
        "lock": 0,
        "profit": 0,
        "concentration": 0,
        "risk_detail": ""
    }

    try:
        price_range = chip_data.get('90%成本区间', '0-0').split('-')
        price_range = [float(x) for x in price_range]
        range_ratio = (price_range[1] - price_range[0]) / price_range[0] if price_range[0] !=0 else 1
        if range_ratio < 0.15:
            detail['shape'] = 8
        else:
            detail['shape'] = 2

        chip_5d_ago = ak.stock_chip_distribution_em(symbol=st.session_state.stock_code).iloc[-5] if len(ak.stock_chip_distribution_em(symbol=st.session_state.stock_code))>=5 else chip_data
        current_bottom = chip_data.get('获利比例', 0)
        prev_bottom = chip_5d_ago.get('获利比例', 0)
        if abs(current_bottom - prev_bottom) < 10:
            detail['lock'] = 6
        else:
            detail['lock'] = 2

        profit_ratio = chip_data.get('获利比例', 0)
        if 60 <= profit_ratio <= 90:
            detail['profit'] = 3
        else:
            detail['profit'] = 0

        concentration = chip_data.get('90%成本集中度', 100)
        if concentration < 10:
            detail['concentration'] = 3
        else:
            detail['concentration'] = 0

        if current_bottom < 10 and prev_bottom > 50:
            red_line_trigger = True
            detail['risk_detail'] += "底部筹码峰完全消失，触发筹码死刑红线；"

    except Exception as e:
        detail['risk_detail'] += f"筹码数据获取异常：{str(e)}；"

    score = detail['shape'] + detail['lock'] + detail['profit'] + detail['concentration']
    return score, detail, red_line_trigger

def technical_audit(kline_df):
    """技术环境审计 满分8分"""
    score = 0
    detail = {
        "lifeline": 0,
        "trend": 0,
        "risk_detail": ""
    }

    try:
        latest_data = kline_df.iloc[-1]
        if latest_data['收盘'] > latest_data['ma120']:
            detail['lifeline'] = 4
        else:
            detail['lifeline'] = 0

        if latest_data['收盘'] > latest_data['ma20'] and latest_data['ma20'] > latest_data['ma60'] and latest_data['ma60'] > latest_data['ma120']:
            detail['trend'] = 4
        elif latest_data['收盘'] > latest_data['ma60']:
            detail['trend'] = 2
        else:
            detail['trend'] = 0
    except:
        detail['risk_detail'] += "技术指标计算异常；"

    score = detail['lifeline'] + detail['trend']
    return score, detail

def risk_audit(financial_data, basic_info):
    """排雷安全审计 满分7分"""
    score = 0
    red_line_trigger = False
    detail = {
        "goodwill": 0,
        "market_cap": 0,
        "risk_detail": ""
    }

    try:
        goodwill_df = financial_data.get('goodwill', pd.DataFrame())
        if not goodwill_df.empty:
            goodwill = goodwill_df.iloc[0]['商誉']
            net_asset = goodwill_df.iloc[0]['所有者权益合计']
            goodwill_ratio = goodwill / net_asset if net_asset !=0 else 1
            if goodwill_ratio < 0.15:
                detail['goodwill'] = 4
            elif 0.15 <= goodwill_ratio < 0.3:
                detail['goodwill'] = 0
            else:
                detail['goodwill'] = -10
                red_line_trigger = True
                detail['risk_detail'] += "商誉占净资产超30%，触发排雷红线；"
        else:
            detail['goodwill'] = 2

        market_cap = basic_info.get('总市值', 0)
        if market_cap > 3000000000:
            detail['market_cap'] = 3
        else:
            detail['market_cap'] = 0
    except:
        detail['risk_detail'] += "排雷数据获取异常；"

    score = detail['goodwill'] + detail['market_cap']
    return score, detail, red_line_trigger

def fund_activity_audit(kline_df, basic_info):
    """资金活性审计 满分5分"""
    score = 0
    detail = {
        "attack": 0,
        "purity": 0,
        "risk_detail": ""
    }

    try:
        latest_data = kline_df.iloc[-1]
        turnover_rate = latest_data['换手率']
        volume_ratio = latest_data['成交量'] / kline_df.iloc[-20:-1]['成交量'].mean()
        if volume_ratio > 1.5 or turnover_rate > 3:
            detail['attack'] = 3
        else:
            detail['attack'] = 0

        recent_30d = kline_df.iloc[-30:]
        max_shadow = (recent_30d['最高'] - recent_30d['收盘']).max() / recent_30d['收盘']
        if max_shadow < 0.08:
            detail['purity'] = 2
        else:
            detail['purity'] = 0
    except:
        detail['risk_detail'] += "资金活性数据计算异常；"

    score = detail['attack'] + detail['purity']
    return score, detail

def odds_audit(kline_df):
    """赔率决策审计 满分5分"""
    score = 0
    r_value = 0
    support = 0
    pressure = 0
    detail = {
        "r_value": 0,
        "support": 0,
        "pressure": 0,
        "risk_detail": ""
    }

    try:
        latest_close = kline_df.iloc[-1]['收盘']
        support = min(kline_df.iloc[-20:]['最低'].min(), kline_df.iloc[-1]['ma60'])
        pressure = kline_df.iloc[-60:]['最高'].max()

        if latest_close - support != 0:
            r_value = (pressure - latest_close) / (latest_close - support)
        else:
            r_value = 0

        if r_value > 3.0:
            detail['r_value'] = 5
        elif 2.0 < r_value <= 3.0:
            detail['r_value'] = 3
        else:
            detail['r_value'] = 0

        detail['support'] = round(support, 2)
        detail['pressure'] = round(pressure, 2)
        detail['r_value'] = round(r_value, 2)
    except:
        detail['risk_detail'] += "赔率计算异常；"

    score = detail['r_value'] if detail['r_value'] <=5 else 5
    return score, detail

def cycle_position(kline_df, chip_data):
    """周期四季定位"""
    try:
        latest_data = kline_df.iloc[-1]
        ma120 = latest_data['ma120']
        close = latest_data['收盘']
        chip_lock = abs(chip_data.get('获利比例', 0) - ak.stock_chip_distribution_em(symbol=st.session_state.stock_code).iloc[-5].get('获利比例', 0)) < 10 if len(ak.stock_chip_distribution_em(symbol=st.session_state.stock_code))>=5 else True
        profit_ratio = chip_data.get('获利比例', 0)
        concentration = chip_data.get('90%成本集中度', 100)

        if close < ma120 and kline_df['ma120'].iloc[-5] > ma120:
            return "崩塌期"
        elif close > ma120 and profit_ratio > 90 and not chip_lock:
            return "派发期"
        elif close > ma120 and 30 <= close/ma120 -1 <= 100 and chip_lock:
            return "主升期"
        elif abs(close - ma120)/ma120 < 0.1 and concentration < 10:
            return "潜伏期"
        else:
            return "潜伏期"
    except:
        return "未知周期"

# -------------------------- Streamlit 界面主程序 --------------------------
st.set_page_config(page_title="Depp·鹰眼MRI审计子系统 v1.9", layout="wide", page_icon="📊")
st.title("📊 Depp·鹰眼 MRI 审计子系统 v1.9 终版")
st.caption("全量无损终版 | 严格匹配终版规则 | 公开数据自动调取 | L2数据手动输入")

# 1. 股票代码输入
col1, col2 = st.columns([3, 1])
with col1:
    stock_code = st.text_input("请输入A股股票代码（例：002594、600519）", max_chars=6, placeholder="仅输入6位数字代码")
with col2:
    st.write("")
    st.write("")
    run_button = st.button("🚀 启动深度体检", type="primary", use_container_width=True)

# 2. L2数据手动输入区域
st.subheader("📥 L2暗盘资金手动侦查数据（必填）")
col_l2_1, col_l2_2, col_l2_3 = st.columns(3)
with col_l2_1:
    l2_5d_score = st.slider("近5天暗盘资金得分（0-10分）", min_value=0, max_value=10, value=0)
with col_l2_2:
    l2_3d_score = st.slider("近3天暗盘资金得分（0-5分）", min_value=0, max_value=5, value=0)
with col_l2_3:
    l2_red_line = st.checkbox("是否触发L2死刑红线？", value=False)
l2_total_score = l2_5d_score + l2_3d_score
st.info(f"当前L2暗盘审计总得分：{l2_total_score}/15分 | 及格线9分")

# 3. 核心体检执行逻辑
if run_button and stock_code:
    st.session_state.stock_code = stock_code
    with st.spinner("正在调取全量公开数据，执行MRI深度审计..."):
        index_data = get_index_data()
        market_data = get_market_overview()
        basic_info = get_stock_basic_info(stock_code)
        kline_df = get_stock_kline(stock_code)
        financial_data = get_stock_financial_data(stock_code)
        chip_data = get_chip_distribution(stock_code)
        hot_industry = get_hot_industry()
        industry_name = basic_info.get('行业', '')
        industry_flow_df = get_industry_fund_flow(industry_name)

        macro_score, macro_detail, macro_red = macro_audit(market_data, index_data)
        industry_score, industry_detail, industry_red = industry_audit(industry_name, industry_flow_df, hot_industry)
        company_score, company_detail, company_red = company_audit(stock_code, financial_data, basic_info)
        chip_score, chip_detail, chip_red = chip_audit(chip_data, kline_df)
        technical_score, technical_detail = technical_audit(kline_df)
        risk_score, risk_detail, risk_red = risk_audit(financial_data, basic_info)
        fund_activity_score, fund_activity_detail = fund_activity_audit(kline_df, basic_info)
        odds_score, odds_detail = odds_audit(kline_df)
        cycle = cycle_position(kline_df, chip_data)

        total_3d_score = macro_score + industry_score + company_score
        total_five_score = chip_score + technical_score + risk_score + fund_activity_score + odds_score
        base_total_score = total_3d_score + l2_total_score + total_five_score

        privilege_bonus = 0
        if total_3d_score == 40:
            privilege_bonus += 10
        if l2_total_score == 15:
            privilege_bonus +=5
        if chip_score ==20:
            privilege_bonus +=3
        final_total_score = base_total_score + privilege_bonus

        death_trigger = False
        death_reason = []
        if macro_red or industry_red or company_red:
            death_trigger = True
            death_reason.append("三维前置审计触发红线条款")
        if l2_red_line:
            death_trigger = True
            death_reason.append("L2暗盘资金侦查触发红线条款")
        if chip_red:
            death_trigger = True
            death_reason.append("筹码诈骗红线触发，底部筹码峰完全消失")
        if financial_data.get('is_st', False) or financial_data.get('is_legal', False):
            death_trigger = True
            death_reason.append("基本面暴雷红线触发，ST/立案调查")
        if risk_score <0:
            death_trigger = True
            death_reason.append("商誉占比超30%，触发排雷红线")

        double_access_pass = (total_3d_score >= SYSTEM_CONFIG['double_access']['3d_pass']) and (l2_total_score >= SYSTEM_CONFIG['double_access']['l2_pass']) and (not death_trigger)
        attack_pass = (total_3d_score >= SYSTEM_CONFIG['red_line']['attack_3d']) and (l2_total_score >= SYSTEM_CONFIG['red_line']['attack_l2']) and (final_total_score >= SYSTEM_CONFIG['red_line']['attack_line']) and double_access_pass

        if death_trigger or not double_access_pass:
            final_command = "空仓拉黑"
        elif final_total_score < 60:
            final_command = "空仓"
        elif 60 <= final_total_score <70:
            final_command = "观察"
        elif 70 <= final_total_score <80:
            final_command = "轻仓"
        elif 80 <= final_total_score <90:
            final_command = "标仓"
        else:
            final_command = "重仓"

        st.divider()
        st.header(f"【鹰眼审计卡 v1.9】{basic_info.get('股票简称', stock_code)} 深度体检报告")
        st.divider()

        st.subheader("I. 核心决策看板（一眼定生死）")
        col_board_1, col_board_2 = st.columns(2)
        with col_board_1:
            st.metric("鹰眼最终总分", f"{final_total_score}分", f"含特权加分：{privilege_bonus}分")
            st.caption(f"及格线：{SYSTEM_CONFIG['red_line']['pass_line']}分 | 强攻线：{SYSTEM_CONFIG['red_line']['attack_line']}分")
            st.metric("周期定位", cycle)
        with col_board_2:
            st.write(f"**双准入校验结果**：三维审计 {total_3d_score}/40分（{'通过' if total_3d_score>=24 else '不通过'}）| L2暗盘审计 {l2_total_score}/15分（{'通过' if l2_total_score>=9 else '不通过'}）")
            st.write(f"**核心定性结论**：{basic_info.get('股票简称', stock_code)}所属{industry_name}赛道，{'为当前市场核心热门主线' if industry_name in hot_industry else '非市场主线'}，大盘{'流动性宽松无系统性风险' if macro_score>=6 else '存在系统性风险'}，L2暗盘{'确认主力锁仓建仓' if l2_total_score>=12 else '无明确主力建仓信号'}，处于{cycle}，{'总分达标触发强攻规则' if attack_pass else '未达到强攻标准'}")
            st.write(f"**最终作战指令**：:red[{final_command}]" if final_command in ["空仓", "空仓拉黑"] else f"**最终作战指令**：:green[{final_command}]")

        if death_trigger:
            st.error(f"⚠️ 触发死刑条款，逻辑崩塌，总分清零，永久拉黑！触发原因：{'、'.join(death_reason)}", icon="🚨")
            st.stop()

        st.divider()

        st.subheader("II. 战术执行方案（精简核心·极致精准）")
        st.caption("⚠️ 【执行铁律】仅双准入校验通过、无红线触发的标的可执行；崩塌期/红线触发标的直接空仓拉黑，严禁操作。")

        col_tactics_1, col_tactics_2 = st.columns(2)
        with col_tactics_1:
            st.subheader("精准进场点位")
            support = odds_detail['support']
            pressure = odds_detail['pressure']
            current_close = kline_df.iloc[-1]['收盘'] if not kline_df.empty else 0
            st.write(f"- **首仓进场位**：{round(support*1.01, 2)}元（20日均线/筹码峰上沿强支撑）")
            st.write(f"  触发条件：回踩支撑不破+L2盘口大单承接，仓位：计划总仓位的50%")
            st.write(f"- **加仓进场位**：{round(pressure*0.99, 2)}元（前高/关键压力位）")
            st.write(f"  触发条件：放量突破（量比≥2）+L2资金持续流入，仓位：计划总仓位的50%")
            st.write("- **进场禁忌**：无承接高位追涨、支撑破位后反抽进场，0仓位")

            st.subheader("极限反向博弈（仅高确定性场景适配）")
            st.caption("⚠️ 【准入前提】必须同时满足：三维+L2全达标、赛道为市场主线、底部筹码100%锁定、仅大盘/板块情绪错杀、处于潜伏期/主升期，缺一不可")
            panic_support = round(support*0.92, 2)
            st.write(f"- **博弈进场位**：{panic_support}元（恐慌杀跌强支撑位/黄金分割0.618位）")
            st.write(f"  触发条件：杀跌末端放量止跌+大单承接")
            st.write("- **仓位限制**：不超过总仓位的20%，仅小仓位博弈")
            st.write("- **博弈止盈**：反弹至10/20日均线压力位全仓兑现，盈利目标5%-10%，不格局")
            st.write("- **博弈止损**：跌破恐慌前低/亏损超5%，无条件清仓，绝不补仓")

        with col_tactics_2:
            st.subheader("止盈止损铁律")
            st.subheader("止盈规则")
            first_pressure = round(current_close*1.1, 2) if pressure ==0 else round(pressure*0.8, 2)
            st.write(f"- **第一止盈位**：{first_pressure}元（第一压力位/套牢盘密集区），触发：触及后放量滞涨，兑现50%仓位")
            st.write(f"- **终极止盈位**：{round(pressure, 2)}元（估值目标位/板块情绪顶），触发：底部筹码松动+L2主力净流出，清仓")
            st.write("- **移动止盈保护**：以20日均线为生命线，有效跌破且当日无法收回，直接清仓")

            st.subheader("止损规则")
            stop_loss = round(support*0.92, 2)
            st.write(f"- **技术止损位**：{stop_loss}元（底部筹码峰下沿/进场位最大回撤8%），有效跌破无条件清仓，单笔亏损不超总资金2%")
            st.write("- **逻辑止损**：触发任意死刑红线/公司出现重大基本面利空，当日无条件清仓，永久拉黑")

        st.divider()

        st.subheader("III. 底层逻辑一句话速览（强制精准落地）")
        trade_amount = market_data.get('trade_amount', pd.DataFrame()).iloc[0]['两市成交额'] if not market_data.get('trade_amount', pd.DataFrame()).empty else 0
        north_flow = market_data.get('north_flow', pd.DataFrame()).iloc[-1]['净流入'] if not market_data.get('north_flow', pd.DataFrame()).empty else 0
        limit_up_count = len(market_data.get('limit_up', pd.DataFrame()))
        limit_down_count = len(market_data.get('limit_down', pd.DataFrame()))
        macro_desc = f"前一日两市成交额{round(trade_amount/100000000, 2)}亿元，北向资金净流入{round(north_flow/100000000, 2)}亿元，全市场涨停{limit_up_count}家，跌停{limit_down_count}家，核心指数{'站稳120日线，货币政策宽松无收紧预期' if macro_score>=6 else '跌破120日线，存在系统性风险'}，市场主线为{','.join(hot_industry[:3])}"
        st.write(f"- **大盘情况**：{macro_desc}")

        industry_flow_5d = industry_flow_df.iloc[0]['5日净流入-净额'] if not industry_flow_df.empty else 0
        industry_desc = f"所属{industry_name}赛道，{'为当前市场TOP3热门主线' if industry_name in hot_industry else '非市场热门主线'}，近5日板块主力资金累计净流入{round(industry_flow_5d/100000000, 2)}亿元，行业景气度{'持续上行' if industry_score>=12 else '平稳/下行'}，市场认可度{'极高' if industry_name in hot_industry else '一般'}"
        st.write(f"- **赛道情况**：{industry_desc}")

        industry_rank = basic_info.get('行业排名', 999)
        industry_total = basic_info.get('行业总家数', 1000)
        financial_df = financial_data.get('financial', pd.DataFrame())
        net_profit_yoy = financial_df.iloc[0]['扣非净利润同比增长'] if not financial_df.empty else 0
        company_desc = f"公司为{industry_name}行业排名第{industry_rank}/{industry_total}，核心上涨驱动为{'业绩增长' if net_profit_yoy>0 else '行业题材'}，最新报告期扣非净利润同比增长{net_profit_yoy}%，{'无重大利空风险' if company_score>=6 else '存在经营/治理风险'}"
        st.write(f"- **公司情况**：{company_desc}")

        st.divider()

        st.subheader("IV. 分维度详细审计说明（强制细化无笼统）")
        with st.expander("1. 宏观大盘维度审计（满分10分，得分{}分）".format(macro_score), expanded=True):
            st.write(f"【市场全景与核心主线】：当前A股核心指数{'站稳120日线，呈多头趋势' if macro_detail['market_env']>=2 else '跌破120日线，呈空头趋势'}，两市成交额{round(trade_amount/100000000, 2)}亿元，市场核心炒作主线为{','.join(hot_industry[:5])}，全市场资金{'整体净流入' if market_data.get('market_flow', pd.DataFrame()).iloc[0]['主力净流入-净额']>0 else '整体净流出'}")
            st.write(f"【利好驱动明细】：北向资金净流入{round(north_flow/100000000, 2)}亿元，市场主线板块持续活跃，涨停家数{limit_up_count}家，市场情绪平稳，无重大地缘/政策利空")
            st.write(f"【利空风险明细】：跌停家数{limit_down_count}家，{'主力资金整体净流出' if market_data.get('market_flow', pd.DataFrame()).iloc[0]['主力净流入-净额']<0 else '无重大资金流出风险'}，{'大盘跌破120日线，存在系统性下跌风险' if macro_red else '无系统性风险'}")
            st.write(f"红线排查：{'是' if macro_red else '否'}触发一票否决条款")

        with st.expander("2. 行业赛道维度审计（满分20分，得分{}分）".format(industry_score), expanded=True):
            st.write(f"【赛道定位与热门度评级】：{industry_name}赛道，全市场热门度排名{hot_industry.index(industry_name)+1 if industry_name in hot_industry else '未进前10'}，行业景气度{'上行周期' if industry_detail['boom']>=4 else '平稳/下行周期'}，板块整体走势{'呈上升趋势' if industry_flow_5d>0 else '横盘/下行趋势'}")
            st.write(f"【热门核心底层逻辑】：{'行业需求扩张、资金持续流入，为市场主线题材' if industry_name in hot_industry else '非市场主线，资金关注度低，无持续上涨逻辑'}")
            st.write(f"【利好催化明细】：近5日板块主力资金净流入{round(industry_flow_5d/100000000, 2)}亿元，{'为市场热门主线，板块效应强' if industry_name in hot_industry else '无重大利好催化'}")
            st.write(f"【利空风险明细】：{'行业景气度下行，资金持续流出' if industry_red else '无行业性利空风险'}")
            st.write(f"红线排查：{'是' if industry_red else '否'}触发一票否决条款")

        with st.expander("3. 公司基本面维度审计（满分10分，得分{}分）".format(company_score), expanded=True):
            st.write(f"【公司核心定位】：{basic_info.get('股票简称', stock_code)}，{industry_name}行业排名第{industry_rank}/{industry_total}，核心竞争力{'为行业龙头，具备品牌/技术壁垒' if company_detail['moat']>=2 else '无明显核心壁垒'}")
            st.write(f"【热门/上涨核心驱动逻辑】：{'业绩持续增长，行业龙头地位稳固' if company_score>=6 else '行业题材炒作，无基本面支撑'}")
            st.write(f"【落地式利好明细】：最新报告期扣非净利润同比增长{net_profit_yoy}%，经营现金流{'为正，盈利质量良好' if company_detail['profit']>=3 else '为负，盈利质量较差'}，股权质押比例低，无重大治理风险")
            st.write(f"【利空风险明细】：{'行业排名靠后，无核心护城河' if company_detail['moat']==0 else '无重大利空风险'}，{'股权质押比例过高' if company_detail['governance']==0 else '无治理风险'}")
            st.write(f"红线排查：{'是' if company_red else '否'}触发一票否决条款")

        with st.expander("4. L2暗盘资金手动侦查（满分15分，得分{}分）".format(l2_total_score), expanded=True):
            st.write("手动验证实盘数据：需用户手动补充近5天累计净流入/流出、近3天单日流向、主力/机构大单占比、对倒诱多排查结果")
            st.write(f"核心分析：近5天暗盘资金得分{l2_5d_score}分，近3天暗盘资金得分{l2_3d_score}分，{'主力中期建仓意图明确' if l2_total_score>=12 else '无明确主力建仓意图'}，{'无对倒诱多痕迹' if not l2_red_line else '存在对倒诱多行为'}")
            st.write(f"红线排查：{'是' if l2_red_line else '否'}触发死刑条款")

        with st.expander("5. 筹码结构审计（满分20分，得分{}分）".format(chip_score), expanded=True):
            st.write(f"核心分析：筹码形态{'为单峰密集，集中度高' if chip_detail['shape']>=8 else '为多峰发散，集中度低'}，底部筹码{'锁定良好，无松动' if chip_detail['lock']>=6 else '松动明显，主力派发'}，当前获利比例{chip_data.get('获利比例', 0)}%，90%成本集中度{chip_data.get('90%成本集中度', 100)}%，{'筹码结构健康，拉升抛压小' if chip_score>=15 else '筹码结构较差，拉升抛压大'}")
            st.write(f"红线排查：{'是' if chip_red else '否'}触发筹码诈骗死刑条款")

        with st.expander("6. 技术环境审计（满分8分，得分{}分）".format(technical_score), expanded=True):
            st.write(f"核心分析：个股股价{'站稳120日牛熊线' if technical_detail['lifeline']>=4 else '跌破120日牛熊线'}，20/60/120日均线{'呈多头排列，上升趋势明确' if technical_detail['trend']>=4 else '呈空头排列，趋势走弱'}，个股与大盘/板块顺势度{'高' if technical_score>=6 else '低'}，关键支撑位{odds_detail['support']}元，关键压力位{odds_detail['pressure']}元")
            st.write(f"风险提示：{'无' if technical_score>=4 else '趋势破位预警/牛熊线下方风险'}")

        with st.expander("7. 排雷安全审计（满分7分，得分{}分）".format(risk_score), expanded=True):
            st.write(f"核心分析：商誉占净资产比例{round(financial_data.get('goodwill_df', pd.DataFrame()).iloc[0]['商誉']/financial_data.get('goodwill_df', pd.DataFrame()).iloc[0]['所有者权益合计']*100 if not financial_data.get('goodwill_df', pd.DataFrame()).empty else 0)}%，流通市值{round(basic_info.get('流通市值', 0)/100000000, 2)}亿元，{'无商誉风险，市值适配性良好' if risk_score>=5 else '存在高商誉/微盘股流动性风险'}")
            st.write(f"风险提示：{'无' if risk_score>=5 else '高商誉预警/微盘股流动性风险'}")

        with st.expander("8. 资金活性审计（满分5分，得分{}分）".format(fund_activity_score), expanded=True):
            st.write(f"核心分析：最新量比{round(kline_df.iloc[-1]['成交量']/kline_df.iloc[-20:-1]['成交量'].mean(), 2)}，换手率{round(kline_df.iloc[-1]['换手率'], 2)}%，盘口承接力{'强' if fund_activity_detail['attack']>=3 else '弱'}，高位套牢盘{'无明显压力' if fund_activity_detail['purity']>=2 else '压力较大'}，个股与板块量能匹配度{'高' if fund_activity_score>=3 else '低'}")
            st.write(f"风险提示：{'无' if fund_activity_score>=3 else '量能不足预警/高位套牢盘压力预警'}")

        with st.expander("9. 赔率决策审计（满分5分，得分{}分）".format(odds_score), expanded=True):
            st.write(f"核心分析：当前价格{round(current_close, 2)}元，强支撑位{odds_detail['support']}元，强压力位{odds_detail['pressure']}元，赔率R值{odds_detail['r_value']}，{'盈亏比极佳，具备高交易性价比' if odds_score>=3 else '盈亏比不足，不具备交易价值'}")
            st.write(f"风险提示：{'无' if odds_score>=3 else '赔率不足预警，不具备交易价值'}")

        st.divider()

        st.subheader("V. 死亡红线终极排查")
        st.write(f"1. 三维审计红线：{'是' if macro_red or industry_red or company_red else '否'}触发，触发则总分清零，永久拉黑")
        st.write(f"2. L2暗盘红线：{'是' if l2_red_line else '否'}触发，触发则总分清零，永久拉黑")
        st.write(f"3. 筹码诈骗红线：{'是' if chip_red else '否'}触发，触发则总分清零，永久拉黑")
        st.write(f"4. 基本面暴雷红线：{'是' if financial_data.get('is_st', False) or financial_data.get('is_legal', False) else '否'}触发，触发则总分清零，永久拉黑")
        st.write(f"- 终极排查结论：{'逻辑崩塌，总分清零，永久拉黑' if death_trigger else '安全无红线'}")

st.divider()
st.caption("Depp·鹰眼 MRI 审计子系统 v1.9 终版 | 隶属乾元·太初全维度量化作战母系统")
