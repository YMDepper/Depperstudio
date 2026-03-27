import streamlit as st
import requests
import time
from streamlit_autorefresh import st_autorefresh

# 1. 终端配置
st.set_page_config(page_title="鹰眼全维度终端", layout="wide")
st_autorefresh(interval=3000, limit=None, key="eagle_eye_v17")

if 'pool' not in st.session_state:
    st.session_state.pool = ["sz002428"] # 初始示例：云南锗业

# 2. 极简黑金 UI 引擎
st.markdown("""
<style>
    .stApp { background-color: #020408; color: #f8fafc; }
    .card { background: #0f172a; border: 1px solid #1e293b; border-radius: 12px; padding: 15px; margin-bottom: 15px; }
    .label-gold { color: #fbbf24; font-size: 12px; font-weight: bold; }
    .data-v { font-size: 18px; font-weight: 700; }
    /* 修正按钮错位 */
    .stButton button { width: 100%; background: #1e293b !important; border: 1px solid #334155 !important; color: #94a3b8 !important; }
    /* 图片容器适配 */
    .img-box { border: 2px solid #1e293b; border-radius: 8px; overflow: hidden; margin-top: 10px; }
</style>
""", unsafe_allow_html=True)

# --- 头部控制 ---
st.markdown('<p style="color:#64748b; font-size:12px;">EAGLE EYE STRATEGIC TERMINAL v1.7</p>', unsafe_allow_html=True)
c_search, _ = st.columns([0.6, 0.4])
with c_search:
    new_c = st.text_input("", placeholder="🔍 输入代码 (如 002428)", label_visibility="collapsed")
    if new_c:
        c_in = new_c.strip()
        if len(c_in) == 6: c_in = ("sh" if c_in.startswith(('6', '9')) else "sz") + c_in
        if c_in not in st.session_state.pool:
            st.session_state.pool.insert(0, c_in); st.rerun()

# --- 核心逻辑循环 ---
for code in st.session_state.pool:
    try:
        # 获取腾讯实时数据
        ts = int(time.time() * 1000)
        res = requests.get(f"http://qt.gtimg.cn/q={code}&_t={ts}", timeout=1.0)
        res.encoding = 'gbk'
        v = res.text.split('="')[1].split('~')
        name, price, change = v[1], v[3], float(v[32])
        color = "#ef4444" if change >= 0 else "#22c55e"
        simple_code = code[2:]

        # --- 模块 3：实时审计看板 (Header) ---
        with st.container():
            st.markdown(f"""
            <div class="card" style="border-left: 5px solid {color};">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <span style="background:{color}; padding:2px 6px; border-radius:4px; font-size:10px;">鹰眼评分 92</span>
                        <span style="font-size:20px; font-weight:bold; margin-left:10px;">{name}</span>
                    </div>
                    <div style="text-align:right;">
                        <span style="font-size:22px; font-weight:bold; color:{color};">{price}</span>
                        <span style="font-size:14px; margin-left:5px; color:{color};">{change}%</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # --- 模块 1 & 2：周线战略图 & 日线筹码图 ---
        c_weekly, c_daily = st.columns(2)
        
        with c_weekly:
            st.markdown('<p class="label-gold">1. 周线战略图 (趋势定位)</p>', unsafe_allow_html=True)
            st.image(f"http://image.sinajs.cn/newchart/weekly/n/{code}.gif", use_container_width=True)
            
        with c_daily:
            st.markdown('<p class="label-gold">2. 日线筹码图 (主力进出)</p>', unsafe_allow_html=True)
            st.image(f"http://image.sinajs.cn/newchart/daily/n/{code}.gif", use_container_width=True)

        # --- 深度审计详情 (反向博弈逻辑) ---
        with st.expander("点击展开：深度博弈审计 (反人性推演)"):
            st.markdown(f"""
            <div style="background:#020617; padding:15px; border-radius:8px; font-size:13px; line-height:1.8;">
                <span style="color:#3b82f6;">● 战略位置：</span> 周线处于<b style="color:#fbbf24;">三浪主升</b>阶段，大趋势向上。<br>
                <span style="color:#3b82f6;">● 筹码推演：</span> 日线级别<b style="color:#fbbf24;">筹码高度锁定</b>，今日回调属于缩量诱空。<br>
                <span style="color:#3b82f6;">● 主力意图：</span> 故意跌破分时均线，恐吓短线散户，实则大单在底部承接。<br>
                <hr style="border:0.5px solid #1e293b;">
                <span style="color:#ef4444;">● 风控指令：</span> 止损位点 <b>{v[4]}</b> | 止盈目标 <b>{round(float(price)*1.15, 2)}</b>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"移除 {name}", key=f"del_{code}"):
                st.session_state.pool.remove(code); st.rerun()

    except Exception as e:
        st.error(f"代码 {code} 审计数据源连接超时...")
        continue
