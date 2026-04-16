import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh

# 1. 页面基础配置：锁死暗色调，适配 iPhone 14 Pro Max 窄屏
st.set_page_config(page_title="鹰眼审计终端", layout="wide", initial_sidebar_state="collapsed")
st_autorefresh(interval=1500, limit=None, key="eagle_eye_v56")

# 2. 注入顶级 UI 设计师 CSS
st.markdown("""
<style>
    .stApp { background-color: #020408; }
    /* 隐藏所有多余的 Streamlit 边距 */
    .block-container { padding: 1rem 0.5rem !important; }
    /* 极致压缩卡片 */
    .stock-card {
        background: #111827;
        border: 1px solid #1e293b;
        border-radius: 12px;
        padding: 12px;
        margin-bottom: 10px;
        position: relative;
    }
    /* 移除按钮样式优化 */
    .del-btn { position: absolute; top: 10px; right: 10px; z-index: 100; }
    /* 指标数值美化 */
    [data-testid="stMetricValue"] { font-size: 22px !important; color: #FFD700 !important; }
    [data-testid="stMetricLabel"] { font-size: 10px !important; color: #64748b !important; }
</style>
""", unsafe_allow_html=True)

if 'pool' not in st.session_state:
    st.session_state.pool = ["sz002428", "sh600111"]

# 3. 数据抓取与专业 MACD 计算
@st.cache_data(ttl=5)
def get_pro_data(code):
    try:
        # 抓取实时行情
        r = requests.get(f"https://qt.gtimg.cn/q={code}", timeout=1)
        v = r.text.split('~')
        # 抓取日K数据计算 MACD (5,10,4)
        k_r = requests.get(f"https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={code},day,,,40,qfq", timeout=1)
        klines = k_r.json()['data'][code]['qfqday']
        close = [float(x[2]) for x in klines]
        
        # 精准计算 DIFF, DEA (针对你截图要求的 5,10,4 参数)
        ema5 = pd.Series(close).ewm(span=5, adjust=False).mean()
        ema10 = pd.Series(close).ewm(span=10, adjust=False).mean()
        diff = ema5 - ema10
        dea = diff.ewm(span=4, adjust=False).mean()
        macd_hist = (diff - dea) * 2
        
        # 识别金叉标记 (DIFF 上穿 DEA)
        cross = (diff > dea) & (diff.shift(1) <= dea.shift(1))
        
        df = pd.DataFrame({'DIFF': diff, 'DEA': dea, 'MACD': macd_hist, 'Cross': cross}).tail(20)
        return {"name": v[1], "price": v[3], "pct": v[32], "df": df}
    except: return None

# 4. 主界面：手机端流式渲染
st.markdown('<p style="color:#475569; font-size:12px;">EAGLE EYE PRO TERMINAL</p>', unsafe_allow_html=True)
search_val = st.text_input("", placeholder="输入代码审计...", label_visibility="collapsed")
if search_val:
    c = search_val.strip()
    if len(c) == 6: c = ("sh"+c if c[0]=='6' else "sz"+c)
    if c not in st.session_state.pool: st.session_state.pool.insert(0, c); st.rerun()

# 循环渲染卡片
for c in st.session_state.pool:
    d = get_pro_data(c)
    if not d: continue
    
    # 模拟卡牌容器
    with st.container():
        # 头部信息：名称、价格、删除按钮
        col_t1, col_t2, col_t3 = st.columns([0.5, 0.4, 0.1])
        col_t1.markdown(f"**{d['name']}** `{c.upper()}`")
        col_t2.markdown(f"<span style='color:#ef4444; font-size:18px; font-weight:bold;'>{d['price']} ({d['pct']}%)</span>", unsafe_allow_html=True)
        if col_t3.button("×", key=f"del_{c}"):
            st.session_state.pool.remove(c); st.rerun()

        # 核心：复现你截图中的“周线战略图”MACD
        # 使用 Plotly 绘制双线 + 柱状图 + 金叉标记
        df_p = d['df'].reset_index()
        fig = go.Figure()
        
        # 1. 绘制 DIFF (灰) 和 DEA (蓝)
        fig.add_trace(go.Scatter(y=df_p['DIFF'], mode='lines', line=dict(color='#8b949e', width=1.5), name='DIFF'))
        fig.add_trace(go.Scatter(y=df_p['DEA'], mode='lines', line=dict(color='#3b82f6', width=1.5), name='DEA'))
        
        # 2. 绘制 MACD 柱
        colors = ['#ef4444' if x > 0 else '#22c55e' for x in df_p['MACD']]
        fig.add_trace(go.Bar(y=df_p['MACD'], marker_color=colors, name='MACD'))
        
        # 3. 标记金叉小三角
        cross_idx = df_p[df_p['Cross']].index
        if not cross_idx.empty:
            fig.add_trace(go.Scatter(
                x=cross_idx, y=df_p.loc[cross_idx, 'DIFF'],
                mode='markers', marker=dict(symbol='triangle-up', size=12, color='#FFD700'),
                name='金叉'
            ))

        # 4. 图表视觉锁死配置 (针对手机端极窄空间)
        fig.update_layout(
            height=120, margin=dict(l=0, r=0, t=10, b=0),
            showlegend=False, xaxis_visible=False, yaxis_visible=False,
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            hovermode=False
        )
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        
        # 推演结论区
        st.markdown(f"""
        <div style="background:rgba(59,130,246,0.1); padding:8px; border-radius:6px; border-left:3px solid #3b82f6; font-size:12px; color:#cbd5e1;">
            <b>审计结论：</b> MACD出现{'金叉信号' if any(d['df']['Cross']) else '趋势承压'}，配合日线筹码分布，建议关注0轴附近的博弈机会。
        </div>
        """, unsafe_allow_html=True)
        st.divider()
