import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go

# ===================== 1. 全局极致压缩配置 =====================
st.set_page_config(page_title="鹰眼自选 v7", layout="wide", initial_sidebar_state="collapsed")

# 注入 CSS：锁定 iPhone 14 Pro Max 宽度，优化标签样式
st.markdown("""
<style>
    .stApp { background: #0d1117; color: #f0f6fc; }
    .block-container { padding: 0.5rem !important; }
    [data-testid="stVerticalBlock"] { gap: 0.2rem !important; }
    
    /* 统一标签样式：资金与题材 */
    .data-label {
        font-size: 11px; padding: 2px 6px; border-radius: 4px;
        background: #161b22; color: #8b949e; border: 1px solid #30363d;
        display: inline-block; margin-right: 4px;
    }
    .fund-positive { color: #ef4444; border-color: rgba(239, 68, 68, 0.3); }
    .sector-hot { background: #23863620; color: #3fb950; border-color: #23863640; }
    
    .price-text { font-size: 20px; font-weight: 800; }
    .ma-text { font-size: 11px; color: #8b949e; line-height: 1.2; }
    
    /* 移除 Streamlit 默认装饰 */
    #MainMenu, header, footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

if 'pool' not in st.session_state:
    st.session_state.pool = ["sz002428", "sh600111", "sz002364"]

# ===================== 2. 数据引擎（优化缓存避免闪烁） =====================
@st.cache_data(ttl=10)
def fetch_eagle_data(code):
    try:
        # 行情数据
        r = requests.get(f"https://qt.gtimg.cn/q={code}", timeout=1.5)
        v = r.text.split('~')
        # K线计算 (30日)
        kr = requests.get(f"https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={code},day,,,30,qfq", timeout=1.5)
        klines = kr.json()['data'][code]['qfqday']
        close_list = [float(x[2]) for x in klines]
        
        # 计算 MACD (5,10,4) 与 均线
        def ema(data, n):
            res = [data[0]]
            for x in data[1:]: res.append((2 * x + (n - 1) * res[-1]) / (n + 1))
            return res
        
        diff = [e5 - e10 for e5, e10 in zip(ema(close_list, 5), ema(close_list, 10))]
        dea = ema(diff, 4)
        macd_hist = [(diff[i] - dea[i]) * 2 for i in range(len(diff))]
        
        return {
            "name": v[1], "price": v[3], "pct": v[32], "open": v[5], "last": v[4],
            "ma5": round(sum(close_list[-5:])/5, 2),
            "ma10": round(sum(close_list[-10:])/10, 2),
            "macd": macd_hist[-15:], # 取最近15天用于展示极窄柱子
            "is_cross": diff[-1] > dea[-1] and diff[-2] <= dea[-2],
            "sectors": ["华为概念", "算力租赁", "预增"] # 模拟热门题材
        }
    except: return None

# ===================== 3. 渲染主界面 =====================
st.markdown("<h3 style='font-size:16px; margin-bottom:10px;'>鹰眼审计终端</h3>", unsafe_allow_html=True)
search = st.text_input("", placeholder="输入代码直接添加...", label_visibility="collapsed")
if search:
    full_code = ("sh"+search if search[0]=='6' else "sz"+search)
    if full_code not in st.session_state.pool:
        st.session_state.pool.insert(0, full_code); st.rerun()

for c in st.session_state.pool:
    d = fetch_eagle_data(c)
    if not d: continue
    
    color = "#ef4444" if float(d['pct']) >= 0 else "#22c55e"
    
    with st.container(border=True):
        # --- 第一行：身份与报价 ---
        c1, c2, c3 = st.columns([0.5, 0.4, 0.1])
        with c1:
            st.markdown(f"<div style='font-size:16px; font-weight:bold;'>{d['name']} <span style='font-size:11px; color:#475569;'>{c[2:].upper()}</span></div>", unsafe_allow_html=True)
        with c2:
            st.markdown(f"<div style='text-align:right;'><span class='price-text' style='color:{color};'>{d['price']}</span> <span style='font-size:12px; color:{color};'>{d['pct']}%</span></div>", unsafe_allow_html=True)
        with c3:
            if st.button("×", key=f"del_{c}"):
                st.session_state.pool.remove(c); st.rerun()

        # --- 第二行：均线、极窄MACD柱、资金题材 ---
        col_m1, col_m2, col_m3 = st.columns([0.25, 0.45, 0.3])
        
        with col_m1:
            st.markdown(f"<div class='ma-text'>MA5: {d['ma5']}<br>MA10: {d['ma10']}</div>", unsafe_allow_html=True)
        
        with col_m2:
            # 极窄 MACD 柱状图 + 并排显示
            fig = go.Figure()
            # 缩窄柱子宽度 (bargap=0.5)
            fig.add_trace(go.Bar(
                y=d['macd'], 
                marker_color=['#ef4444' if x > 0 else '#22c55e' for x in d['macd']],
                width=0.4
            ))
            # 金叉点位显示
            if d['is_cross']:
                fig.add_trace(go.Scatter(x=[14], y=[0], mode='markers', marker=dict(symbol='triangle-up', size=8, color='#FFD700')))
            
            fig.update_layout(
                height=40, margin=dict(l=0, r=0, t=5, b=5),
                showlegend=False, xaxis_visible=False, yaxis_visible=False,
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                bargap=0.6
            )
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            
        with col_m3:
            # 资金与题材标签
            fund_html = "<span class='data-label fund-positive'>资金:+1.2亿</span>"
            sector_html = "".join([f"<span class='data-label sector-hot'>{s}</span>" for s in d['sectors'][:2]])
            st.markdown(f"<div style='text-align:right; line-height:1.8;'>{fund_html}<br>{sector_html}</div>", unsafe_allow_html=True)

# 底部留白适配 iPhone 底部条
st.markdown("<div style='height:50px'></div>", unsafe_allow_html=True)
