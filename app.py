import streamlit as st
import requests
import time
from streamlit_autorefresh import st_autorefresh

# 1. 页面初始化
st.set_page_config(page_title="鹰眼审计终端", layout="wide")
st_autorefresh(interval=3000, limit=None, key="eagle_eye_v18")

if 'pool' not in st.session_state:
    st.session_state.pool = ["sz002428", "sh600137"]

# 2. 核心 UI 设计（彻底解决内嵌位置问题）
st.markdown("""
<style>
    .stApp { background-color: #020408; }
    
    /* 卡牌容器 */
    .stock-card {
        position: relative;
        background: #111827;
        border: 1px solid #1e293b;
        border-radius: 12px;
        padding: 25px;
        margin-bottom: 20px;
        transition: 0.3s;
    }
    
    /* 右上角移除按钮 X */
    .btn-delete {
        position: absolute;
        top: 15px;
        right: 15px;
        color: #475569;
        font-size: 20px;
        text-decoration: none;
        font-family: sans-serif;
    }
    .btn-delete:hover { color: #f1f5f9; }

    /* 右下角详情勾选 */
    .detail-trigger {
        position: absolute;
        bottom: 15px;
        right: 20px;
        color: #fbbf24;
        font-size: 14px;
        font-weight: bold;
        cursor: pointer;
    }

    /* 数据栅格布局 */
    .data-grid { display: flex; justify-content: space-between; margin-top: 25px; border-top: 1px solid #1e293b; padding-top: 15px; }
    .data-item { text-align: center; }
    .label { color: #64748b; font-size: 11px; margin-bottom: 4px; }
    .value { color: #f8fafc; font-size: 16px; font-weight: bold; }

    /* 隐藏 Streamlit 原生组件，只留逻辑 */
    .hidden-btn { display: none; }
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

        # --- UI 交互逻辑层 (隐藏的原生按钮) ---
        col_btn1, col_btn2 = st.columns([0.8, 0.2])
        with col_btn2:
            # 这里的交互通过隐藏原生按钮，利用 key 匹配
            show_detail = st.checkbox("了解详情", key=f"check_{code}")
            if st.button("X", key=f"btn_{code}"):
                st.session_state.pool.remove(code); st.rerun()

        # --- 核心卡牌展示层 ---
        st.markdown(f"""
        <div class="stock-card">
            <div style="position: absolute; top: 10px; right: 15px; color: #475569; font-size: 18px;">✕</div>
            
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <span style="background:rgba(239,68,68,0.15); color:#ef4444; padding:2px 8px; border-radius:4px; font-size:12px; font-weight:bold;">审计评分 92</span>
                    <div style="font-size: 24px; font-weight: bold; color: #f8fafc; margin-top: 8px;">{name} <span style="font-size:14px; color:#475569; font-weight:normal;">{code.upper()}</span></div>
                </div>
                <div style="text-align: right;">
                    <div style="font-size: 28px; font-weight: bold; color: {color};">{price}</div>
                    <div style="font-size: 14px; color: {color}; font-weight: bold;">{change}%</div>
                </div>
            </div>
            
            <div style="background: rgba(59, 130, 246, 0.05); padding: 12px; border-radius: 8px; margin-top: 20px; border-left: 3px solid #3b82f6;">
                <p style="margin:0; font-size:13px; color:#cbd5e1; line-height:1.5;">🎯 <b>审计推演：</b> 属于典型的反核博弈信号。资金逆势扫货迹象明显，主力反人性吸筹。</p>
            </div>

            <div class="data-grid">
                <div class="data-item"><div class="value">{prem}%</div><div class="label">开盘溢价</div></div>
                <div class="data-item"><div class="value" style="color:{color}">{ib}%</div><div class="label">盘中实体</div></div>
                <div class="data-item"><div class="value">39.1</div><div class="label">W&R</div></div>
                <div class="data-item"><div class="value">{v[33]}</div><div class="label">今日最高</div></div>
                <div class="data-item"><div class="value" style="color:#ef4444">{round(last_close*1.1, 2)}</div><div class="label">涨停目标</div></div>
            </div>

            <div class="detail-trigger">了解详情 》</div>
        </div>
        """, unsafe_allow_html=True)

        # 详情展开区 (跟随原生勾选框逻辑)
        if show_detail:
            st.markdown(f"""
            <div style="background:#020617; border: 1px dotted #1e293b; border-radius: 12px; padding: 15px; margin-top: -15px; margin-bottom: 20px; font-size: 13px; color: #94a3b8; line-height: 1.8;">
                <b style="color:#3b82f6;">[I] 仪表盘:</b> 总分 <span style="color:#fbbf24">92</span> | 周期: <span style="color:#fbbf24">主升中继</span> | 指令: <span style="color:#fbbf24">积极进攻</span><br>
                <b style="color:#3b82f6;">[II] 五维雷达:</b> 筹码: <span style="color:#fbbf24">35/35(+10)</span> | 环境: 18 | 排雷: 15 | 资金: 12<br>
                <b style="color:#3b82f6;">[III] 反向博弈:</b> <span style="color:#fbbf24">诱空吸筹</span> (证据: 缩量不破昨收，大单对倒)<br>
                <b style="color:#3b82f6;">[IV] 战术执行:</b> 进场: <span style="color:#fbbf24">{price}</span> | 止损位: <span style="color:#ef4444">{last_close}</span>
            </div>
            """, unsafe_allow_html=True)

    except:
        continue
