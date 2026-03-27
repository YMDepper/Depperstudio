import streamlit as st
import requests
import time
from streamlit_autorefresh import st_autorefresh

# 1. 极致页面配置
st.set_page_config(page_title="鹰眼审计终端", layout="wide")
st_autorefresh(interval=3000, limit=None, key="eagle_eye_v20")

if 'pool' not in st.session_state:
    st.session_state.pool = ["sz002428", "sh600137"]

# 2. 核心 CSS 注入：精准控制卡牌样式和内嵌位置
st.markdown("""
<style>
    .stApp { background-color: #020408; }
    
    /* 卡牌容器：通过 Container 模拟 */
    [data-testid="stVerticalBlock"] > div:has(.stock-card-header) {
        background: #111827;
        border: 1px solid #1e293b;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
    }

    /* 右上角 X 按钮样式强修 */
    .stButton button:has(div:contains("✕")) {
        position: absolute !important;
        top: -10px !important;
        right: 0px !important;
        background: transparent !important;
        border: none !important;
        color: #475569 !important;
        font-size: 22px !important;
        z-index: 100;
    }

    /* 右下角 详情 勾选框样式强修 */
    .stCheckbox {
        position: absolute !important;
        bottom: 10px !important;
        right: 15px !important;
        z-index: 100;
    }
    .stCheckbox label p { color: #fbbf24 !important; font-weight: bold !important; font-size: 14px !important; }

    /* 内部文字样式 */
    .stock-title { font-size: 24px; font-weight: bold; color: #f8fafc; margin-bottom: 5px; }
    .stock-code { color: #475569; font-size: 14px; }
    .audit-box { background: rgba(59, 130, 246, 0.05); padding: 12px; border-radius: 8px; border-left: 3px solid #3b82f6; margin: 15px 0; }
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
        # 获取数据逻辑保持不变
        ts = int(time.time() * 1000)
        res = requests.get(f"http://qt.gtimg.cn/q={code}&_t={ts}", timeout=1.0)
        res.encoding = 'gbk'
        v = res.text.split('="')[1].split('~')
        name, price, change = v[1], v[3], float(v[32])
        last_close, open_p = float(v[4]), float(v[5])
        color = "#ef4444" if change >= 0 else "#22c55e"
        
        prem = round((open_p - last_close) / last_close * 100, 2)
        ib = round((float(price) - open_p) / open_p * 100, 2) if open_p > 0 else 0

        # --- 核心布局：利用 Container 嵌套 ---
        with st.container():
            # 标记类名供 CSS 抓取样式
            st.markdown('<div class="stock-card-header"></div>', unsafe_allow_html=True)
            
            # 布局 1：顶部信息 + 右上角 X
            col_info, col_x = st.columns([0.9, 0.1])
            with col_info:
                st.markdown(f'<span style="background:rgba(239,68,68,0.15); color:#ef4444; padding:2px 8px; border-radius:4px; font-size:11px; font-weight:bold;">审计评分 92</span>', unsafe_allow_html=True)
                st.markdown(f'<div class="stock-title">{name} <span class="stock-code">{code.upper()}</span></div>', unsafe_allow_html=True)
            with col_x:
                if st.button("✕", key=f"del_{code}"):
                    st.session_state.pool.remove(code); st.rerun()

            # 布局 2：价格展示
            c_p1, c_p2 = st.columns([0.5, 0.5])
            with c_p2:
                st.markdown(f'<div style="text-align: right; margin-top: -50px;"><span style="font-size: 32px; font-weight: bold; color: {color};">{price}</span><br><span style="font-size: 16px; color: {color};">{change}%</span></div>', unsafe_allow_html=True)

            # 布局 3：结论区
            st.markdown(f'<div class="audit-box"><p style="margin:0; font-size:13px; color:#cbd5e1;">🎯 <b>审计推演：</b> 属于典型的反核博弈信号。资金逆势扫货迹象明显，建议分批入场。</p></div>', unsafe_allow_html=True)

            # 布局 4：底层数据网格
            cols = st.columns(5)
            metrics = [
                (f"{prem}%", "开盘溢价"), (f"{ib}%", "盘中实体"), ("39.1", "W&R"), (f"{v[33]}", "今日最高"), (f"{round(last_close*1.1, 2)}", "涨停目标")
            ]
            for i, (val, lab) in enumerate(metrics):
                with cols[i]:
                    st.markdown(f'<div style="text-align: center;"><div style="font-size: 16px; font-weight: bold; color: #f8fafc;">{val}</div><div style="font-size: 11px; color: #64748b;">{lab}</div></div>', unsafe_allow_html=True)

            # 布局 5：右下角详情（原生内嵌）
            show_detail = st.checkbox("详情 》", key=f"chk_{code}")

        # 3. 详情展示
        if show_detail:
            st.markdown(f"""
            <div style="background:#020617; border: 1px dotted #1e293b; border-radius: 12px; padding: 15px; margin-top: -10px; margin-bottom: 20px; font-size: 13px; color: #94a3b8; line-height: 1.8;">
                <b style="color:#3b82f6;">[I] 仪表盘:</b> 总分 <span style="color:#fbbf24">92</span> | 周期: <span style="color:#fbbf24">主升浪中继</span> | 指令: <span style="color:#fbbf24">积极进攻</span><br>
                <b style="color:#3b82f6;">[II] 筹码博弈:</b> <span style="color:#fbbf24">诱空吸筹</span> (证据: 缩量不破昨收，大单对倒现身)
            </div>
            """, unsafe_allow_html=True)

    except Exception as e:
        continue
