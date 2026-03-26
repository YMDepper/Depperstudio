import streamlit as st
import requests
import pandas as pd
import time

# 页面基础配置
st.set_page_config(page_title="专属实时监控", page_icon="📈", layout="wide")

# 强制注入 CSS 样式：修正后的参数名 unsafe_allow_html
st.markdown("""
    <style>
    [data-testid="stMetricDelta"] svg { display: none; }
    div[data-testid="stMetric"] { background-color: #f0f2f6; padding: 10px; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("📈 破军·实时监控系统")

# --- 侧边栏 ---
st.sidebar.header("⚙️ 策略逻辑调整")
raw_codes = st.sidebar.text_input("监控代码 (如: sh600519,sz000001)", "sh600519,sz000001,sz002594")
rolling_buy = st.sidebar.number_input("仓位滚动买入阈值 (跌幅%)", value=-3.0, step=0.1)
stop_loss = st.sidebar.number_input("绝对止损警戒线 (跌幅%)", value=-5.0, step=0.1)

def get_stock_data(codes):
    url = f"http://qt.gtimg.cn/q={codes}"
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=5)
        response.encoding = 'gbk'
        data_lines = response.text.strip().split(';')
        results = []
        for line in data_lines:
            if '="' not in line: continue
            parts = line.split('=')
            info = parts[1].strip('"').split('~')
            if len(info) > 32:
                results.append({
                    "名称": info[1],
                    "代码": info[2],
                    "当前价": float(info[3]),
                    "涨跌额": float(info[31]),
                    "涨跌幅": float(info[32])
                })
        return results
    except:
        return []

if raw_codes:
    stocks = get_stock_data(raw_codes)
    cols = st.columns(len(stocks) if len(stocks) > 0 else 1)
    for i, s in enumerate(stocks):
        with cols[i]:
            delta_color = "normal" if s['涨跌幅'] >= 0 else "inverse"
            st.metric(label=f"{s['名称']}", value=f"¥{s['当前价']}", delta=f"{s['涨跌幅']}%", delta_color=delta_color)

    st.divider()
    st.subheader("🤖 主力反人性推演 & 买卖参考")
    for s in stocks:
        change = s['涨跌幅']
        with st.expander(f"查看 {s['名称']} 实时诊断", expanded=True):
            if change <= stop_loss:
                st.error(f"🚨 **风控扫描**：跌幅{change}%。已击穿止损线，根据逻辑需警惕主力反向诱空或趋势走坏。")
            elif change <= rolling_buy:
                st.success(f"💰 **反向博弈**：跌幅{change}%。符合‘仓位滚动法’买入区间，可考虑分批切入。")
            else:
                st.info(f"⚖️ **观望**：目前波动 {change}%，尚未触及预设逻辑点。")
else:
    st.warning("👈 请在左侧边栏输入股票代码")

if st.button('🔄 点击手动刷新'):
    st.rerun()
