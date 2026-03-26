import streamlit as st
import requests
import pandas as pd
import time

# 1. 页面配置：极致简洁
st.set_page_config(page_title="破军·鹰眼终端", page_icon="🦅", layout="wide")

# 2. 注入高级 CSS：优化列表显示与移动端间距
st.markdown("""
    <style>
    .stTable { background-color: white; border-radius: 10px; }
    .stMetric { border: 1px solid #eee; padding: 10px; border-radius: 8px; }
    .status-tag { padding: 2px 8px; border-radius: 4px; font-weight: bold; font-size: 12px; }
    .buy { background-color: #00fa9a; color: #006400; }
    .risk { background-color: #ffcccb; color: #8b0000; }
    .hold { background-color: #e0f7fa; color: #006064; }
    </style>
    """, unsafe_allow_html=True)

# --- 核心逻辑：数据抓取 ---
def fetch_stock_data(codes):
    if not codes: return []
    url = f"http://qt.gtimg.cn/q={','.join(codes)}"
    try:
        res = requests.get(url, timeout=5)
        res.encoding = 'gbk'
        results = []
        for line in res.text.strip().split(';'):
            if '="' not in line: continue
            info = line.split('=')[1].strip('"').split('~')
            if len(info) > 38:
                results.append({
                    "名称": info[1],
                    "代码": info[2],
                    "当前价": float(info[3]),
                    "涨跌幅%": float(info[32]),
                    "换手%": float(info[38]),
                    "成交额(亿)": round(float(info[37])/10000, 2)
                })
        return results
    except: return []

# --- 侧边栏：自选股池管理 ---
with st.sidebar:
    st.header("🦅 鹰眼池管理")
    
    # 预设几个默认股票，你可以直接删除并添加自己的
    if 'my_watch_list' not in st.session_state:
        st.session_state.my_watch_list = ["sh600519", "sz000001", "sz002594"]
    
    # 手动添加功能
    new_code = st.text_input("➕ 输入新代码 (如 sh600000)", "").lower()
    if st.button("添加到池子") and new_code:
        if n := new_code.strip():
            st.session_state.my_watch_list.append(n)
            st.session_state.my_watch_list = list(set(st.session_state.my_watch_list)) # 去重
            st.rerun()

    if st.button("🗑️ 清空所有自选"):
        st.session_state.my_watch_list = []
        st.rerun()

    st.divider()
    st.subheader("⚙️ 逻辑阈值")
    buy_limit = st.number_input("滚动买入触发(%)", value=-3.0, step=0.5)
    risk_limit = st.number_input("止损警报触发(%)", value=-5.0, step=0.5)

# --- 主界面 ---
st.title("🦅 破军·鹰眼实时终端")

if st.session_state.my_watch_list:
    data = fetch_stock_data(st.session_state.my_watch_list)
    df = pd.DataFrame(data)

    # A. 顶部重点监控（展示涨跌最剧烈的几只）
    st.subheader("🔥 重点波动监控")
    top_cols = st.columns(min(len(data), 4))
    for i, row in enumerate(data[:4]):
        with top_cols[i]:
            color = "normal" if row['涨跌幅%'] >= 0 else "inverse"
            st.metric(row['名称'], f"¥{row['当前价']}", f"{row['涨跌幅%']}%", delta_color=color)

    st.divider()

    # B. 全量列表看板（表格形式，简洁干净）
    st.subheader("📋 我的自选池清单")
    
    # 增加逻辑诊断列
    def judge(x):
        if x <= risk_limit: return "🛑 破位风控"
        if x <= buy_limit: return "💰 滚动买入"
        return "⚖️ 观望中"
    
    df['鹰眼诊断'] = df['涨跌幅%'].apply(judge)
    
    # 格式化表格显示
    st.dataframe(
        df, 
        column_config={
            "涨跌幅%": st.column_config.NumberColumn(format="%.2f%%"),
            "当前价": st.column_config.NumberColumn(format="¥%.2f"),
        },
        hide_index=True,
        use_container_width=True
    )

    # C. 主力博弈简报
    st.markdown("---")
    st.subheader("🧠 主力博弈逻辑推演")
    for row in data:
        if row['涨跌幅%'] <= buy_limit:
            st.success(f"**{row['名称']}**: 股价进入反人性布局区（{row['涨跌幅%']}%）。换手率 {row['换手%']}%，观察是否有缩量止跌信号。")
        elif row['涨跌幅%'] <= risk_limit:
            st.error(f"**{row['名称']}**: 触发风险扫描。当前跌幅较大，需对比日线筹码图确认支撑是否失效。")

else:
    st.info("💡 你的鹰眼池还是空的，请在左侧边栏添加股票代码（如 sh600519）。")

# 自动刷新
if st.button("🔄 同步最新行情"):
    st.rerun()
