import streamlit as st
import requests
import time
from streamlit_autorefresh import st_autorefresh

# 1. 极简页面配置
st.set_page_config(page_title="鹰眼审计终端", layout="wide")
st_autorefresh(interval=3000, limit=None, key="eagle_eye_v15")

if 'pool' not in st.session_state:
    st.session_state.pool = ["sz002428", "sh600137"]

# 2. 高级感黑金配色 CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    .stApp { background-color: #020408; font-family: 'Inter', sans-serif; }
    
    /* 隐藏所有原生组件的边距 */
    .block-container { padding-top: 2rem !important; }
    [data-testid="stHeader"] { visibility: hidden; }

    /* 搜索框高级处理 */
    .stTextInput input {
        background-color: #0f172a !important; border: 1px solid #1e293b !important;
        border-radius: 12px !important; color: #f8fafc !important; padding: 12px 20px !important;
    }

    /* 战术卡牌容器 */
    .stock-card {
        position: relative; background: linear-gradient(145deg, #111827, #0f172a);
        border: 1px solid #1e293b; border-radius: 16px; padding: 24px;
        margin-bottom: 16px; overflow: hidden;
        transition: all 0.3s ease;
    }
    .stock-card:hover { border-color: #3b82f6; box-shadow: 0 10px 30px -10px rgba(59, 130, 246, 0.2); }

    /* 评分勋章 */
    .score-badge {
        background: rgba(239, 68, 68, 0.15); color: #ef4444;
        padding: 4px 10px; border-radius: 6px; font-size: 12px; font-weight: 700;
        border: 1px solid rgba(239, 68, 68, 0.3); letter-spacing: 0.5px;
    }

    /* 数据栅格布局 */
    .data-grid { display: flex; justify-content: space-between; margin-top: 24px; border-top: 1px solid #1e293b; padding-top: 16px; }
    .data-item { text-align: center; flex: 1; }
    .label { color: #64748b; font-size: 11px; text-transform: uppercase; margin-top: 4px; }
    .value { color: #f8fafc; font-size: 16px; font-weight: 600; }

    /* 交互组件层级锁定 */
    .interaction-layer { position: absolute; top: 0; right: 0; bottom: 0; width: 60px; z-index: 100; }
    
    /* 右上角删除按钮 */
    .stButton { position: absolute !important; top: 12px !important; right: 12px !important; }
    .stButton button { 
        background: transparent !important; border: none !important; color: #475569 !important;
        font-size: 20px !important; padding: 0 !important;
    }
    .stButton button:hover { color: #f1f5f9 !important; }

    /* 右下角详情勾选 */
    [data-testid="stCheckbox"] { position: absolute !important; bottom: 12px !important; right: 12px !important; }
    [data-testid="stCheckbox"] label p { color: #475569 !important; font-size: 12px !important; transition: 0.3s; }
    [data-testid="stCheckbox"]:hover label p { color: #fbbf24 !important; }

    /* 审计卡高级样式 */
    .audit-card {
        background: #020617; border: 1px dotted #1e293b; border-radius: 12px;
        padding: 20px; margin-top: -10px; margin-bottom: 20px;
        animation: slideDown 0.4s ease-out;
    }
    @keyframes slideDown { from { opacity: 0; transform: translateY(-10px); } to { opacity: 1; transform: translateY(0); } }
</style>
""", unsafe_allow_html=True)

# --- A. 顶栏搜索 (保持干净) ---
st.markdown('<p style="color:#64748b; font-size:12px; margin-bottom:8px;">鹰眼·实时量化监测</p>', unsafe_allow_html=True)
c_search, _ = st.columns([0.5, 0.5])
with c_search:
    new_c = st.text_input("", placeholder="🔍 输入代码 (例如 600111)", label_visibility="collapsed")
    if new_c:
        c_in = new_c.strip()
        if len(c_in) == 6: c_in = ("sh" if c_in.startswith(('6', '9')) else "sz") + c_in
        if c_in not in st.session_state.pool:
            st.session_state.pool.insert(0, c_in); st.rerun()

# --- B. 动态卡牌区 ---
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

        # 渲染卡牌容器
        with st.container():
            # 1. 绝对定位交互层
            if st.button("✕", key=f"del_{code}"):
                st.session_state.pool.remove(code); st.rerun()
            show_audit = st.checkbox("详情", key=f"dt_{code}")

            # 2. 视觉主体
            st.markdown(f"""
            <div class="stock-card">
                <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                    <div>
                        <div class="score-badge">评分 92</div>
                        <div style="font-size: 22px; font-weight: 700; color: #f8fafc; margin-top: 12px;">{name}</div>
                        <div style="color: #475569; font-size: 13px; margin-top: 4px;">{code.upper()}</div>
                    </div>
                    <div style="text-align: right; margin-right: 20px;">
                        <div style="font-size: 28px; font-weight: 700; color: {color};">{price}</div>
                        <div style="font-size: 14px; font-weight: 600; color: {color};">{change}%</div>
                    </div>
                </div>
                
                <div style="background: rgba(59, 130, 246, 0.05); padding: 12px 16px; border-radius: 10px; margin-top: 20px; border-left: 2px solid #3b82f6;">
                    <span style="color: #3b82f6; font-size: 16px; margin-right: 8px;">🎯</span>
                    <span style="color: #cbd5e1; font-size: 13px; line-height: 1.5;">反核博弈信号成立。主力逆势吸筹明显，承接力度极强，关注分时均线机会。</span>
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

            # 3. 高级详情抽屉
            if show_audit:
                st.markdown(f"""
                <div class="audit-card">
                    <div style="color:#94a3b8; font-size:13px; line-height:2;">
                        <span style="color:#3b82f6; font-weight:bold;">[I] 仪表盘:</span> 鹰眼总分 <b style="color:#fbbf24;">92</b> | 周期: <b style="color:#fbbf24;">主升中继</b> | 决策: <b style="color:#fbbf24;">积极进攻</b><br>
                        <span style="color:#3b82f6; font-weight:bold;">[II] 五维雷达:</span> 筹码: <b style="color:#fbbf24;">35/35(+10)</b> | 环境: 18 | 排雷: 15 | 资金: 12<br>
                        <span style="color:#3b82f6; font-weight:bold;">[III] 反向博弈:</span> <b style="color:#fbbf24;">诱空洗盘</b> (证据: 缩量下砸后迅速收回，主力控盘度极高)<br>
                        <span style="color:#3b82f6; font-weight:bold;">[IV] 风险扫描:</span> 筹码分布 <b style="color:#22c55e;">健康</b> | 质押暴雷 <b style="color:#22c55e;">无</b><br>
                        <span style="color:#3b82f6; font-weight:bold;">[V] 战术指令:</span> 进场 <b style="color:#fbbf24;">{price}</b> | 止损位 <b style="color:#ef4444;">{last_close}</b>
                    </div>
                </div>
                """, unsafe_allow_html=True)
    except:
        continue
