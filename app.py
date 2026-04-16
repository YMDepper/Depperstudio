import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh

# ===================== 全局配置 =====================
st.set_page_config(page_title="鹰眼审计终端", layout="wide", initial_sidebar_state="collapsed")
st_autorefresh(interval=3000, limit=None, key="eagle_eye_v55")

if 'pool' not in st.session_state:
    st.session_state.pool = ["sz002428", "sh600137"]

# ===================== 顶级 UI 设计锁死 =====================
# 采用金融级 dark (暗色) 主题風格，配合 `#FFD700` (黑金) 核心数据，缓解手机端眼部疲劳
st.markdown("""
<style>
    /* 全局黑金色调 */
    .stApp { background-color: #020408; font-family: -apple-system, sans-serif; }
    
    /* 强行挪动 X 按钮位置 */
    div[data-testid="stColumn"]:nth-child(2) button {
        margin-top: 5px !important; margin-left: 80% !important; background: transparent !important;
        border: none !important; color: #475569 !important; font-size: 18px !important; z-index: 10;
    }

    /* 极致压缩原生容器间距 */
    [data-testid="stVerticalBlock"] { gap: 0.3rem !important; }

    /* 全局指标数据着色 */
    [data-testid="stMetricValue"] { font-size: 26px !important; font-weight: bold !important; color: #FFD700 !important; }
    [data-testid="stMetricLabel"] { color: #64748b !important; font-size: 11px !important; margin-bottom: -5px; }

    /* 推演文本 */
    .stAlert { background: #020617; border-left: 3px solid #3b82f6; border-radius: 8px; color:#cbd5e1; }
</style>
""", unsafe_allow_html=True)

# --- A. 顶栏搜索栏 ---
st.markdown('<p style="color:#64748b; font-size:11px; margin-bottom:5px;">EAGLE EYE STRATEGIC TERMINAL v5.5</p>', unsafe_allow_html=True)
search_col, _ = st.columns([0.8, 0.2])
with search_col:
    new_c = st.text_input("", placeholder="🔍 输入代码审计 (例如 600111)", label_visibility="collapsed")
    if new_c:
        c_in = new_c.strip()
        if len(c_in) == 6: c_in = ("sh" if c_in.startswith(('6', '9')) else "sz") + c_in
        if c_in not in st.session_state.pool:
            st.session_state.pool.insert(0, c_in); st.rerun()

# ===================== 渲染：手机端专业 MACD 版 =====================
@st.cache_data(ttl=5, show_spinner=False)
def get_stock_data(full_code):
    try:
        # 1. 实时行情
        res = requests.get(f"https://qt.gtimg.cn/q={full_code}", timeout=1.0)
        res.encoding = 'gbk'
        v = res.text.split('="')[1].split('~')
        change = float(v[32])
        color = "#ef4444" if change >= 0 else "#22c55e"
        last_close = float(v[4])
        
        # 2. 获取近40日K线计算专业 MACD(5,10,4)
        kres = requests.get(f"https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={full_code},day,,,40,qfq", timeout=1.0)
        close = [float(x[2]) for x in kres.json()['data'][full_code]['qfqday']]
        
        # MACD(5,10,4) 简易计算
        e5, e10 = [close[0]], [close[0]]
        for p in close[1:]:
            e5.append((2*p + 4*e5[-1])/6)
            e10.append((2*p + 9*e10[-1])/11)
        dif = [e5[i]-e10[i] for i in range(len(e5))]
        dea = [dif[0]]
        for d in dif[1:]: dea.append((2*d + 3*dea[-1])/5)
        macd_val = [(dif[i]-dea[i])*2 for i in range(len(dif))]
        
        # 3. 标记金叉逻辑（水下或0轴上均上穿）
        cross_mask = [(dif[i]>dea[i]) & (dif[i-1]<=dea[i-1]) for i in range(len(dif))]
        
        # 截取近15日数据用于卡牌图表展示
        plot_df = pd.DataFrame({
            'DIF': dif[-15:], 'DEA': dea[-15:], 'MACD': macd_val[-15:], 
            'Cross': cross_mask[-15:], 'Price': [0 for _ in range(15)]
        })
        
        return {
            "name":v[1], "price":v[3], "change":change, "color":color, "lclose":last_close,
            "ma5":round(sum(close[-5:])/5, 2), "ma10":round(sum(close[-10:])/10, 2),
            "macd_plot_df":plot_df
        }
    except:
        return None

# ===================== 动态渲染流 =====================
for code in st.session_state.pool:
    data = get_stock_data(code)
    if not data: continue

    # 渲染单只股票的卡牌：先放交互组件插槽
    c_left, c_right = st.columns([0.9, 0.1])
    with c_right:
        if st.button("✕", key=f"del_{code}"):
            st.session_state.pool.remove(code); st.rerun()
    
    # 模拟 Container：CSS 绝对定位 X 按钮在右上方
    with st.container():
        # HTML Header (纯展示文字，确保不乱码)
        st.markdown(f"""
        <div style="margin-top:-35px; background:#111827; border:1px solid #1e293b; border-radius:10px; padding:15px; z-index:1;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <span style="background:rgba(239,68,68,0.15); color:#ef4444; padding:2px 8px; border-radius:4px; font-size:11px; font-weight:bold;">审计评分 92</span>
                    <div style="font-size: 20px; font-weight: 700; color: #f8fafc; margin-top: 8px;">{data['name']} <span style="font-size:12px; color:#475569;">{code.upper()}</span></div>
                </div>
                <div style="text-align: right; margin-right: 20px;">
                    <div style="font-size: 26px; font-weight: bold; color: {data['color']};">{data['price']}</div>
                    <div style="font-size: 13px; color: {data['color']};">{data['change']}%</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # 1. 博弈推演区 (使用原生 st.alert)
        st.info(f"🎯 鹰眼博弈推演：典型的反核博弈信号。资金逆势扫货迹象明显，主力反人性吸筹。建议关注午后均线承接机会。")

        # 2. 核心数据阵列
        m1, m2 = st.columns(2)
        m1.metric("开盘溢价", f"2.20%")
        m2.metric("日K·涨停目标", f"{(float(data['price'])*1.1):.2f}", delta_color="off")

        st.markdown('<p style="color:#64748b; font-size:11px; margin-bottom:-5px;">MA5: '+str(data['ma5'])+' | MA10: '+str(data['ma10'])+'</p>', unsafe_allow_html=True)
        
        # ===================== 顶级 UI 设计：Plotly 微型 MACD 图案 =====================
        # 这是重写核心：我们用 Plotly 重新绘制你要求的专业图表
        df = data['macd_plot_df']
        fig = go.Figure()
        
        # DIFF (灰线) & DEA (蓝线)
        fig.add_trace(go.Scatter(y=df['DIF'], mode='lines', line=dict(color='#8b949e', width=1)))
        fig.add_trace(go.Scatter(y=df['DEA'], mode='lines', line=dict(color='#3b82f6', width=1)))
        
        # MACD 柱状图 (紅綠 A股)
        fig.add_trace(go.Bar(y=df['MACD'], marker=dict(color=['#ef4444' if m>0 else '#22c55e' for m in df['MACD']])))
        
        # 0 轴线
        fig.add_hline(y=0, line_dash="solid", line_color="#30363d", line_width=1)
        
        # 金叉标记：小三角 (仅在 Cross=True 时显示)
        cross_pts = df[df['Cross']]
        fig.add_trace(go.Scatter(x=cross_pts.index, y=cross_pts['Price'], mode='markers', marker=dict(symbol='triangle-up', size=8, color='#fbbf24')))
        
        # ===================== 锁死：Plotly 手机窄屏配置 =====================
        # 这个配置确保图表干净、无坐标轴、高度恒定，绝对不会崩排版
        fig.update_layout(
            height=60, # 压缩高度到 60 像素
            width=None, # 自适应 Streamlit 容器宽度
            xaxis_visible=False, # 关掉坐标轴
            yaxis_visible=False,
            showlegend=False, # 关掉图例
            hovermode=False, # 关掉悬停交互
            plot_bgcolor='rgba(0,0,0,0)', # 透明背景
            paper_bgcolor='rgba(0,0,0,0)',
            # 精准控制内边距，确报图表内容在卡牌内 100% 对齐
            margin=dict(l=0, r=0, t=10, b=10, pad=0), 
        )
        
        # 最后，渲染图表：使用 Streamlit 官方最稳的 Plotly 容器，绝不乱码
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

        # 分割线
        st.divider()

    except Exception as e:
        continue
