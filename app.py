import streamlit as st
import requests
import pandas as pd
import time

# 1. 页面极简配置 (强制宽屏+深色/浅色适配)
st.set_page_config(page_title="破军·鹰眼系统", page_icon="🎯", layout="wide")

# 2. 注入高级 CSS 样式 (让界面变高级、变干净)
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; border: 1px solid #e9ecef; padding: 15px; border-radius: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    [data-testid="stMetricValue"] { font-size: 28px !important; font-weight: 700 !important; color: #1a1a1a; }
    .status-box { padding: 12px; border-radius: 8px; margin: 10px 0; font-weight: 500; border-left: 5px solid; }
    .buy-zone { background-color: #e6fffa; border-left-color: #38a169; color: #234e52; }
    .risk-zone { background-color: #fff5f5; border-left-color: #e53e3e; color: #742a2a; }
    .watch-zone { background-color: #ebf8ff; border-left-color: #3182ce; color: #2a4365; }
    </style>
    """, unsafe_allow_html=True)

# --- 侧边栏：鹰眼参数配置 ---
with st.sidebar:
    st.header("🎯 鹰眼策略参数")
    user_stocks = st.text_input("监控代码 (逗号分隔)", "sh600519,sz000001,sz002594")
    
    st.subheader("📊 筹码逻辑")
    chip_support = st.number_input("日线筹码支撑位 (跌幅%)", value=-3.0, step=0.5)
    
    st.subheader("🛡️ 风险控制")
    stop_loss = st.number_input("绝对止损线 (跌幅%)", value=-5.5, step=0.1)
    
    st.info("💡 提示：修改参数后，右侧逻辑会自动重算。")

# --- 核心函数：高速数据抓取 ---
def get_data(codes):
    url = f"http://qt.gtimg.cn/q={codes}"
    try:
        res = requests.get(url, timeout=3)
        res.encoding = 'gbk'
        lines = res.text.strip().split(';')
        results = []
        for line in lines:
            if '="' not in line: continue
            info = line.split('=')[1].strip('"').split('~')
            if len(info) > 38:
                results.append({
                    "name": info[1],
                    "code": info[2],
                    "price": float(info[3]),
                    "change": float(info[32]),
                    "volume": float(info[37]), # 万
                    "turnover": float(info[38]) # 换手率
                })
        return results
    except: return []

# --- 主界面布局 ---
st.title("🎯 破军·鹰眼分析终端")

if user_stocks:
    data = get_data(user_stocks)
    
    # 顶部关键指标：一行展示，突出重点
    cols = st.columns(len(data))
    for i, s in enumerate(data):
        with cols[i]:
            # A股习惯：涨红跌绿
            color = "normal" if s['change'] >= 0 else "inverse"
            st.metric(label=f"{s['name']}", value=f"¥{s['price']}", delta=f"{s['change']}%", delta_color=color)

    st.markdown("---")
    
    # 下方：鹰眼逻辑推演区
    st.subheader("🔍 鹰眼系统：主力博弈推演")
    
    for s in data:
        change = s['change']
        turnover = s['turnover']
        
        # 逻辑判断
        if change <= stop_loss:
            status_class = "risk-zone"
            status_title = "🛑 风险预警：趋势破位"
            logic_desc = f"当前跌幅 {change}% 已击穿止损线。换手率 {turnover}%。若缩量阴跌，主力可能已离场；若放量，则是恐慌盘涌出，需严格执行风控。"
        elif change <= chip_support:
            status_class = "buy-zone"
            status_title = "💰 战略机会：筹码支撑区"
            logic_desc = f"跌幅 {change}% 进入日线筹码密集区。符合‘仓位滚动法’。此位置主力反人性诱空概率大，建议分批分仓切入。"
        else:
            status_class = "watch-zone"
            status_title = "⚖️ 动态观察：均衡博弈"
            logic_desc = f"当前波动 {change}%，属于正常震荡区间。换手率 {turnover}% 正常，主力意图不显，建议持仓不动，等待参数触碰。"

        # 渲染卡片
        st.markdown(f"""
            <div class="status-box {status_class}">
                <div style="font-size: 18px; font-weight: bold;">{s['name']} | {status_title}</div>
                <div style="margin-top: 8px; font-size: 14px; line-height: 1.6;">{logic_desc}</div>
            </div>
            """, unsafe_allow_html=True)

else:
    st.warning("👈 请在左侧输入股票代码。")

# 4. 自动刷新提示 (Streamlit Cloud 会自动处理重载，这里加个手动保底)
if st.button("🔄 立即同步最新数据"):
    st.rerun()
