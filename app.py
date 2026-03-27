import streamlit as st
import requests
import time
from streamlit_autorefresh import st_autorefresh

# 1. 适配 iPhone & Mac 的页面配置
st.set_page_config(page_title="鹰眼审计终端", layout="wide")
st_autorefresh(interval=3000, limit=None, key="eagle_eye_v22")

if 'pool' not in st.session_state:
    st.session_state.pool = ["sz002428", "sh600137"]

# 2. 增强型 CSS：确保原生组件看起来像内嵌卡牌
st.markdown("""
<style>
    .stApp { background-color: #020408; }
    
    /* 模拟卡牌背景 */
    div[data-testid="stVerticalBlock"] > div:has(.audit-header) {
        background: #111827 !important;
        border: 1px solid #1e293b !important;
        border-radius: 12px !important;
        padding: 20px !important;
        margin-bottom: 15px !important;
    }

    /* 右上角 X 按钮精准压入 */
    .stButton button {
        position: absolute !important;
        top: -12px !important;
        right: -5px !important;
        background: transparent !important;
        border: none !important;
        color: #475569 !important;
        font-size: 22px !important;
        z-index: 100;
    }

    /* 右下角 详情 勾选框精准压入 */
    .stCheckbox {
        position: absolute !important;
        bottom: 15px !important;
        right: 15px !important;
        z-index: 100;
    }
    .stCheckbox label p { color: #fbbf24 !important; font-weight: bold !important; font-size: 14px !important; }

    /* 内部文字样式强制覆盖，防止被 Streamlit 默认样式干扰 */
    .stock-name { font-size: 24px !important; font-weight: bold !important; color: #f8fafc !important; }
    .price-large { font-size: 28px !important; font-weight: bold !important; }
    .audit-text-box { 
        background: rgba(59, 130, 246, 0.08); 
        padding: 12px; 
        border-radius: 8px; 
        border-left: 3px solid #3b82f6;
        color: #cbd5e1 !important;
        font-size: 14px !important;
        margin: 15px 0 !important;
    }
</style>
""", unsafe_allow_html=True)

# --- A. 搜索框 ---
c_s1, _ = st.columns([0.8, 0.2])
with c_s1:
    new_stock = st.text_input("", placeholder="🔍 输入代码审计 (回车添加)", label_visibility="collapsed")
    if new_stock:
        c_in = new_stock.strip()
        if len(c_in) == 6: c_in = ("sh" if c_in.startswith(('6', '9')) else "sz") + c_in
        if c_in not in st.session_state.pool:
            st.session_state.pool.insert(0, c_in); st.rerun()

# --- B. 审计卡牌队列 ---
for code in st.session_state.pool:
    try:
        # 数据获取
        res = requests.get(f"http://qt.gtimg.cn/q={code}", timeout=1.0)
        res.encoding = 'gbk'
        v = res.text.split('="')[1].split('~')
        name, price, change = v[1], v[3], float(v[32])
        color = "#ef4444" if change >= 0 else "#22c55e"
        
        # --- 核心结构：放弃整体 HTML，改用原生嵌套 ---
        with st.container():
            # 1. 隐形锚点（CSS 靠这个类名给 Container 加背景）
            st.markdown('<div class="audit-header"></div>', unsafe_allow_html=True)
            
            # 2. 顶层：名称、价格、以及那个 X
            t1, t2, t3 = st.columns([0.6, 0.3, 0.1])
            with t1:
                st.markdown(f'<span style="background:rgba(239,68,68,0.2);color:#ef4444;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:bold;">审计评分 92</span>', unsafe_allow_html=True)
                st.markdown(f'<div class="stock-name">{name} <span style="font-size:14px;color:#475569;">{code.upper()}</span></div>', unsafe_allow_html=True)
            with t2:
                st.markdown(f'<div style="text-align:right;"><div class="price-large" style="color:{color}">{price}</div><div style="color:{color};font-size:14px;">{change}%</div></div>', unsafe_allow_html=True)
            with t3:
                if st.button("✕", key=f"del_{code}"):
                    st.session_state.pool.remove(code); st.rerun()

            # 3. 推演区：单独的 Markdown，不嵌套在任何 Div 里，防止乱码
            st.markdown(f"""<div class="audit-text-box">🎯 <b>审计推演：</b> 典型的反核博弈信号。资金逆势扫货迹象明显，主力反人性吸筹。</div>""", unsafe_allow_html=True)

            # 4. 数据栅格：用 st.columns 彻底解决间距和乱码问题
            m1, m2, m3, m4, m5 = st.columns(5)
            # 这里简单模拟数据，你可以换成你的实时逻辑
            m1.metric("开盘溢价", f"{v[5]}%", delta_color="off")
            m2.metric("盘中实体", f"{v[32]}%", delta_color="normal")
            m3.metric("W&R", "39.1", delta_color="off")
            m4.metric("今日最高", v[33], delta_color="off")
            m5.metric("涨停目标", round(float(v[4])*1.1, 2), delta_color="off")

            # 5. 右下角开关
            show_detail = st.checkbox("详情 》", key=f"chk_{code}")

        # --- 6. 详情展开 ---
        if show_detail:
            st.markdown(f"""
            <div style="background:#020617; border: 1px dotted #334155; border-radius: 8px; padding: 15px; margin-top: -10px; margin-bottom: 20px;">
                <span style="color:#3b82f6;"><b>[周线战略图]</b></span> 处于主升浪中继，筹码高度锁定。<br>
                <span style="color:#3b82f6;"><b>[日线筹码图]</b></span> 诱空吸筹结束，关注分时均线承接机会。
            </div>
            """, unsafe_allow_html=True)

    except:
        continue
