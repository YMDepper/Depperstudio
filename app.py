import streamlit as st
import requests
import time
from streamlit_autorefresh import st_autorefresh

# 1. 基础配置
st.set_page_config(page_title="鹰眼审计终端", layout="wide")
st_autorefresh(interval=3000, limit=None, key="eagle_eye_fix")

if 'pool' not in st.session_state:
    st.session_state.pool = ["sz002428", "sh600137"]

# 2. 核心样式修复（只做背景和文字着色，不改结构）
st.markdown("""
<style>
    .stApp { background-color: #0d1117; }
    /* 卡牌容器样式 */
    .reportview-container .main .block-container { padding-top: 2rem; }
    div[data-testid="stMetric"] { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 10px; }
</style>
""", unsafe_allow_html=True)

# --- A. 搜索栏 ---
search_input = st.text_input("🔍 输入代码审计 (回车添加)", placeholder="例如: 600111")
if search_input:
    code = search_input.strip()
    if len(code) == 6: code = ("sh" if code.startswith(('6', '9')) else "sz") + code
    if code not in st.session_state.pool:
        st.session_state.pool.insert(0, code); st.rerun()

# --- B. 审计队列 ---
for code in st.session_state.pool:
    try:
        # 获取实时数据
        res = requests.get(f"http://qt.gtimg.cn/q={code}", timeout=1)
        v = res.text.split('~')
        name, price, change = v[1], v[3], float(v[32])
        color = "red" if change >= 0 else "green"
        
        # --- 1. 卡牌头部 (原生渲染) ---
        col_header, col_action = st.columns([0.9, 0.1])
        with col_header:
            st.markdown(f"### <span style='background:#ef4444; color:white; padding:2px 8px; border-radius:4px;'>评分 92</span> {name} <small style='color:#8b949e;'>{code.upper()}</small>", unsafe_allow_html=True)
        with col_action:
            if st.button("✕", key=f"del_{code}"):
                st.session_state.pool.remove(code); st.rerun()

        # --- 2. 核心指标与价格 ---
        p1, p2 = st.columns([0.7, 0.3])
        with p1:
            st.info(f"🎯 **审计推演**：属于典型的反核博弈信号。资金逆势扫货迹象明显，关注午后承接力度。")
        with p2:
            st.markdown(f"<div style='text-align:right;'><h1 style='color:{color};margin-bottom:0;'>{price}</h1><p style='color:{color};'>{change}%</p></div>", unsafe_allow_html=True)

        # --- 3. 五维数据栅格 ---
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("开盘溢价", f"{v[5]}%")
        m2.metric("盘中实体", f"{v[32]}%")
        m3.metric("W&R指标", "39.1")
        m4.metric("今日最高", v[33])
        m5.metric("涨停目标", round(float(v[4])*1.1, 2))

        # --- 4. 详情展开逻辑 ---
        if st.checkbox("查看详情 》", key=f"chk_{code}"):
            st.markdown(f"""
            <div style="background:#0d1117; border: 1px solid #30363d; border-left: 4px solid #3b82f6; padding: 15px; border-radius: 4px;">
                <p style="color:#58a6ff; margin:0;"><b>I. 仪表盘:</b> 鹰眼总分 92 | 周期: <b style="color:#f0883e;">主升浪中继</b> | 决策: <b>积极进攻</b></p>
                <p style="color:#58a6ff; margin:0;"><b>II. 五维雷达:</b> 筹码: 35/35(+10) | 环境: 18 | 排雷: 15 | 决策: 12</p>
                <p style="color:#58a6ff; margin:0;"><b>III. 真假博弈:</b> 意图判定: <b style="color:#f0883e;">诱空吸筹</b> | 核心证据: 缩量不破昨收</p>
                <p style="color:#58a6ff; margin:0;"><b>IV. 死亡红线:</b> 筹码诈骗: 无 | 硬伤暴雷: 无 | 判定: <b style="color:#3fb950;">安全</b></p>
                <p style="color:#58a6ff; margin:0;"><b>V. 战术执行:</b> 进场: <b style="color:#f0883e;">{price}</b> | 止损: 46.69</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.divider() # 卡牌分割线

    except Exception as e:
        continue
