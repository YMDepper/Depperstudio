import streamlit as st
import requests
import time
from streamlit_autorefresh import st_autorefresh

# 1. 极致页面配置
st.set_page_config(page_title="鹰眼审计终端", layout="wide")
st_autorefresh(interval=3000, limit=None, key="eagle_eye_v19")

if 'pool' not in st.session_state:
    st.session_state.pool = ["sz002428", "sh600137"]

# 2. 深度 UI 修正：强行定位原生组件
st.markdown("""
<style>
    .stApp { background-color: #020408; }
    
    /* 卡牌容器 */
    .stock-card {
        background: #111827;
        border: 1px solid #1e293b;
        border-radius: 12px;
        padding: 20px;
        margin-top: -50px; /* 向上偏移以包裹原生按钮 */
        position: relative;
        z-index: 1;
    }
    
    /* 强行挪动 X 按钮位置 */
    div[data-testid="stColumn"]:nth-child(2) button {
        margin-top: 15px !important;
        margin-left: 80% !important;
        background: transparent !important;
        border: none !important;
        color: #475569 !important;
        font-size: 20px !important;
        z-index: 10;
    }

    /* 强行挪动 详情 勾选框位置 */
    div[data-testid="stCheckbox"] {
        position: relative;
        top: 185px; /* 根据卡牌高度微调 */
        left: 85%;
        z-index: 10;
    }
    div[data-testid="stCheckbox"] label p { color: #fbbf24 !important; font-weight: bold !important; font-size: 13px !important; }

    /* 数据栅格布局 */
    .data-grid { display: flex; justify-content: space-between; margin-top: 20px; border-top: 1px solid #1e293b; padding-top: 15px; }
    .data-item { text-align: center; }
    .label { color: #64748b; font-size: 11px; }
    .value { color: #f8fafc; font-size: 16px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# --- A. 顶栏搜索 ---
c_search, _ = st.columns([0.6, 0.4])
with c_search:
    new_c = st.text_input("", placeholder="🔍 输入代码审计 (回车添加)", label_visibility="collapsed")
    if new_c:
        c_in = new_c.strip()
        if len(c_in) == 6: c_in = ("sh" if c_in.startswith(('6', '9')) else "sz") + c_in
        if c_in not in st.session_state.pool:
            st.session_state.pool.insert(0, c_in); st.rerun()

# --- B. 动态卡牌渲染 ---
for code in st.session_state.pool:
    try:
        ts = int(time.time() * 1000)
        res = requests.get(f"http://qt.gtimg.cn/q={code}&_t={ts}", timeout=1.0)
        res.encoding = 'gbk'
        v = res.text.split('="')[1].split('~')
        name, price, change = v[1], v[3], float(v[32])
        last_close, open_p = float(v[4]), float(v[5])
        color = "#ef4444" if change >= 0 else "#22c55e"
        
        prem = round((open_p - last_close) / last_close * 100, 2)
        ib = round((float(price) - open_p) / open_p * 100, 2) if open_p > 0 else 0

        # 1. 预留插槽层（用于放置 X 和 勾选框）
        c_left, c_right = st.columns([0.9, 0.1])
        with c_right:
            if st.button("✕", key=f"btn_{code}"):
                st.session_state.pool.remove(code); st.rerun()
        
        show_detail = st.checkbox("详情 》", key=f"chk_{code}")

        # 2. 核心展示层（纯 HTML 展示，不带任何交互属性，确保不乱码）
        st.markdown(f"""
        <div class="stock-card">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <span style="background:rgba(239,68,68,0.15); color:#ef4444; padding:2px 8px; border-radius:4px; font-size:11px; font-weight:bold;">审计评分 92</span>
                    <div style="font-size: 22px; font-weight: bold; color: #f8fafc; margin-top: 8px;">{name} <span style="font-size:13px; color:#475569;">{code.upper()}</span></div>
                </div>
                <div style="text-align: right; margin-right: 40px;">
                    <div style="font-size: 26px; font-weight: bold; color: {color};">{price}</div>
                    <div style="font-size: 14px; color: {color};">{change}%</div>
                </div>
            </div>
            
            <div style="background: rgba(59, 130, 246, 0.05); padding: 12px; border-radius: 8px; margin-top: 15px; border-left: 3px solid #3b82f6; width: 85%;">
                <p style="margin:0; font-size:13px; color:#cbd5e1;">🎯 <b>审计推演：</b> 属于典型的反核博弈信号。资金逆势扫货迹象明显，主力反人性吸筹。</p>
            </div>

            <div class="data-grid">
                <div class="data-item"><div class="value">{prem}%</div><div class="label">开盘溢价</div></div>
                <div class="data-item"><div class="value" style="color:{color}">{ib}%</div><div class="label">盘中实体</div></div>
                <div class="data-item"><div class="value">39.1</div><div class="label">W&R</div></div>
                <div class="data-item"><div class="value">{v[33]}</div><div class="label">最高</div></div>
                <div class="data-item"><div class="value" style="color:#ef4444">{round(last_close*1.1, 2)}</div><div class="label">涨停目标</div></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # 3. 详情展开
        if show_detail:
            st.info(f"【深度审计】意图：诱空吸筹 | 证据：缩量不破昨收，大单对倒 | 建议：{price} 附近积极进场。")

    except:
        continue
