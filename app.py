import streamlit as st
import akshare as ak
import pandas as pd
from datetime import datetime, timedelta

# 页面配置
st.set_page_config(page_title="鹰眼卡片审计", layout="wide", page_icon="📈")
st.title("📈 鹰眼MRI · 股票卡片对比系统（极速版）")

# 全局缓存（极速提速）
@st.cache_data(ttl=600, show_spinner=False)
def get_stock_base(stock_code):
    try:
        info = ak.stock_individual_info_em(symbol=stock_code)
        return dict(zip(info['item'], info['value']))
    except:
        return {"股票简称": stock_code, "总市值": 0}

@st.cache_data(ttl=600, show_spinner=False)
def get_kline(stock_code):
    try:
        end = datetime.now().strftime('%Y%m%d')
        start = (datetime.now()-timedelta(days=120)).strftime('%Y%m%d')
        df = ak.stock_zh_a_hist(symbol=stock_code, period="daily", start=start, end=end, adjust="qfq")
        if len(df) >= 120:
            df['ma20'] = df['收盘'].rolling(20).mean()
            df['ma120'] = df['收盘'].rolling(120).mean()
        return df
    except:
        return pd.DataFrame()

# 极简打分（只算核心，极速）
def fast_score(code, l2_5=8, l2_3=4):
    try:
        info = get_stock_base(code)
        k = get_kline(code)
        
        if len(k) == 0:
            return {
                "name": info.get("股票简称", code),
                "code": code,
                "price": "数据异常",
                "market": "数据异常",
                "score_3d": 0,
                "score_l2": 0,
                "total": 0,
                "cmd": "❌ 数据获取失败",
                "trend": "未知"
            }

        close = round(k.iloc[-1]['收盘'], 2)
        ma120 = k.iloc[-1]['ma120'] if len(k)>=120 else close
        market_cap = round(info.get("总市值", 0)/1e8, 1)

        # 核心三维分（极简）
        macro = 6 if close>ma120 else 2
        industry = 12
        company = 6
        score_3d = macro + industry + company
        score_l2 = l2_5 + l2_3
        total = score_3d + score_l2

        # 指令
        if total < 40: cmd = "❌ 空仓"
        elif total < 60: cmd = "⚠️ 观察"
        elif total < 80: cmd = "🟡 轻仓"
        else: cmd = "🟢 重仓"

        return {
            "name": info.get("股票简称", code),
            "code": code,
            "price": close,
            "market": market_cap,
            "score_3d": score_3d,
            "score_l2": score_l2,
            "total": total,
            "cmd": cmd,
            "trend": "多头" if close>ma120 else "空头"
        }
    except Exception as e:
        return {
            "name": code,
            "code": code,
            "price": "异常",
            "market": "异常",
            "score_3d": 0,
            "score_l2": 0,
            "total": 0,
            "cmd": f"❌ 错误：{str(e)[:20]}",
            "trend": "未知"
        }

# 输入区（批量多股票）
col_in1, col_in2 = st.columns([3,1])
with col_in1:
    codes = st.text_input(
        "批量输入股票代码（逗号分隔）",
        value="002594,600519,601318",
        placeholder="例：002594,600519"
    )
with col_in2:
    st.write("")
    st.write("")
    run = st.button("🚀 一键审计", type="primary", use_container_width=True)

# L2默认值（全局统一）
l2_5_def = 8
l2_3_def = 4

# 卡片网格渲染（纯Streamlit原生，100%兼容）
if run and codes:
    code_list = [i.strip() for i in codes.split(",") if i.strip().isdigit() and len(i)==6]
    
    if not code_list:
        st.warning("请输入正确的6位A股股票代码，用逗号分隔")
        st.stop()

    st.divider()
    st.subheader("📊 多股对比卡片（网格视图）")

    # 显示加载状态
    with st.spinner("正在极速审计中..."):
        # 批量计算所有股票
        all_data = []
        for code in code_list:
            all_data.append(fast_score(code, l2_5_def, l2_3_def))

    # 每行3张卡片
    for i in range(0, len(all_data), 3):
        cols = st.columns(3)
        for j in range(3):
            if i+j < len(all_data):
                data = all_data[i+j]
                with cols[j]:
                    # 纯Streamlit原生卡片
                    with st.container(border=True):
                        st.subheader(f"{data['name']}")
                        st.caption(f"代码：{data['code']}")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("现价", data['price'])
                        with col2:
                            st.metric("市值(亿)", data['market'])

                        st.metric("趋势", data['trend'], 
                                  delta="上涨" if data['trend']=="多头" else "下跌",
                                  delta_color="normal")

                        col3, col4 = st.columns(2)
                        with col3:
                            st.metric("三维得分", data['score_3d'])
                        with col4:
                            st.metric("L2得分", data['score_l2'])

                        st.divider()
                        st.metric("最终总分", data['total'])
                        st.subheader(data['cmd'])

st.divider()
st.caption("⚡ 极速精简版 | 纯原生组件 | 零报错 | 网格对比 | 1秒出结果")
