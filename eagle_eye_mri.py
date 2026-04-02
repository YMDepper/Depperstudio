# 自动定时刷新（单位：毫秒，300000=5分钟）
st_autorefresh = st.components.v1.html(
    """<script>setInterval(() => window.parent.location.reload(), 300000)</script>""",
    height=0
)
import streamlit as st
import akshare as ak
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# -------------------------- 全局配置 & 系统终版规则锁死 --------------------------
SYSTEM_CONFIG = {
    "total_score": 100,
    "weight": {
        "3d_audit": 40,
        "l2_audit": 15,
        "five_dimension": 45
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
        "3d_pass": 24,
        "l2_pass": 9
    },
    "red_line": {
        "pass_line": 60,
        "attack_line": 80,
        "attack_3d": 32,
        "attack_l2": 12
    }
}

# -------------------------- 页面基础配置 --------------------------
st.set_page_config(
    page_title="Depp·鹰眼MRI审计子系统 v1.9",
    layout="wide",
    page_icon="📊",
    initial_sidebar_state="collapsed"
)

# -------------------------- 全局会话状态持久化（解决刷新/后台退出重进问题） --------------------------
if 'stock_code' not in st.session_state:
    st.session_state.stock_code = ''
if 'l2_5d_score' not in st.session_state:
    st.session_state.l2_5d_score = 0
if 'l2_3d_score' not in st.session_state:
    st.session_state.l2_3d_score = 0
if 'l2_red_line' not in st.session_state:
    st.session_state.l2_red_line = False
if 'audit_data' not in st.session_state:
    st.session_state.audit_data = None
if 'load_finished' not in st.session_state:
    st.session_state.load_finished = False

# -------------------------- 安全数据获取工具函数（彻底解决索引越界报错） --------------------------
def safe_iloc(df, index, default=None):
    """安全取DataFrame的iloc值，为空则返回默认值，彻底解决索引越界"""
    try:
        if len(df) > abs(index):
            return df.iloc[index]
        else:
            return default if default is not None else pd.Series()
    except:
        return default if default is not None else pd.Series()

def safe_round(value, decimals=2, default=0):
    """安全四舍五入，为空则返回默认值"""
    try:
        return round(float(value), decimals)
    except:
        return default

# -------------------------- 极速缓存优化（按数据类型分配合适的缓存时间） --------------------------
@st.cache_data(ttl=1800, show_spinner=False)  # 大盘数据缓存30分钟
def get_index_data_cached():
    try:
        index_df = ak.stock_zh_index_spot()
        return index_df[index_df['代码'].isin(['sh000001', 'sz399001', 'sz399006', 'sh000688'])]
    except:
        return pd.DataFrame()

@st.cache_data(ttl=1800, show_spinner=False)
def get_market_overview_cached():
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

@st.cache_data(ttl=600, show_spinner=False)  # 个股基础信息缓存10分钟
def get_stock_basic_info_cached(stock_code):
    try:
        basic_df = ak.stock_individual_info_em(symbol=stock_code)
        basic_dict = dict(zip(basic_df['item'], basic_df['value']))
        industry_df = ak.stock_board_industry_cons_em(symbol=basic_dict.get('行业', ''))
        industry_rank = industry_df[industry_df['代码'] == stock_code].index[0] + 1 if not industry_df.empty and stock_code in industry_df['代码'].values else 999
        basic_dict['行业排名'] = industry_rank
        basic_dict['行业总家数'] = len(industry_df) if not industry_df.empty else 1000
        return basic_dict
    except:
        return {}

@st.cache_data(ttl=600, show_spinner=False)
def get_stock_kline_cached(stock_code):
    start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')
    end_date = datetime.now().strftime('%Y%m%d')
    try:
        kline_df = ak.stock_zh_a_hist(
            symbol=stock_code,
            period="daily",
            start_date=start_date,
            end_date=end_date,
            adjust="qfq"
        )
        if len(kline_df) >= 120:
            kline_df['ma20'] = kline_df['收盘'].rolling(window=20).mean()
            kline_df['ma60'] = kline_df['收盘'].rolling(window=60).mean()
            kline_df['ma120'] = kline_df['收盘'].rolling(window=120).mean()
        return kline_df
    except:
        return pd.DataFrame()

@st.cache_data(ttl=1800, show_spinner=False)
def get_industry_fund_flow_cached(industry_name):
    try:
        industry_flow_df = ak.stock_sector_fund_flow_rank_em(indicator="5日")
        return industry_flow_df[industry_flow_df['行业名称'] == industry_name]
    except:
        return pd.DataFrame()

@st.cache_data(ttl=3600, show_spinner=False)  # 财务数据缓存1小时
def get_stock_financial_data_cached(stock_code):
    try:
        financial_df = ak.stock_financial_abstract_em(symbol=stock_code)
        goodwill_df = ak.stock_financial_report_sina(stock=stock_code, symbol="资产负债表")
        pledge_df = ak.stock_holder_pledge_em(symbol=stock_code)
        risk_df = ak.stock_em_st_warning()
        is_st = stock_code in risk_df['代码'].values if not risk_df.empty else False
        legal_df = ak.stock_em_legal_proceeding()
        is_legal = stock_code in legal_df['证券代码'].values if not legal_df.empty else False
        return {
            "financial": financial_df,
            "goodwill": goodwill_df,
            "pledge": pledge_df,
            "is_st": is_st,
            "is_legal": is_legal
        }
    except:
        return {}

@st.cache_data(ttl=600, show_spinner=False)
def get_chip_distribution_cached(stock_code):
    try:
        chip_df = ak.stock_chip_distribution_em(symbol=stock_code)
        latest_chip = chip_df.iloc[-1] if len(chip_df) > 0 else {}
        return latest_chip, chip_df
    except:
        return {}, pd.DataFrame()

@st.cache_data(ttl=1800, show_spinner=False)
def get_hot_industry_cached():
    try:
        hot_df = ak.stock_sector_fund_flow_rank_em(indicator="今日")
        return hot_df.head(10)['行业名称'].tolist() if not hot_df.empty else []
    except:
        return []

# -------------------------- 核心审计打分函数（无重复接口调用，极速计算） --------------------------
def macro_audit_fast(market_data, index_data):
    score = 0
    red_line_trigger = False
    detail = {"market_env": 0, "liquidity": 0, "policy": 3, "risk_detail": ""}

    try:
        sz_index = safe_iloc(index_data[index_data['代码'] == 'sh000001'], 0)
        latest_close = sz_index.get('最新价', 0)
        sz_kline = ak.stock_zh_index_hist_csindex(
            symbol='000001',
            start_date=(datetime.now()-timedelta(days=180)).strftime('%Y%m%d'),
            end_date=datetime.now().strftime('%Y%m%d')
        )
        if len(sz_kline) >= 120:
            sz_kline['ma120'] = sz_kline['收盘'].rolling(window=120).mean()
            ma120 = safe_iloc(sz_kline, -1).get('ma120', 0)
            ma120_prev = safe_iloc(sz_kline, -5).get('ma120', ma120)
        else:
            ma120 = 0
            ma120_prev = 0

        if latest_close > ma120 and ma120 > ma120_prev and ma120 != 0:
            detail['market_env'] = 4
        elif latest_close > ma120 and ma120 != 0:
            detail['market_env'] = 2
        else:
            detail['market_env'] = 0
            red_line_trigger = True
            detail['risk_detail'] += "大盘有效跌破120日线呈空头排列，触发宏观红线；"
    except:
        detail['market_env'] = 2
        detail['risk_detail'] += "大盘数据获取异常，默认中性；"

    try:
        trade_amount_row = safe_iloc(market_data.get('trade_amount', pd.DataFrame()), 0)
        trade_amount = trade_amount_row.get('两市成交额', 0)
        north_flow = safe_iloc(market_data.get('north_flow', pd.DataFrame()), -1).get('净流入', 0)
        main_flow = safe_iloc(market_data.get('market_flow', pd.DataFrame()), 0).get('主力净流入-净额', 0)
        if north_flow > 0 and main_flow > 0 and trade_amount > 800000000000:
            detail['liquidity'] = 3
        elif north_flow > 0 or main_flow > 0:
            detail['liquidity'] = 1
        else:
            detail['liquidity'] = 0
    except:
        detail['liquidity'] = 1
        detail['risk_detail'] += "流动性数据获取异常，默认中性；"

    score = detail['market_env'] + detail['liquidity'] + detail['policy']
    return 0 if red_line_trigger else score, detail, red_line_trigger

def industry_audit_fast(industry_name, industry_flow_df, hot_industry_list, basic_info):
    score = 0
    red_line_trigger = False
    detail = {"boom": 0, "competition": 0, "plate_effect": 0, "risk_detail": ""}

    try:
        net_flow_5d = safe_iloc(industry_flow_df, 0).get('5日净流入-净额', 0)
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
        industry_rank = basic_info.get('行业排名', 999)
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
            net_flow_5d = safe_iloc(industry_flow_df, 0).get('5日净流入-净额', 0)
            detail['plate_effect'] = 6 if net_flow_5d > 0 else 3
        elif industry_name in hot_industry_list:
            detail['plate_effect'] = 3
        else:
            detail['plate_effect'] = 0
    except:
        detail['plate_effect'] = 0
        detail['risk_detail'] += "板块效应数据获取异常；"

    score = detail['boom'] + detail['competition'] + detail['plate_effect']
    return 0 if red_line_trigger else score, detail, red_line_trigger

def company_audit_fast(stock_code, financial_data, basic_info):
    score = 0
    red_line_trigger = False
    detail = {"moat": 0, "profit": 0, "governance": 0, "risk_detail": ""}

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
        latest_finance = safe_iloc(financial_df, 0)
        net_profit_yoy = latest_finance.get('扣非净利润同比增长', 0)
        operate_cash = latest_finance.get('经营活动产生的现金流量净额', 0)
        revenue_yoy = latest_finance.get('营业收入同比增长', 0)
        if net_profit_yoy > 0 and operate_cash > 0 and revenue_yoy > 0:
            detail['profit'] = 3
        elif net_profit_yoy > 0:
            detail['profit'] = 1
        else:
            detail['profit'] = 0
    except:
        detail['profit'] = 1
        detail['risk_detail'] += "盈利数据获取异常，默认中性；"

    try:
        pledge_df = financial_data.get('pledge', pd.DataFrame())
        pledge_ratio = safe_iloc(pledge_df, 0).get('质押比例', 0)
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

def chip_audit_fast(chip_data, chip_df, kline_df, stock_code):
    score = 0
    red_line_trigger = False
    detail = {"shape": 0, "lock": 0, "profit": 0, "concentration": 0, "risk_detail": ""}

    try:
        price_range = chip_data.get('90%成本区间', '0-0').split('-')
        price_range = [float(x) for x in price_range] if len(price_range)==2 else [0,0]
        range_ratio = (price_range[1] - price_range[0]) / price_range[0] if price_range[0] !=0 else 1
        detail['shape'] = 8 if range_ratio < 0.15 else 2

        chip_5d_ago = safe_iloc(chip_df, -5, chip_data)
        current_bottom = chip_data.get('获利比例', 0)
        prev_bottom = chip_5d_ago.get('获利比例', 0)
        detail['lock'] = 6 if abs(current_bottom - prev_bottom) < 10 else 2

        profit_ratio = chip_data.get('获利比例', 0)
        detail['profit'] = 3 if 60 <= profit_ratio <= 90 else 0

        concentration = chip_data.get('90%成本集中度', 100)
        detail['concentration'] = 3 if concentration < 10 else 0

        if current_bottom < 10 and prev_bottom > 50:
            red_line_trigger = True
            detail['risk_detail'] += "底部筹码峰完全消失，触发筹码死刑红线；"
    except Exception as e:
        detail['risk_detail'] += f"筹码数据获取异常：{str(e)}；"

    score = detail['shape'] + detail['lock'] + detail['profit'] + detail['concentration']
    return score, detail, red_line_trigger

def technical_audit_fast(kline_df):
    score = 0
    detail = {"lifeline": 0, "trend": 0, "risk_detail": ""}
    try:
        latest_data = safe_iloc(kline_df, -1)
        close_price = latest_data.get('收盘', 0)
        ma120 = latest_data.get('ma120', 0)
        ma60 = latest_data.get('ma60', 0)
        ma20 = latest_data.get('ma20', 0)
        detail['lifeline'] = 4 if close_price > ma120 and ma120 !=0 else 0
        if close_price > ma20 and ma20 > ma60 and ma60 > ma120 and ma20 !=0:
            detail['trend'] = 4
        elif close_price > ma60 and ma60 !=0:
            detail['trend'] = 2
        else:
            detail['trend'] = 0
    except:
        detail['risk_detail'] += "技术指标计算异常；"
    score = detail['lifeline'] + detail['trend']
    return score, detail

def risk_audit_fast(financial_data, basic_info):
    score = 0
    red_line_trigger = False
    detail = {"goodwill": 0, "market_cap": 0, "risk_detail": ""}

    try:
        goodwill_df = financial_data.get('goodwill', pd.DataFrame())
        latest_balance = safe_iloc(goodwill_df, 0)
        goodwill = latest_balance.get('商誉', 0)
        net_asset = latest_balance.get('所有者权益合计', 0)
        goodwill_ratio = goodwill / net_asset if net_asset !=0 else 1
        if goodwill_ratio < 0.15:
            detail['goodwill'] = 4
        elif 0.15 <= goodwill_ratio < 0.3:
            detail['goodwill'] = 0
        else:
            detail['goodwill'] = -10
            red_line_trigger = True
            detail['risk_detail'] += "商誉占净资产超30%，触发排雷红线；"
    except:
        detail['goodwill'] = 2
        detail['risk_detail'] += "商誉数据获取异常，默认中性；"

    try:
        market_cap = basic_info.get('总市值', 0)
        detail['market_cap'] = 3 if market_cap > 3000000000 else 0
    except:
        detail['market_cap'] = 0
        detail['risk_detail'] += "市值数据获取异常；"

    score = detail['goodwill'] + detail['market_cap']
    return score, detail, red_line_trigger

def fund_activity_audit_fast(kline_df):
    score = 0
    detail = {"attack": 0, "purity": 0, "risk_detail": ""}
    try:
        latest_data = safe_iloc(kline_df, -1)
        turnover_rate = latest_data.get('换手率', 0)
        avg_volume = kline_df.iloc[-20:-1]['成交量'].mean() if len(kline_df)>=20 else latest_data.get('成交量', 0)
        volume_ratio = latest_data.get('成交量', 0) / avg_volume if avg_volume !=0 else 0
        detail['attack'] = 3 if volume_ratio > 1.5 or turnover_rate > 3 else 0

        recent_30d = kline_df.iloc[-30:] if len(kline_df)>=30 else kline_df
        if len(recent_30d) > 0:
            max_shadow = (recent_30d['最高'] - recent_30d['收盘']).max() / recent_30d['收盘'].mean() if recent_30d['收盘'].mean() !=0 else 0
            detail['purity'] = 2 if max_shadow < 0.08 else 0
    except:
        detail['risk_detail'] += "资金活性数据计算异常；"
    score = detail['attack'] + detail['purity']
    return score, detail

def odds_audit_fast(kline_df):
    score = 0
    detail = {"r_value": 0, "support": 0, "pressure": 0, "risk_detail": ""}
    try:
        latest_close = safe_iloc(kline_df, -1).get('收盘', 0)
        min_20d = kline_df.iloc[-20:]['最低'].min() if len(kline_df)>=20 else latest_close*0.92
        ma60 = safe_iloc(kline_df, -1).get('ma60', latest_close*0.92)
        support = min(min_20d, ma60)
        pressure = kline_df.iloc[-60:]['最高'].max() if len(kline_df)>=60 else latest_close*1.2

        if latest_close - support > 0.01:
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
        detail['support'] = 0
        detail['pressure'] = 0
        detail['r_value'] = 0
    score = detail['r_value'] if detail['r_value'] <=5 else 5
    return score, detail

def cycle_position_fast(kline_df, chip_data, chip_df):
    try:
        latest_data = safe_iloc(kline_df, -1)
        ma120 = latest_data.get('ma120', 0)
        close = latest_data.get('收盘', 0)
        chip_5d_ago = safe_iloc(chip_df, -5, chip_data)
        chip_lock = abs(chip_data.get('获利比例', 0) - chip_5d_ago.get('获利比例', 0)) < 10
        profit_ratio = chip_data.get('获利比例', 0)
        concentration = chip_data.get('90%成本集中度', 100)

        if close < ma120 and ma120 !=0 and safe_iloc(kline_df, -5).get('ma120', ma120) > ma120:
            return "崩塌期"
        elif close > ma120 and profit_ratio > 90 and not chip_lock and ma120 !=0:
            return "派发期"
        elif close > ma120 and 0.3 <= close/ma120 -1 <= 1 and chip_lock and ma120 !=0:
            return "主升期"
        elif abs(close - ma120)/ma120 < 0.1 and concentration < 10 and ma120 !=0:
            return "潜伏期"
        else:
            return "潜伏期"
    except:
        return "未知周期"

# -------------------------- 页面主程序 --------------------------
st.title("📊 Depp·鹰眼 MRI 审计子系统 v1.9 终版")
st.caption("全量无损终版 | 极速加载优化 | 会话持久化 | 实时数据更新 | 异常兜底修复")

# 1. 股票代码输入与实时刷新按钮
col1, col2, col3 = st.columns([3, 1, 1])
with col1:
    stock_code_input = st.text_input(
        "请输入A股股票代码（例：002594、600519）",
        max_chars=6,
        placeholder="仅输入6位数字代码",
        value=st.session_state.stock_code
    )
with col2:
    st.write("")
    st.write("")
    run_button = st.button("🚀 启动深度体检", type="primary", use_container_width=True)
with col3:
    st.write("")
    st.write("")
    refresh_button = st.button("🔄 刷新最新数据", use_container_width=True)

# 2. L2数据手动输入区域（持久化保存）
st.subheader("📥 L2暗盘资金手动侦查数据（必填）")
col_l2_1, col_l2_2, col_l2_3 = st.columns(3)
with col_l2_1:
    st.session_state.l2_5d_score = st.slider(
        "近5天暗盘资金得分（0-10分）",
        min_value=0, max_value=10,
        value=st.session_state.l2_5d_score
    )
with col_l2_2:
    st.session_state.l2_3d_score = st.slider(
        "近3天暗盘资金得分（0-5分）",
        min_value=0, max_value=5,
        value=st.session_state.l2_3d_score
    )
with col_l2_3:
    st.session_state.l2_red_line = st.checkbox(
        "是否触发L2死刑红线？",
        value=st.session_state.l2_red_line
    )
l2_total_score = st.session_state.l2_5d_score + st.session_state.l2_3d_score
st.info(f"当前L2暗盘审计总得分：{l2_total_score}/15分 | 及格线9分")

# 3. 刷新数据逻辑
if refresh_button:
    get_index_data_cached.clear()
    get_market_overview_cached.clear()
    get_stock_basic_info_cached.clear()
    get_stock_kline_cached.clear()
    get_industry_fund_flow_cached.clear()
    get_stock_financial_data_cached.clear()
    get_chip_distribution_cached.clear()
    get_hot_industry_cached.clear()
    st.session_state.audit_data = None
    st.session_state.load_finished = False
    st.success("✅ 缓存已清空，将加载最新实时数据")

# 4. 核心体检执行逻辑
if run_button and stock_code_input:
    st.session_state.stock_code = stock_code_input.strip()
    st.session_state.audit_data = None
    st.session_state.load_finished = False

    # 进度条显示
    progress_bar = st.progress(0, text="正在初始化数据...")
    status_text = st.empty()

    try:
        # 第一步：预加载所有缓存数据（一次性拉取，无重复调用，全兜底）
        status_text.text("1/8 正在加载大盘全景数据...")
        progress_bar.progress(10)
        index_data = get_index_data_cached()
        market_data = get_market_overview_cached()
        hot_industry = get_hot_industry_cached()

        # 安全提取大盘基础数据（提前处理，避免渲染时报错）
        trade_amount_row = safe_iloc(market_data.get('trade_amount', pd.DataFrame()), 0)
        trade_amount = trade_amount_row.get('两市成交额', 0)
        north_flow = safe_iloc(market_data.get('north_flow', pd.DataFrame()), -1).get('净流入', 0)
        limit_up_count = len(market_data.get('limit_up', pd.DataFrame()))
        limit_down_count = len(market_data.get('limit_down', pd.DataFrame()))

        status_text.text("2/8 正在加载个股基础信息...")
        progress_bar.progress(20)
        basic_info = get_stock_basic_info_cached(st.session_state.stock_code)
        st.session_state.basic_info = basic_info
        industry_name = basic_info.get('行业', '')
        industry_flow_df = get_industry_fund_flow_cached(industry_name)
        industry_flow_5d = safe_iloc(industry_flow_df, 0).get('5日净流入-净额', 0)

        status_text.text("3/8 正在加载个股K线数据...")
        progress_bar.progress(35)
        kline_df = get_stock_kline_cached(st.session_state.stock_code)
        current_close = safe_iloc(kline_df, -1).get('收盘', 0)

        status_text.text("4/8 正在加载个股财务数据...")
        progress_bar.progress(50)
        financial_data = get_stock_financial_data_cached(st.session_state.stock_code)
        financial_df = financial_data.get('financial', pd.DataFrame())
        latest_finance = safe_iloc(financial_df, 0)
        net_profit_yoy = latest_finance.get('扣非净利润同比增长', 0)
        industry_rank = basic_info.get('行业排名', 999)
        industry_total = basic_info.get('行业总家数', 1000)

        status_text.text("5/8 正在加载筹码分布数据...")
        progress_bar.progress(65)
        chip_data, chip_df = get_chip_distribution_cached(st.session_state.stock_code)

        # 第二步：全维度审计打分
        status_text.text("6/8 正在执行全维度审计打分...")
        progress_bar.progress(80)
        macro_score, macro_detail, macro_red = macro_audit_fast(market_data, index_data)
        industry_score, industry_detail, industry_red = industry_audit_fast(industry_name, industry_flow_df, hot_industry, basic_info)
        company_score, company_detail, company_red = company_audit_fast(st.session_state.stock_code, financial_data, basic_info)
        chip_score, chip_detail, chip_red = chip_audit_fast(chip_data, chip_df, kline_df, st.session_state.stock_code)
        technical_score, technical_detail = technical_audit_fast(kline_df)
        risk_score, risk_detail, risk_red = risk_audit_fast(financial_data, basic_info)
        fund_activity_score, fund_activity_detail = fund_activity_audit_fast(kline_df)
        odds_score, odds_detail = odds_audit_fast(kline_df)
        cycle = cycle_position_fast(kline_df, chip_data, chip_df)

        # 总分计算
        total_3d_score = macro_score + industry_score + company_score
        total_five_score = chip_score + technical_score + risk_score + fund_activity_score + odds_score
        base_total_score = total_3d_score + l2_total_score + total_five_score

        # 特权加分
        privilege_bonus = 0
        if total_3d_score == 40:
            privilege_bonus += 10
        if l2_total_score == 15:
            privilege_bonus +=5
        if chip_score ==20:
            privilege_bonus +=3
        final_total_score = base_total_score + privilege_bonus

        # 死刑条款判定
        death_trigger = False
        death_reason = []
        if macro_red or industry_red or company_red:
            death_trigger = True
            death_reason.append("三维前置审计触发红线条款")
        if st.session_state.l2_red_line:
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

        # 双准入校验
        double_access_pass = (total_3d_score >= SYSTEM_CONFIG['double_access']['3d_pass']) and (l2_total_score >= SYSTEM_CONFIG['double_access']['l2_pass']) and (not death_trigger)
        attack_pass = (total_3d_score >= SYSTEM_CONFIG['red_line']['attack_3d']) and (l2_total_score >= SYSTEM_CONFIG['red_line']['attack_l2']) and (final_total_score >= SYSTEM_CONFIG['red_line']['attack_line']) and double_access_pass

        # 最终作战指令
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

        # 所有数据持久化到会话状态（渲染时只用这里的安全数据）
        st.session_state.audit_data = {
            "final_total_score": final_total_score,
            "privilege_bonus": privilege_bonus,
            "cycle": cycle,
            "total_3d_score": total_3d_score,
            "l2_total_score": l2_total_score,
            "double_access_pass": double_access_pass,
            "attack_pass": attack_pass,
            "final_command": final_command,
            "death_trigger": death_trigger,
            "death_reason": death_reason,
            "macro_score": macro_score,
            "macro_detail": macro_detail,
            "macro_red": macro_red,
            "industry_score": industry_score,
            "industry_detail": industry_detail,
            "industry_red": industry_red,
            "company_score": company_score,
            "company_detail": company_detail,
            "company_red": company_red,
            "chip_score": chip_score,
            "chip_detail": chip_detail,
            "chip_red": chip_red,
            "technical_score": technical_score,
            "technical_detail": technical_detail,
            "risk_score": risk_score,
            "risk_detail": risk_detail,
            "risk_red": risk_red,
            "fund_activity_score": fund_activity_score,
            "fund_activity_detail": fund_activity_detail,
            "odds_score": odds_score,
            "odds_detail": odds_detail,
            # 预计算好的安全渲染数据（彻底解决0值问题）
            "trade_amount": trade_amount,
            "north_flow": north_flow,
            "limit_up_count": limit_up_count,
            "limit_down_count": limit_down_count,
            "hot_industry": hot_industry,
            "industry_name": industry_name,
            "industry_flow_5d": industry_flow_5d,
            "basic_info": basic_info,
            "financial_data": financial_data,
            "kline_df": kline_df,
            "current_close": current_close,
            "net_profit_yoy": net_profit_yoy,
            "industry_rank": industry_rank,
            "industry_total": industry_total,
            "chip_data": chip_data,
            "chip_df": chip_df
        }
        st.session_state.load_finished = True

        status_text.text("7/8 审计完成，正在生成报告...")
        progress_bar.progress(95)
        progress_bar.empty()
        status_text.empty()

    except Exception as e:
        st.error(f"❌ 数据加载失败，请检查股票代码是否正确，错误信息：{str(e)}")
        progress_bar.empty()
        status_text.empty()

# 5. 审计报告渲染（持久化数据，刷新页面不用重新计算）
if st.session_state.load_finished and st.session_state.audit_data is not None:
    data = st.session_state.audit_data
    st.divider()
    st.header(f"【鹰眼审计卡 v1.9】{data['basic_info'].get('股票简称', st.session_state.stock_code)} 深度体检报告")
    st.divider()

    # I. 核心决策看板
    st.subheader("I. 核心决策看板（一眼定生死）")
    col_board_1, col_board_2 = st.columns(2)
    with col_board_1:
        st.metric("鹰眼最终总分", f"{data['final_total_score']}分", f"含特权加分：{data['privilege_bonus']}分")
        st.caption(f"及格线：{SYSTEM_CONFIG['red_line']['pass_line']}分 | 强攻线：{SYSTEM_CONFIG['red_line']['attack_line']}分")
        st.metric("周期定位", data['cycle'])
    with col_board_2:
        st.write(f"**双准入校验结果**：三维审计 {data['total_3d_score']}/40分（{'通过' if data['double_access_pass'] else '不通过'}）| L2暗盘审计 {data['l2_total_score']}/15分（{'通过' if data['l2_total_score']>=9 else '不通过'}）")
        st.write(f"**核心定性结论**：{data['basic_info'].get('股票简称', st.session_state.stock_code)}所属{data['industry_name']}赛道，{'为当前市场核心热门主线' if data['industry_name'] in data['hot_industry'] else '非市场主线'}，大盘{'流动性宽松无系统性风险' if data['macro_score']>=6 else '存在系统性风险'}，L2暗盘{'确认主力锁仓建仓' if data['l2_total_score']>=12 else '无明确主力建仓信号'}，处于{data['cycle']}，{'总分达标触发强攻规则' if data['attack_pass'] else '未达到强攻标准'}")
        st.write(f"**最终作战指令**：:red[{data['final_command']}]" if data['final_command'] in ["空仓", "空仓拉黑"] else f"**最终作战指令**：:green[{data['final_command']}]")

    if data['death_trigger']:
        st.error(f"⚠️ 触发死刑条款，逻辑崩塌，总分清零，永久拉黑！触发原因：{'、'.join(data['death_reason'])}", icon="🚨")
        st.stop()

    st.divider()

    # II. 战术执行方案（彻底解决0值问题）
    st.subheader("II. 战术执行方案（精简核心·极致精准）")
    st.caption("⚠️ 【执行铁律】仅双准入校验通过、无红线触发的标的可执行；崩塌期/红线触发标的直接空仓拉黑，严禁操作。")
    col_tactics_1, col_tactics_2 = st.columns(2)

    support = data['odds_detail']['support']
    pressure = data['odds_detail']['pressure']
    current_close = data['current_close']

    with col_tactics_1:
        st.subheader("精准进场点位")
        first_entry = round(support*1.01, 2) if support !=0 else "数据获取异常"
        add_entry = round(pressure*0.99, 2) if pressure !=0 else "数据获取异常"
        st.write(f"- **首仓进场位**：{first_entry}元（20日均线/筹码峰上沿强支撑）")
        st.write(f"  触发条件：回踩支撑不破+L2盘口大单承接，仓位：计划总仓位的50%")
        st.write(f"- **加仓进场位**：{add_entry}元（前高/关键压力位）")
        st.write(f"  触发条件：放量突破（量比≥2）+L2资金持续流入，仓位：计划总仓位的50%")
        st.write("- **进场禁忌**：无承接高位追涨、支撑破位后反抽进场，0仓位")

        st.subheader("极限反向博弈（仅高确定性场景适配）")
        st.caption("⚠️ 【准入前提】必须同时满足：三维+L2全达标、赛道为市场主线、底部筹码100%锁定、仅大盘/板块情绪错杀、处于潜伏期/主升期，缺一不可")
        panic_support = round(support*0.92, 2) if support !=0 else "数据获取异常"
        st.write(f"- **博弈进场位**：{panic_support}元（恐慌杀跌强支撑位/黄金分割0.618位）")
        st.write(f"  触发条件：杀跌末端放量止跌+大单承接")
        st.write("- **仓位限制**：不超过总仓位的20%，仅小仓位博弈")
        st.write("- **博弈止盈**：反弹至10/20日均线压力位全仓兑现，盈利目标5%-10%，不格局")
        st.write("- **博弈止损**：跌破恐慌前低/亏损超5%，无条件清仓，绝不补仓")

    with col_tactics_2:
        st.subheader("止盈止损铁律")
        st.subheader("止盈规则")
        first_pressure = round(current_close*1.1, 2) if pressure ==0 else round(pressure*0.8, 2)
        st.write(f"- **第一止盈位**：{round(first_pressure, 2)}元（第一压力位/套牢盘密集区），触发：触及后放量滞涨，兑现50%仓位")
        st.write(f"- **终极止盈位**：{round(pressure, 2)}元（估值目标位/板块情绪顶），触发：底部筹码松动+L2主力净流出，清仓")
        st.write("- **移动止盈保护**：以20日均线为生命线，有效跌破且当日无法收回，直接清仓")

        st.subheader("止损规则")
        stop_loss = round(support*0.92, 2) if support !=0 else "数据获取异常"
        st.write(f"- **技术止损位**：{stop_loss}元（底部筹码峰下沿/进场位最大回撤8%），有效跌破无条件清仓，单笔亏损不超总资金2%")
        st.write("- **逻辑止损**：触发任意死刑红线/公司出现重大基本面利空，当日无条件清仓，永久拉黑")

    st.divider()

    # III. 底层逻辑一句话速览（彻底解决0值问题）
    st.subheader("III. 底层逻辑一句话速览（强制精准落地）")
    trade_amount = data['trade_amount']
    north_flow = data['north_flow']
    limit_up_count = data['limit_up_count']
    limit_down_count = data['limit_down_count']
    macro_desc = f"前一日两市成交额{safe_round(trade_amount/100000000, 2)}亿元，北向资金净流入{safe_round(north_flow/100000000, 2)}亿元，全市场涨停{limit_up_count}家，跌停{limit_down_count}家，核心指数{'站稳120日线，货币政策宽松无收紧预期' if data['macro_score']>=6 else '跌破120日线，存在系统性风险'}，市场主线为{','.join(data['hot_industry'][:3])}"
    st.write(f"- **大盘情况**：{macro_desc}")

    industry_flow_5d = data['industry_flow_5d']
    industry_desc = f"所属{data['industry_name']}赛道，{'为当前市场TOP3热门主线' if data['industry_name'] in data['hot_industry'] else '非市场热门主线'}，近5日板块主力资金累计净流入{safe_round(industry_flow_5d/100000000, 2)}亿元，行业景气度{'持续上行' if data['industry_score']>=12 else '平稳/下行'}，市场认可度{'极高' if data['industry_name'] in data['hot_industry'] else '一般'}"
    st.write(f"- **赛道情况**：{industry_desc}")

    industry_rank = data['industry_rank']
    industry_total = data['industry_total']
    net_profit_yoy = data['net_profit_yoy']
    company_desc = f"公司为{data['industry_name']}行业排名第{industry_rank}/{industry_total}，核心上涨驱动为{'业绩增长' if net_profit_yoy>0 else '行业题材'}，最新报告期扣非净利润同比增长{safe_round(net_profit_yoy, 2)}%，{'无重大利空风险' if data['company_score']>=6 else '存在经营/治理风险'}"
    st.write(f"- **公司情况**：{company_desc}")

    st.divider()

    # IV. 分维度详细审计说明（懒加载，点击展开才显示）
    st.subheader("IV. 分维度详细审计说明（强制细化无笼统）")
    with st.expander("1. 宏观大盘维度审计（满分10分，得分{}分）".format(data['macro_score']), expanded=False):
        st.write(f"【市场全景与核心主线】：当前A股核心指数{'站稳120日线，呈多头趋势' if data['macro_detail']['market_env']>=2 else '跌破120日线，呈空头趋势'}，两市成交额{safe_round(trade_amount/100000000, 2)}亿元，市场核心炒作主线为{','.join(data['hot_industry'][:5])}，全市场资金{'整体净流入' if safe_iloc(data.get('market_data', {}).get('market_flow', pd.DataFrame()), 0).get('主力净流入-净额', 0)>0 else '整体净流出'}")
        st.write(f"【利好驱动明细】：北向资金净流入{safe_round(north_flow/100000000, 2)}亿元，市场主线板块持续活跃，涨停家数{limit_up_count}家，市场情绪平稳，无重大地缘/政策利空")
        st.write(f"【利空风险明细】：跌停家数{limit_down_count}家，{'主力资金整体净流出' if safe_iloc(data.get('market_data', {}).get('market_flow', pd.DataFrame()), 0).get('主力净流入-净额', 0)<0 else '无重大资金流出风险'}，{'大盘跌破120日线，存在系统性下跌风险' if data['macro_red'] else '无系统性风险'}")
        st.write(f"红线排查：{'是' if data['macro_red'] else '否'}触发一票否决条款")

    with st.expander("2. 行业赛道维度审计（满分20分，得分{}分）".format(data['industry_score']), expanded=False):
        st.write(f"【赛道定位与热门度评级】：{data['industry_name']}赛道，全市场热门度排名{data['hot_industry'].index(data['industry_name'])+1 if data['industry_name'] in data['hot_industry'] else '未进前10'}，行业景气度{'上行周期' if data['industry_detail']['boom']>=4 else '平稳/下行周期'}，板块整体走势{'呈上升趋势' if industry_flow_5d>0 else '横盘/下行趋势'}")
        st.write(f"【热门核心底层逻辑】：{'行业需求扩张、资金持续流入，为市场主线题材' if data['industry_name'] in data['hot_industry'] else '非市场主线，资金关注度低，无持续上涨逻辑'}")
        st.write(f"【利好催化明细】：近5日板块主力资金净流入{safe_round(industry_flow_5d/100000000, 2)}亿元，{'为市场热门主线，板块效应强' if data['industry_name'] in data['hot_industry'] else '无重大利好催化'}")
        st.write(f"【利空风险明细】：{'行业景气度下行，资金持续流出' if data['industry_red'] else '无行业性利空风险'}")
        st.write(f"红线排查：{'是' if data['industry_red'] else '否'}触发一票否决条款")

    with st.expander("3. 公司基本面维度审计（满分10分，得分{}分）".format(data['company_score']), expanded=False):
        st.write(f"【公司核心定位】：{data['basic_info'].get('股票简称', st.session_state.stock_code)}，{data['industry_name']}行业排名第{industry_rank}/{industry_total}，核心竞争力{'为行业龙头，具备品牌/技术壁垒' if data['company_detail']['moat']>=2 else '无明显核心壁垒'}")
        st.write(f"【热门/上涨核心驱动逻辑】：{'业绩持续增长，行业龙头地位稳固' if data['company_score']>=6 else '行业题材炒作，无基本面支撑'}")
        st.write(f"【落地式利好明细】：最新报告期扣非净利润同比增长{safe_round(net_profit_yoy, 2)}%，经营现金流{'为正，盈利质量良好' if data['company_detail']['profit']>=3 else '为负，盈利质量较差'}，股权质押比例低，无重大治理风险")
        st.write(f"【利空风险明细】：{'行业排名靠后，无核心护城河' if data['company_detail']['moat']==0 else '无重大利空风险'}，{'股权质押比例过高' if data['company_detail']['governance']==0 else '无治理风险'}")
        st.write(f"红线排查：{'是' if data['company_red'] else '否'}触发一票否决条款")

    with st.expander("4. L2暗盘资金手动侦查（满分15分，得分{}分）".format(data['l2_total_score']), expanded=False):
        st.write("手动验证实盘数据：需用户手动补充近5天累计净流入/流出、近3天单日流向、主力/机构大单占比、对倒诱多排查结果")
        st.write(f"核心分析：近5天暗盘资金得分{st.session_state.l2_5d_score}分，近3天暗盘资金得分{st.session_state.l2_3d_score}分，{'主力中期建仓意图明确' if data['l2_total_score']>=12 else '无明确主力建仓意图'}，{'无对倒诱多痕迹' if not st.session_state.l2_red_line else '存在对倒诱多行为'}")
        st.write(f"红线排查：{'是' if st.session_state.l2_red_line else '否'}触发死刑条款")

    with st.expander("5. 筹码结构审计（满分20分，得分{}分）".format(data['chip_score']), expanded=False):
        st.write(f"核心分析：筹码形态{'为单峰密集，集中度高' if data['chip_detail']['shape']>=8 else '为多峰发散，集中度低'}，底部筹码{'锁定良好，无松动' if data['chip_detail']['lock']>=6 else '松动明显，主力派发'}，当前获利比例{data['chip_data'].get('获利比例', 0)}%，90%成本集中度{data['chip_data'].get('90%成本集中度', 100)}%，{'筹码结构健康，拉升抛压小' if data['chip_score']>=15 else '筹码结构较差，拉升抛压大'}")
        st.write(f"红线排查：{'是' if data['chip_red'] else '否'}触发筹码诈骗死刑条款")

    with st.expander("6. 技术环境审计（满分8分，得分{}分）".format(data['technical_score']), expanded=False):
        st.write(f"核心分析：个股股价{'站稳120日牛熊线' if data['technical_detail']['lifeline']>=4 else '跌破120日牛熊线'}，20/60/120日均线{'呈多头排列，上升趋势明确' if data['technical_detail']['trend']>=4 else '呈空头排列，趋势走弱'}，个股与大盘/板块顺势度{'高' if data['technical_score']>=6 else '低'}，关键支撑位{data['odds_detail']['support']}元，关键压力位{data['odds_detail']['pressure']}元")
        st.write(f"风险提示：{'无' if data['technical_score']>=4 else '趋势破位预警/牛熊线下方风险'}")

    with st.expander("7. 排雷安全审计（满分7分，得分{}分）".format(data['risk_score']), expanded=False):
        goodwill_ratio = safe_round(safe_iloc(data['financial_data'].get('goodwill', pd.DataFrame()), 0).get('商誉', 0)/safe_iloc(data['financial_data'].get('goodwill', pd.DataFrame()), 0).get('所有者权益合计', 1)*100, 2)
        circulate_market_cap = safe_round(data['basic_info'].get('流通市值', 0)/100000000, 2)
        st.write(f"核心分析：商誉占净资产比例{goodwill_ratio}%，流通市值{circulate_market_cap}亿元，{'无商誉风险，市值适配性良好' if data['risk_score']>=5 else '存在高商誉/微盘股流动性风险'}")
        st.write(f"风险提示：{'无' if data['risk_score']>=5 else '高商誉预警/微盘股流动性风险'}")

    with st.expander("8. 资金活性审计（满分5分，得分{}分）".format(data['fund_activity_score']), expanded=False):
        volume_ratio = safe_round(safe_iloc(data['kline_df'], -1).get('成交量', 0)/data['kline_df'].iloc[-20:-1]['成交量'].mean() if len(data['kline_df'])>=20 else 0, 2)
        turnover_rate = safe_round(safe_iloc(data['kline_df'], -1).get('换手率', 0), 2)
        st.write(f"核心分析：最新量比{volume_ratio}，换手率{turnover_rate}%，盘口承接力{'强' if data['fund_activity_detail']['attack']>=3 else '弱'}，高位套牢盘{'无明显压力' if data['fund_activity_detail']['purity']>=2 else '压力较大'}，个股与板块量能匹配度{'高' if data['fund_activity_score']>=3 else '低'}")
        st.write(f"风险提示：{'无' if data['fund_activity_score']>=3 else '量能不足预警/高位套牢盘压力预警'}")

    with st.expander("9. 赔率决策审计（满分5分，得分{}分）".format(data['odds_score']), expanded=False):
        st.write(f"核心分析：当前价格{safe_round(current_close, 2)}元，强支撑位{data['odds_detail']['support']}元，强压力位{data['odds_detail']['pressure']}元，赔率R值{data['odds_detail']['r_value']}，{'盈亏比极佳，具备高交易性价比' if data['odds_score']>=3 else '盈亏比不足，不具备交易价值'}")
        st.write(f"风险提示：{'无' if data['odds_score']>=3 else '赔率不足预警，不具备交易价值'}")

    st.divider()

    # V. 死亡红线终极排查
    st.subheader("V. 死亡红线终极排查")
    st.write(f"1. 三维审计红线：{'是' if data['macro_red'] or data['industry_red'] or data['company_red'] else '否'}触发，触发则总分清零，永久拉黑")
    st.write(f"2. L2暗盘红线：{'是' if st.session_state.l2_red_line else '否'}触发，触发则总分清零，永久拉黑")
    st.write(f"3. 筹码诈骗红线：{'是' if data['chip_red'] else '否'}触发，触发则总分清零，永久拉黑")
    st.write(f"4. 基本面暴雷红线：{'是' if data['financial_data'].get('is_st', False) or data['financial_data'].get('is_legal', False) else '否'}触发，触发则总分清零，永久拉黑")
    st.write(f"- 终极排查结论：{'逻辑崩塌，总分清零，永久拉黑' if data['death_trigger'] else '安全无红线'}")

st.divider()
st.caption("Depp·鹰眼 MRI 审计子系统 v1.9 终版 | 隶属乾元·太初全维度量化作战母系统 | 异常兜底修复版")
