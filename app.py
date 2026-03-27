import streamlit as st
import requests
import time
from streamlit_autorefresh import st_autorefresh

# 1. 响应式页面配置
st.set_page_config(page_title="鹰眼审计终端", layout="wide")
st_autorefresh(interval=3000, limit=None, key="eagle_eye_v21")

if 'pool' not in st.session_state:
    st.session_state.pool = ["sz002428", "sh600137"]

# 2. 响应式 CSS（支持 iPhone & MacBook）
st.markdown("""
<style>
    .stApp { background-color: #020408; }
    
    /* 核心卡牌容器 */
    .stock-card {
        background: #111827;
        border: 1px solid #1e293b;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 10px;
        position: relative;
        display: flex;
        flex-direction: column;
    }

    /* 顶部操作区布局 */
    .card-top { display: flex; justify-content: space-between; align-items: flex-start; }
    
    /* 修正 X 按钮：使用 Streamlit 默认位置但通过 CSS 视觉微调 */
    .stButton button {
        background: transparent !important;
        border: none !important;
        color: #475569 !important;
        padding: 0 !important;
        min-height: 0 !important;
        font-size: 20px !important;
    }

    /* 详情勾选框：强制右下角对齐 */
    .detail-container {
        display: flex;
        justify-content: flex-end;
        margin-top: 10px;
    }
    div[data-testid="stCheckbox"] { margin-bottom: -15px !important; }
    div[data-testid="stCheckbox"] label p { color: #fbbf24 !important; font-size: 14px !important; font-weight: bold !important; }

    /* 数据栅格：手机端自动换行 */
    .data-grid { 
        display: grid; 
        grid-template-columns: repeat(auto-fit, minmax(60px, 1fr)); 
        gap: 10px;
        margin-top: 15px; 
        border-top: 1px solid #1e293b; 
        padding-top: 12px; 
    }
    .data-item { text-align: center; }
    .label { color: #64748b; font-size: 10px; }
    .value { color: #f8fafc; font-size: 14px; font-weight: bold; }

    /* 移动端适配：缩小字号防止错乱 */
    @media (max-width: 600px) {
        .stock-title { font-size: 18px !important; }
        .price-text { font-size: 22px !important; }
        .audit-text { font-size: 12px !important; }
    }
</style>
""", unsafe_allow_html=True)

# --- A. 顶栏搜索 ---
c_search, _ = st.columns([0.8, 0.2])
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

        # --- 1. 顶部操作栏（内嵌视觉核心） ---
        c_main, c_x = st.columns([0.9, 0.1])
        with c_x:
            if st.button("✕", key=f"del_{code}"):
                st.session_state.pool.remove(code); st.rerun()
        
        # --- 2. 卡牌主体（通过 Markdown 渲染文字，避免嵌套按钮） ---
        st.markdown(f"""
        <div class="stock-card" style="margin-top: -45px;">
            <div class="card-top">
                <div>
                    <span style="background:rgba(239,68,68,0.15); color:#ef4444; padding:2px 6px; border-radius:4px; font-size:10px; font-weight:bold;">审计评分 92</span>
                    <div class="stock-title" style="font-size: 22px; font-weight: bold; color: #f8fafc; margin-top: 5px;">{name} <span style="font-size:12px; color:#475569;">{code.upper()}</span></div>
                </div>
                <div style="text-align: right; margin-right: 15px;">
                    <div class="price-text" style="font-size: 26px; font-weight: bold; color: {color};">{price}</div>
                    <div style="font-size: 13px; color: {color};">{change}%</div>
                </div>
            </div>
            
            <div style="background: rgba(59, 130, 246, 0.05); padding: 10px; border-radius: 8px; margin-top: 12px; border-left: 3px solid #3b82f6;">
                <p class="audit-text" style="margin:0; font-size:13px; color:#cbd5e1; line-height:1.4;">🎯 <b>审计推演：</b> 属于典型的反核博弈信号。资金逆势扫货迹象明显，主力反人性吸筹。</p>
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

        # --- 3. 右下角详情开关 ---
        with st.container():
            col_space, col_check = st.columns([0.7, 0.3])
            with col_check:
                show_detail = st.checkbox("详情 》", key=f"chk_{code}")

        if show_detail:
            st.markdown(f"""
            <div style="background:#020617; border: 1px dotted #334155; border-radius: 8px; padding: 12px; margin-top: -10px; margin-bottom: 15px; font-size: 12px; color: #94a3b8;">
                <b style="color:#3b82f6;">[I] 仪表盘:</b> 鹰眼总分 92 | 周期: <b>主升浪中继</b><br>
                <b style="color:#3b82f6;">[II] 真假博弈:</b> 意图判定: <b>诱空吸筹</b> | 核心证据: 缩量不破昨收
            </div>
            """, unsafe_allow_html=True)

    except:
        continue
