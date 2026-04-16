import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh

# ===================== 全局配置 =====================
st.set_page_config(page_title="鹰眼自选", layout="wide", initial_sidebar_state="collapsed")
st_autorefresh(interval=3000, limit=None, key="eagle_eye_fix_v6")

if 'stock_pool' not in st.session_state:
    st.session_state.stock_pool = ["sz001896", "sz002364", "sh600111", "sz002428"]

HOT_SECTORS = ["AI", "芯片", "算力", "新能源", "光伏", "稀土", "电力"]
STOCK_PY_MAP = {"ynzy":"sz002428", "bfxt":"sh600111", "zhdq":"sz002364", "ynkg":"sz001896"}

# ===================== 顶级 UI 样式引擎 =====================
# 锁定暗色主题，压缩间距，美化指标
st.markdown("""
<style>
    .stApp { background: #020408; font-family: -apple-system, sans-serif; }
    #MainMenu, header, footer { display: none !important; }
    .block-container { padding: 1rem 0.5rem !important; max-width: 800px; }
    
    /* 极致压缩原生容器间距 */
    [data-testid="stVerticalBlock"] { gap: 0.4rem !important; }
    
    /* X 按钮微调 */
    .stButton > button {
        background: transparent !important; border: none !important; color: #475569 !important; font-size: 16px !important; padding: 0 !important; height: auto !important; margin-top: 5px !important;
    }
    .stButton > button:hover { color: #ef4444 !important; }

    /* 徽章与标签样式 */
    .badge { padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: 700; display: inline-block; border: 1px solid transparent; }
    .b-score { background: rgba(239, 68, 68, 0.15); color: #ef4444; border-color: rgba(239, 68, 68, 0.3); }
    .b-sector { background: #e0f2fe; color: #0284c7; } /* 板块 */
    .b-fund { background: #f3f4f6; color: #475569; } /* 资金 */
    
    /* 核心数据美化 */
    .price-val { font-size: 20px; font-weight: bold; }
    .pct-val { font-size: 12px; }
    .mini-data { font-size: 11px; color: #64748b; margin-top: 4px;}
</style>
""", unsafe_allow_html=True)

# --- A. 顶部搜索 ---
col_s1, col_s2 = st.columns([0.85, 0.15])
with col_s1:
    new_code = st.text_input("", placeholder="🔍 输入代码/首字母快速审计", label_visibility="collapsed")
with col_s2:
    if st.button("清空池"): st.session_state.stock_pool = []; st.rerun()

if new_code:
    s = new_code.strip().lower()
    c = "sh"+s if s.isdigit() and s.startswith(('6','9')) else "sz"+s if s.isdigit() else STOCK_PY_MAP.get(s)
    if c and c not in st.session_state.stock_pool:
        st.session_state.stock_pool.insert(0, c); st.rerun()

# ===================== 数据函数（适配 Plotly MACD） =====================
@st.cache_data(ttl=5, show_spinner=False)
def get_data_v6(full_code):
    try:
        # 获取基础数据
        res = requests.get(f"https://qt.gtimg.cn/q={full_code}", timeout=1)
        res.encoding = 'gbk'
        arr = res.text.split("~")
        name, price, pct = arr[1], float(arr[3]), float(arr[32] or 0)
        lclose, open_p = float(arr[4]), float(arr[5])
        
        # 获取近30日K线计算指标
        kres = requests.get(f"https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={full_code},day,,,30,qfq", timeout=1)
        kdata = kres.json()['data'][full_code]['qfqday']
        close_p = [float(x[2]) for x in kdata]
        
        # 均线
        ma5 = round(sum(close_p[-5:])/5, 2)
        ma10 = round(sum(close_p[-10:])/10, 2)

        # 专业 MACD 计算 (5,10,4)
        def get_ema(d, s):
            e = [d[0]]
            for i in range(1, len(d)): e.append((2*d[i]+(s-1)*e[i-1])/(s+1))
            return e
        e5, e10 = get_ema(close_p, 5), get_ema(close_p, 10)
        dif = [e5[i]-e10[i] for i in range(len(e5))]
        dea = get_ema(dif, 4)
        macd = [(dif[i]-dea[i])*2 for i in range(len(dif))]

        # 金叉逻辑：DIF上穿DEA
        is_cross = (dif[-1]>dea[-1] and dif[-2]<=dea[-2])

        # Plotly 数据对
        plot_df = pd.DataFrame({
            'DIFF': dif[-15:], 'DEA': dea[-15:], 'MACD': macd[-15:]
        })

        sector_map = {"001896":"电力", "002364":"电力设备", "600111":"稀土永磁", "002428":"小金属"}
        return {
            "code": full_code[2:], "name": name, "price": price, "pct": pct, "open":open_p,
            "ma5":ma5, "ma10":ma10, "plot_df":plot_df, "is_cross":is_cross,
            "sector":sector_map.get(full_code[2:], "题材")
        }
    except: return None

# ===================== 双行卡牌流渲染 =====================
for code in st.session_state.stock_pool:
    data = get_data_v6(code)
    if not data: continue

    c_hex = "#ef4444" if data['pct'] >= 0 else "#22c55e" # A股红绿
    
    # 使用 container(border=True) 强制锁死卡牌边框
    with st.container(border=True):
        # --- 第一行：身份、评分、实时报价 ---
        r1_l, r1_m, r1_r = st.columns([0.45, 0.45, 0.1])
        with r1_l:
            st.markdown(f"<div style='line-height:1.2; margin-top:2px;'><div><span class='badge b-score'>评分 90</span></div><div style='font-size:16px; font-weight:bold; color:#f0f6fc;'>{data['name']}<span style='font-size:12px; color:#64748b; margin-left:5px;'>{data['code']}</span></div></div>", unsafe_allow_html=True)
        with r1_m:
            st.markdown(f"<div style='text-align:right; line-height:1.2; margin-top:10px;'><span class='price-val' style='color:{c_hex};'>{data['price']:.2f}</span> <span class='pct-val' style='background:{c_hex}15; color:{c_hex}; padding:2px 4px; border-radius:4px;'>{data['pct']}%</span></div>", unsafe_allow_html=True)
        with r1_r:
            if st.button("✕", key=f"del_{code}"):
                st.session_state.pool.remove(code); st.rerun()

        # --- 第二行：均线、专业MACD图、标签 ---
        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True) # 呼吸空间
        
        r2_l, r2_m, r2_r = st.columns([0.35, 0.35, 0.3])
        with r2_l:
            # 开盘溢价判定
            prem = round((data['open'] - float(requests.get(f'https://qt.gtimg.cn/q={code}', timeout=1).text.split('~')[4]))/float(requests.get(f'https://qt.gtimg.cn/q={code}', timeout=1).text.split('~')[4])*100, 2)
            st.markdown(f"""<div class="mini-data"><div>溢价: {prem}%</div><div>MA5: {data['ma5']}</div><div>MA10: {data['ma10']}</div></div>""", unsafe_allow_html=True)
        
        with r2_m:
            # ===================== 核心：Plotly 专业级 MACD (双线+金叉) =====================
            # 严格锁死高度为 60px，绝对不崩排版
            df = data['plot_df']
            fig = go.Figure()
            # 1. 绘制 DIFF (灰) 和 DEA (蓝) 双线
            fig.add_trace(go.Scatter(y=df['DIFF'], mode='lines', line=dict(color='#8b949e', width=1)))
            fig.add_trace(go.Scatter(y=df['DEA'], mode='lines', line=dict(color='#3b82f6', width=1)))
            # 2. 绘制 MACD 紅綠柱
            fig.add_trace(go.Bar(y=df['MACD'], marker_color=['#ef4444' if x>0 else '#22c55e' for x in df['MACD']]))
            # 3. 0轴线与金叉判定
            fig.add_hline(y=0, line_dash="solid", line_color="#30363d", line_width=1)
            # 手机端金叉标记逻辑：只有符合金叉条件才打标记
            if data['is_cross']:
                fig.add_trace(go.Scatter(x=[df.index[-1]], y=[0], mode='markers', marker=dict(symbol='triangle-up', size=10, color='#fbbf24')))
            
            # ===================== 手机窄屏配置 =====================
            fig.update_layout(
                height=60, margin=dict(l=0, r=0, t=10, b=10, pad=0),
                showlegend=False, xaxis_visible=False, yaxis_visible=False,
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                hovermode=False
            )
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            
        with r2_r:
            st.markdown(f"<div style='text-align:right; margin-top:20px;'><span class='badge b-fund' style='margin-bottom:3px;'>资金：+1.2亿</span><br><span class='badge b-sector'>{data['sector']}</span></div>", unsafe_allow_html=True)
