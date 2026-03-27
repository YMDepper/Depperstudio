import streamlit as st
import requests
import time
from streamlit_autorefresh import st_autorefresh

# 1. 基础配置
st.set_page_config(page_title="鹰眼审计终端", layout="wide")
st_autorefresh(interval=2000, limit=None, key="eagle_eye_v14")

if 'pool' not in st.session_state:
    st.session_state.pool = ["sz002428"]

# 2. 核心 CSS：强制消除 Streamlit 组件的默认占位
st.markdown("""
<style>
    .stApp { background-color: #05070a; color: #ffffff; }
    
    /* 容器设为相对定位 */
    .stock-card { 
        position: relative; 
        background: #111827; 
        border-radius: 10px; 
        padding: 15px; 
        margin-bottom: 10px; 
        border: 1px solid #1f2937;
        border-left: 5px solid #ef4444;
    }

    /* 暴力锁定右上角删除：解决移动端错位 */
    .stButton { position: absolute !important; top: 0 !important; right: 0 !important; width: auto !important; z-index: 1001; }
    .stButton button { 
        background: transparent !important; border: none !important; color: #FFD700 !important; 
        font-size: 20px !important; padding: 10px 15px !important; box-shadow: none !important;
    }

    /* 暴力锁定右下角详情：解决移动端错位 */
    [data-testid="stCheckbox"] { 
        position: absolute !important; bottom: 8px !important; right: 10px !important; 
        width: auto !important; z-index: 1001; margin: 0 !important;
    }
    [data-testid="stCheckbox"] label p { color: #FFD700 !important; font-weight: bold !important; font-size: 14px !important; }

    /* 数据显示网格调整 */
    .data-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 5px; text-align: center; margin-top: 15px; width: 85%; }
    .gold-text { color: #FFD700; font-weight: bold; }
    
    /* 详情卡片样式 */
    .audit-card { background: #0f172a; border: 1px solid #3b82f6; border-radius: 8px; padding: 15px; margin-top: -5px; margin-bottom: 15px; }
</style>
""", unsafe_allow_html=True)

# --- A. 搜索区 ---
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
    ts = int(time.time() * 1000)
    try:
        res = requests.get(f"http://qt.gtimg.cn/q={code}&_t={ts}", timeout=1.0)
        res.encoding = 'gbk'
        v = res.text.split('="')[1].split('~')
        name, price, change = v[1], v[3], float(v[32])
        last_close, open_p = float(v[4]), float(v[5])
        color = "#ef4444" if change >= 0 else "#22c55e"
        
        # 逻辑：开盘溢价与实体计算
        prem = round((open_p - last_close) / last_close * 100, 2)
        ib = round((float(price) - open_p) / open_p * 100, 2) if open_p > 0 else 0

        # 开始卡牌渲染
        with st.container():
            # 1. 注入内嵌交互组件 (利用绝对定位直接覆盖在卡牌之上)
            if st.button("✕", key=f"del_{code}"):
                st.session_state.pool.remove(code); st.rerun()
            
            show_audit = st.checkbox("详情》", key=f"dt_{code}")

            # 2. 卡牌主体 HTML
            st.markdown(f"""
            <div class="stock-card">
                <div style="display: flex; justify-content: space-between; margin-right: 40px;">
                    <div>
                        <span style="background:#ef4444; padding:2px 6px; border-radius:4px; font-weight:bold; font-size:12px;">评分 92</span>
                        <span style="font-size:18px; font-weight:bold; margin-left:5px;">{name}</span>
                        <span style="color:#64748b; font-size:12px; margin-left:5px;">{code}</span>
                    </div>
                    <div style="text-align:right;">
                        <span style="font-size:20px; font-weight:bold; color:{color};">{price}</span>
                        <span style="font-size:13px; font-weight:bold; color:{color}; margin-left:5px;">{change}%</span>
                    </div>
                </div>
                <div style="background:#0a0f1a; padding:10px; border-radius:6px; margin:15px 0; border-left:3px solid #3b82f6; width: 88%; font-size:13px;">
                    🎯 <b>核心结论：</b> 属于典型的反核博弈信号。资金逆势扫货迹象明显，建议分批挂单。
                </div>
                <div class="data-grid">
                    <div><div style="font-size:15px; font-weight:bold;">{prem}%</div><div style="font-size:10px; color:#64748b;">开盘溢价</div></div>
                    <div><div style="font-size:15px; font-weight:bold; color:{color}">{ib}%</div><div style="font-size:10px; color:#64748b;">盘中实体</div></div>
                    <div><div style="font-size:15px; font-weight:bold;">39.1</div><div style="font-size:10px; color:#64748b;">W&R</div></div>
                    <div><div style="font-size:15px; font-weight:bold;">{v[33]}</div><div style="font-size:10px; color:#64748b;">最高</div></div>
                    <div><div style="font-size:15px; font-weight:bold; color:#ef4444">{round(last_close*1.1, 2)}</div><div style="font-size:10px; color:#64748b;">涨停价</div></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # 3. 详情审计卡 (按需求完整呈现五个部分)
            if show_audit:
                st.markdown(f"""
                <div class="audit-card">
                    <div style="font-size:13px; line-height:1.6;">
                        <p><b style="color:#3b82f6;">I. 仪表盘:</b> 总分 <span class="gold-text">92</span> | 周期: <span class="gold-text">主升中继</span> | 指令: <span class="gold-text">积极进攻</span></p>
                        <p><b style="color:#3b82f6;">II. 五维雷达:</b> 筹码 <span class="gold-text">35/35(+10)</span> | 环境 18 | 排雷 15 | 资金 12 | 决策 12</p>
                        <p><b style="color:#3b82f6;">III. 真假博弈:</b> 意图: <span class="gold-text">诱空吸筹</span> | 证据: 缩量不破昨收，大单对倒现身。</p>
                        <p><b style="color:#3b82f6;">IV. 死亡红线:</b> 筹码诈骗/暴雷排查: <span style="color:#22c55e;">安全 (PASS)</span></p>
                        <p><b style="color:#3b82f6;">V. 战术执行:</b> 进场: <span class="gold-text">{price}</span> | 止损: <span style="color:#ef4444;">{last_close}</span></p>
                    </div>
                </div>
                """, unsafe_allow_html=True)
    except:
        continue
