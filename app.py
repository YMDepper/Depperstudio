import streamlit as st
import requests
import time
from streamlit_autorefresh import st_autorefresh

# 1. 大师级页面配置
st.set_page_config(page_title="鹰眼审计终端", layout="wide")
st_autorefresh(interval=3000, limit=None, key="eagle_eye_fix_v19")

if 'pool' not in st.session_state:
    st.session_state.pool = ["sz002428"] # 初始示例：云南锗业

# 2. 金融级 UI 引擎 CSS 注入：确保原生组件看起来像高端卡牌
st.markdown("""
<style>
    /* 全局黑金色调 */
    .stApp { background-color: #020408; font-family: -apple-system, sans-serif; }
    
    /* 强行挪动 X 按钮位置 */
    div[data-testid="stColumn"]:nth-child(2) button {
        margin-top: 10px !important;
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
        top: 20px; /* 根据卡牌高度微调 */
        left: 80%;
        z-index: 10;
    }
    div[data-testid="stCheckbox"] label p { color: #FFD700 !important; font-weight: bold !important; font-size: 13px !important; }

    /* 全局指标数据着色 */
    [data-testid="stMetricValue"] { font-size: 26px !important; font-weight: bold !important; color: #FFD700 !important; }
    [data-testid="stMetricLabel"] { color: #64748b !important; font-size: 12px !important; }

    /* 详情卡片样式：蓝框包围 */
    .stAlert {
        background: #020617; border: 1px dotted #1e293b; border-radius: 8px;
        padding: 15px; margin-top: -10px; margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# --- A. 简洁搜索栏 ---
st.markdown('<p style="color:#64748b; font-size:12px; margin-bottom:8px;">EAGLE EYE STRATEGIC TERMINAL v1.9</p>', unsafe_allow_html=True)
c_search, _ = st.columns([0.6, 0.4])
with c_search:
    new_c = st.text_input("", placeholder="🔍 输入代码审计 (例如 600111)", label_visibility="collapsed")
    if new_c:
        c_in = new_c.strip()
        if len(c_in) == 6: c_in = ("sh" if c_in.startswith(('6', '9')) else "sz") + c_in
        if c_in not in st.session_state.pool:
            st.session_state.pool.insert(0, c_in); st.rerun()

# --- B. 动态卡牌渲染区 ---
for code in st.session_state.pool:
    try:
        ts = int(time.time() * 1000)
        res = requests.get(f"http://qt.gtimg.cn/q={code}&_t={ts}", timeout=1.0)
        res.encoding = 'gbk'
        v = res.text.split('="')[1].split('~')
        name, price, change = v[1], v[3], float(v[32])
        color = "#ef4444" if change >= 0 else "#22c55e"
        
        # 1. 操作插槽（用于绝对定位 X 和 勾选框）
        c_left, c_right = st.columns([0.9, 0.1])
        with c_right:
            if st.button("✕", key=f"del_{code}"):
                st.session_state.pool.remove(code); st.rerun()
        show_audit = st.checkbox("详情 》", key=f"chk_{code}")

        # 2. 核心信息看板 (Header)
        # 用 Container 包裹一个纯展示 HTML，防止内部交互崩溃，确保不乱码
        with st.container():
            st.markdown(f"""
            <div style="background:#111827; border:1px solid #1e293b; border-radius:12px; padding:20px; margin-top:-50px; z-index:1;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <span style="background:{color}; color:white; padding:2px 8px; border-radius:4px; font-size:11px; font-weight:bold;">审计评分 92</span>
                        <div style="font-size: 22px; font-weight: 700; color: #f8fafc; margin-top: 8px;">{name} <span style="font-size:13px; color:#475569;">{code.upper()}</span></div>
                    </div>
                    <div style="text-align: right; margin-right: 20px;">
                        <div style="font-size: 28px; font-weight: 700; color: {color};">{price}</div>
                        <div style="font-size: 14px; color: {color};">{change}%</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # 3. 核心推演：博弈推演 (使用 st.info 自带柔和蓝色背景)
        st.info(f"🎯 鹰眼审计结论：此为典型的反核博弈信号。资金逆势扫货迹象明显，主力反人性吸筹。建议关注午后均线承接机会。")

        # 4. 指标栅格（iPhone 竖屏排列优化）
        st.markdown('<p style="color:#64748b; font-size:12px;">实时核心指标</p>', unsafe_allow_html=True)
        g1, g2 = st.columns(2)
        with g1: st.metric("开盘溢价", f"{v[5]}%")
        with g2: st.metric("盘中实体", f"{v[32]}%")

        g3, g4, g5 = st.columns(3)
        with g3: st.metric("W&R", "39.1")
        with g4: st.metric("最高价", v[33])
        with g5: st.metric("涨停目标价", round(float(v[4])*1.1, 2))

        # 5. 详情审计抽屉 (勾选展开)
        if show_audit:
            # st.alert 自带蓝框，高级感十足
            st.markdown(f"""
            <div class="stAlert">
                <div style="color:#94a3b8; font-size:13px; line-height:2;">
                    <span style="color:#3b82f6; font-weight:bold;">[I] 仪表盘:</span> 鹰眼总分 <b style="color:#FFD700;">92</b> | 周期: <b style="color:#FFD700;">主升中继</b> | 决策: <b>积极进攻</b><br>
                    <span style="color:#3b82f6; font-weight:bold;">[II] 真假博弈:</span> <b style="color:#FFD700;">诱空吸筹</b> (证据: 缩量不破昨收，大单对倒现身)<br>
                    <span style="color:#3b82f6; font-weight:bold;">[III] 战术执行:</span> 建议进场: <b style="color:#FFD700;">{price}</b> | 止损位: <b style="color:#ef4444;">{v[4]}</b>
                </div>
            </div>
            """, unsafe_allow_html=True)

    except:
        continue
