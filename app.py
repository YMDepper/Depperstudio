import streamlit as st
import requests
import pandas as pd
import time

# 页面基础配置：手机适配优化
st.set_page_config(page_title="专属实时监控", page_icon="📈", layout="wide")

# 强制注入 CSS 样式：让 A 股习惯的红涨绿跌更直观
st.markdown("""
    <style>
    [data-testid="stMetricDelta"] svg { display: none; }
    div[data-testid="stMetric"] { background-color: #f0f2f6; padding: 10px; border-radius: 10px; }
    </style>
    """, unsafe_allow_stdio=True)

st.title("📈 破军·实时监控系统")

# --- 侧边栏：随时调整你的交易逻辑 ---
st.sidebar.header("⚙️ 策略逻辑调整")

# 1. 输入自选股（支持多个，用逗号隔开）
# 默认放了茅台(sh600519)、平安(sz000001)、比亚迪(sz002594)
raw_codes = st.sidebar.text_input("监控代码 (如: sh600519,sz000001)", "sh600519,sz000001,sz002594")

# 2. 你的核心逻辑参数（随时修改，实时生效）
st.sidebar.subheader("📉 买点触发逻辑")
rolling_buy = st.sidebar.number_input("仓位滚动买入阈值 (跌幅%)", value=-3.0, step=0.1)

st.sidebar.subheader("🛡️ 风险控制逻辑")
stop_loss = st.sidebar.number_input("绝对止损警戒线 (跌幅%)", value=-5.0, step=0.1)

# --- 核心功能：获取腾讯财经实时数据 ---
def get_stock_data(codes):
    url = f"http://qt.gtimg.cn/q={codes}"
    try:
        # 模拟浏览器头部，防止拦截
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=5)
        response.encoding = 'gbk' # 腾讯接口使用gbk编码
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
                    "涨跌幅": float(info[32]),
                    "成交额(万)": round(float(info[37]), 2)
                })
        return results
    except:
        return []

# --- 主界面展示 ---
if raw_codes:
    stocks = get_stock_data(raw_codes)
    
    # 顶部卡片展示
    cols = st.columns(len(stocks) if len(stocks) > 0 else 1)
    for i, s in enumerate(stocks):
        with cols[i]:
            # A 股逻辑：涨跌幅为正显示红色，负显示绿色
            delta_color = "normal" if s['涨跌幅'] >= 0 else "inverse"
            st.metric(
                label=f"{s['名称']} ({s['代码']})", 
                value=f"¥{s['当前价']}", 
                delta=f"{s['涨跌幅']}%",
                delta_color=delta_color
            )

    st.divider()

    # --- 逻辑推演区 ---
    st.subheader("🤖 主力反人性推演 & 买卖参考")
    
    for s in stocks:
        change = s['涨跌幅']
        with st.expander(f"查看 {s['名称']} 实时诊断", expanded=True):
            col1, col2 = st.columns([1, 2])
            
            with col1:
                if change <= stop_loss:
                    st.error("🚨 触发【风控扫描】")
                elif change <= rolling_buy:
                    st.success("💰 触发【反向博弈】")
                else:
                    st.info("⚖️ 状态：波动观察中")
            
            with col2:
                if change <= stop_loss:
                    st.write(f"**诊断：** 当前跌幅 {change}% 已击穿止损线。根据‘反人性’逻辑，需判断是恐慌盘杀跌还是趋势走坏。建议执行预设风控。")
                elif change <= rolling_buy:
                    st.write(f"**诊断：** 符合‘仓位滚动法’。当前跌幅 {change}% 处于左侧布局区间，若成交额无异常放大，可考虑分批切入。")
                else:
                    st.write(f"**诊断：** 股价目前在合理区间震荡。主力意图不明显，建议保持观望，等待参数触发。")

else:
    st.warning("👈 请在左侧边栏输入股票代码开始监控")

# 设置每 30 秒自动尝试刷新（Streamlit 会重新运行脚本）
time.sleep(30)
if st.button('点击手动刷新实时数据'):
    st.rerun()