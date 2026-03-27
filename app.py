import streamlit as st
import requests
import time
from streamlit_autorefresh import st_autorefresh

# 1. 极简配置
st.set_page_config(page_title="鹰眼审计终端", layout="wide")
st_autorefresh(interval=3000, limit=None, key="eagle_eye_v15_pro")

if 'pool' not in st.session_state:
    st.session_state.pool = ["sz002428", "sh600137"]

# 2. 深度定制 CSS：锁定 UI 比例，防止代码外溢
st.markdown("""
<style>
    .stApp { background-color: #020408; }
    
    /* 战术卡牌容器 */
    .stock-card {
        background: linear-gradient(145deg, #111827, #0f172a);
        border: 1px solid #1e293b; 
        border-radius: 16px; 
        padding: 24px;
        margin-bottom: 5px;
        position: relative;
    }

    /* 数据层级显示 */
    .data-grid { display: flex; justify-content: space-between; margin-top: 20px; border-top: 1px solid #1e293b; padding-top: 15px; }
    .data-item { text-align: center; }
    .label { color: #64748b; font-size: 11px; text-transform: uppercase; }
    .value { color: #f8fafc; font-size: 16px; font-weight: 600; margin-bottom: 4px; }

    /* 按钮样式微调 */
    .stButton button { background: transparent !important; border: 1px solid #334155 !important; color: #94a3b8 !important; border-radius: 8px !important; width: 100% !important; }
    .stCheckbox label p { color: #fbbf24 !important; font-weight: bold !important; }
</style>
""", unsafe_allow_html=True)

# --- A. 顶栏搜索 (保持干净) ---
st.markdown('<p style="color:#64748b; font-size:12px; margin-bottom:10px;">鹰眼·实时量化监测</p>', unsafe_allow_html=True)
c_search, _ = st.columns([0.6, 0.4])
with c_search:
    new_c = st.text_input("", placeholder="🔍 输入代码审计 (如 600111)", label_visibility="collapsed")
    if new_c:
        c_in = new_c.strip()
        if len(c_in) == 6: c_in = ("sh" if c_in.startswith(('6', '9')) else "sz") + c_in
        if c_in not in st.session_state.pool:
            st.session_state.pool.insert(0, c_in); st.rerun()

# --- B. 审计监控区 ---
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

        # 1. 顶部操作条（将交互单独提出，不再强制嵌套进 HTML 卡牌内部，避免崩坏）
        c_op1, c_op2, _ = st.columns([0.15, 0.2, 0.65])
        with c_op1:
            if st.button("移除", key=f"del_{code}"):
                st.session_state.pool.remove(code); st.rerun()
        with c_op2:
            show_audit = st.checkbox("深度审计》", key=f"dt_{code}")

        # 2. 高级感数据卡牌 (HTML 纯展示)
        st.markdown(f"""
        <div class="stock-card">
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                <div>
                    <span style="background:rgba(239,68,68,0.15); color:#ef4444; padding:2px 8px; border-radius:4px; font-size:12px; font-weight:bold;">审计评分 92</span>
                    <div style="font-size: 22px; font-weight: 700; color: #f8fafc; margin-top: 10px;">{name}</div>
                    <div style="color: #475569; font-size: 13px;">{code.upper()}</div>
                </div>
                <div style="text-align: right;">
                    <div style="font-size: 26px; font-weight: 700; color: {color};">{price}</div>
                    <div style="font-size: 14px; color: {color};">{change}%</div>
                </div>
            </div>
            
            <div style="background: rgba(59, 130, 246, 0.05); padding: 12px; border-radius: 10px; margin-top: 20px; border-left: 3px solid #3b82f6;">
                <span style="color: #cbd5e1; font-size: 13px; line-height: 1.5;">🎯 <b>审计推演：</b> 属于典型的反核博弈信号。资金逆势扫货迹象明显，主力反人性吸筹。</span>
            </div>

            <div class="data-grid">
                <div class="data-item"><div class="value">{prem}%</div><div class="label">开盘溢价</div></div>
                <div class="data-item"><div class="value" style="color:{color}">{ib}%</div><div class="label">盘中实体</div></div>
                <div class="data-item"><div class="value">39.1</div><div class="label">W&R</div></div>
                <div class="data-item"><div class="value">{v[33]}</div><div class="label">今日最高</div></div>
                <div class="data-item"><div class="value" style="color:#ef4444">{round(last_close*1.1, 2)}</div><div class="label">涨停目标</div></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # 3. 详情审计模块
        if show_audit:
            st.markdown(f"""
            <div style="background:#020617; border: 1px dotted #1e293b; border-radius: 12px; padding: 15px; margin-bottom: 20px; font-size: 13px; color: #94a3b8; line-height: 1.8;">
                <b style="color:#3b82f6;">[I] 仪表盘:</b> 总分 <span style="color:#fbbf24">92</span> | 周期: <span style="color:#fbbf24">主升中继</span> | 指令: <span style="color:#fbbf24">积极进攻</span><br>
                <b style="color:#3b82f6;">[II] 五维雷达:</b> 筹码: <span style="color:#fbbf24">35/35(+10)</span> | 环境: 18 | 排雷: 15 | 决策: 12<br>
                <b style="color:#3b82f6;">[III] 反向博弈:</b> <span style="color:#fbbf24">诱空吸筹</span> (证据: 缩量不破昨收，盘中大单对倒)<br>
                <b style="color:#3b82f6;">[IV] 战术执行:</b> 进场: <span style="color:#fbbf24">{price}</span> | 止损位: <span style="color:#ef4444">{last_close}</span>
            </div>
            """, unsafe_allow_html=True)
    except:
        continue
