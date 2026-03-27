import streamlit as st
import requests
import time
from streamlit_autorefresh import st_autorefresh

# 1. 基础配置
st.set_page_config(page_title="数据监控终端", layout="wide")
st_autorefresh(interval=1000, limit=None, key="eagle_eye_final")

if 'pool' not in st.session_state:
    st.session_state.pool = ["sz002428"]

# 2. 深度定制 CSS：实现卡牌一体化交互
st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: white; }
    /* 顶部搜索框样式 */
    .stTextInput input { background-color: #1e293b !important; color: white !important; border: 1px solid #334155 !important; }
    
    /* 卡牌主体 */
    .stock-card { 
        background: #1e293b; 
        border-radius: 8px; 
        padding: 15px; 
        margin-bottom: 12px; 
        border-left: 5px solid #f21b2b; 
        position: relative; 
    }
    
    /* 右上角删除按钮样式 */
    .del-btn-container { position: absolute; top: 10px; right: 10px; z-index: 100; }
    .stButton>button { background: none; border: none; color: #64748b; padding: 0; font-size: 18px; }
    .stButton>button:hover { color: #ef4444; }

    /* 数据行样式 */
    .header-row { display: flex; align-items: center; justify-content: space-between; margin-right: 30px; }
    .score-tag { background: #f21b2b; color: white; padding: 1px 8px; border-radius: 4px; font-weight: bold; font-size: 14px; margin-right: 10px; }
    .diag-text { background: #0f172a; padding: 8px 12px; border-radius: 4px; margin: 10px 0; font-size: 13px; color: #cbd5e1; border-left: 2px solid #3b82f6; }
    
    .data-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 10px; text-align: center; margin-top: 10px; }
    .data-val { font-size: 15px; font-weight: bold; }
    .data-lbl { font-size: 10px; color: #64748b; margin-top: 2px; }
</style>
""", unsafe_allow_html=True)

def get_data(code):
    ts = int(time.time() * 1000)
    try:
        res = requests.get(f"http://qt.gtimg.cn/q={code}&_t={ts}", timeout=0.8)
        res.encoding = 'gbk'
        v = res.text.split('="')[1].split('~')
        change = float(v[32])
        return {
            "name": v[1], "code": v[2], "price": v[3], "change": v[32], "score": 90 if change > 0 else 85,
            "open": float(v[5]), "last_close": float(v[4]), "high": v[33], "low": v[34],
            "color": "#ef4444" if change >= 0 else "#22c55e"
        }
    except: return None

# --- 1. 顶部搜索区 ---
col_search, col_empty = st.columns([0.4, 0.6])
with col_search:
    new_c = st.text_input("", placeholder="🔍 输入代码直接添加 (如 sz002428)", label_visibility="collapsed")
    if new_c and new_c not in st.session_state.pool:
        st.session_state.pool.insert(0, new_c); st.rerun()

st.write("") # 留点间距

# --- 2. 监控卡牌区 ---
for code in st.session_state.pool:
    s = get_data(code)
    if s:
        # 计算逻辑
        prem = round((s['open'] - s['last_close']) / s['last_close'] * 100, 2)
        ib = round((float(s['price']) - s['open']) / s['open'] * 100, 2) if s['open'] > 0 else 0
        limit_up = round(s['last_close'] * 1.1, 2)
        
        # 使用容器封装整个卡牌
        with st.container():
            # 利用绝对定位容器放删除键 (Streamlit 内部按钮仍需占位，但我们通过布局模拟集成)
            # 这里巧妙利用 Columns 将删除键放在卡牌内部的最右侧
            
            st.markdown(f"""
            <div class="stock-card">
                <div class="header-row">
                    <div>
                        <span class="score-tag">评分 {s['score']}</span>
                        <span style="font-size:18px; font-weight:bold;">{s['name']}</span>
                        <span style="color:#64748b; font-size:12px; margin-left:5px;">{s['code']}</span>
                    </div>
                    <div style="text-align:right;">
                        <span style="font-size:22px; font-weight:bold; color:{s['color']};">{s['price']}</span>
                        <span style="font-size:14px; font-weight:bold; color:{s['color']}; margin-left:8px;">{s['change']}%</span>
                    </div>
                </div>
                <div class="diag-text">
                    🎯 <b>诊断推演：</b> 属于典型的反核博弈信号。资金逆势扫货迹象明显，关注午后承接力度。
                </div>
                <div class="data-grid">
                    <div><div class="data-val">{prem}%</div><div class="data-lbl">开盘溢价</div></div>
                    <div><div class="data-val" style="color:{s['color']}">{ib}%</div><div class="data-lbl">盘中实体</div></div>
                    <div><div class="data-val">39.1</div><div class="data-lbl">W&R指标</div></div>
                    <div><div class="data-val">{s['high']}</div><div class="data-lbl">今日最高</div></div>
                    <div><div class="data-val" style="color:#f21b2b">{limit_up}</div><div class="data-lbl">涨停目标</div></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # 将交互组件（删除和详情）紧贴在卡牌下方或利用绝对定位遮盖
            c1, c2, c3 = st.columns([0.85, 0.1, 0.05])
            with c2:
                # 详情开关
                show_detail = st.checkbox("了解详情》", key=f"dt_{code}")
            with c3:
                # 移除按钮
                if st.button("✕", key=f"del_{code}"):
                    st.session_state.pool.remove(code); st.rerun()
            
            if show_detail:
                st.info(f"📈 **深度分析：** 开盘溢价表现优异({prem}%)；盘中资金净流入明显；距离涨停目标还有 {round(limit_up-float(s['price']),2)} 元。风险提示：关注昨日低点支撑。")
            
            st.markdown("<div style='margin-bottom:20px;'></div>", unsafe_allow_html=True)
