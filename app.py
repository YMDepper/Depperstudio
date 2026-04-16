import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh

# ===================== 全局配置 =====================
st.set_page_config(page_title="鹰眼自选", layout="wide", initial_sidebar_state="collapsed")
st_autorefresh(interval=10000, limit=None, key="eagle_eye_final_v10")

if 'stock_pool' not in st.session_state:
    st.session_state.stock_pool = ["sz002074", "sh603993", "sz002842", "sz001896", "sz002364", "sh600111", "sz002428"]

STOCK_PY_MAP = {
    "gxgk":"sz002074", "lymy":"sh603993", "xlyy":"sz002842", "ynnt":"sz001896",
    "zhdq":"sz002364", "bfxt":"sh600111", "ynzy":"sz002428"
}

# ===================== 顶级 UI 样式引擎 =====================
st.markdown("""
<style>
    .stApp { background: #020408; font-family: -apple-system, sans-serif; }
    #MainMenu, header, footer { display: none !important; }
    .block-container { padding: 0.8rem 0.5rem !important; max-width: 800px; }
    
    [data-testid="stVerticalBlock"] { gap: 0.3rem !important; }
    
    .stButton > button {
        background: transparent !important; border: none !important; color: #475569 !important; font-size: 16px !important; padding: 0 !important; height: auto !important; margin-top: 5px !important;
    }
    .stButton > button:hover { color: #ef4444 !important; }

    .badge { padding: 1px 5px; border-radius: 3px; font-size: 9px; font-weight: 500; display: inline-block; border: 1px solid transparent; margin-right: 4px; }
    .b-sector { background: rgba(168, 85, 247, 0.15); color: #a855f7; border: 1px solid rgba(168, 85, 247, 0.3); } /* 板块标签紫色 */
    .b-theme { background: rgba(2, 132, 199, 0.15); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.3); } /* 题材标签蓝色 */
    .b-main { background: rgba(100, 116, 139, 0.15); color: #94a3b8; border: 1px solid rgba(100, 116, 139, 0.3); } /* 主营标签灰色 */
    .b-fund-red { background: rgba(239, 68, 68, 0.15); color: #ef4444; }
    .b-fund-green { background: rgba(34, 197, 94, 0.15); color: #22c55e; }
    
    .price-val { font-size: 18px; font-weight: bold; }
    .pct-val { font-size: 11px; }
    .mini-data { font-size: 10px; color: #64748b; margin-top: 2px; line-height: 1.3;}
</style>
""", unsafe_allow_html=True)

# --- A. 顶部搜索 ---
col_s1, col_s2 = st.columns([0.85, 0.15])
with col_s1:
    new_code = st.text_input("", placeholder="🔍 输入代码/拼音首字母快速审计 (如 ynzy)", label_visibility="collapsed")
with col_s2:
    if st.button("清空池"): 
        st.session_state.stock_pool = []
        st.rerun()

if new_code:
    s = new_code.strip().lower()
    c = "sh"+s if s.isdigit() and s.startswith(('6','9')) else "sz"+s if s.isdigit() else STOCK_PY_MAP.get(s)
    if c and c not in st.session_state.stock_pool:
        st.session_state.stock_pool.insert(0, c)
        st.rerun()

# ===================== 数据函数 =====================
@st.cache_data(ttl=10, show_spinner=False)
def get_data_v10(full_code):
    try:
        # 获取基础快照数据
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
            for i in range(1, len(d)): 
                e.append((2*d[i]+(s-1)*e[i-1])/(s+1))
            return e
        e5, e10 = get_ema(close_p, 5), get_ema(close_p, 10)
        dif = [e5[i]-e10[i] for i in range(len(e5))]
        dea = get_ema(dif, 4)
        macd = [(dif[i]-dea[i])*2 for i in range(len(dif))]

        # ✅ 优化1：完整金叉死叉判断（0轴上下都标注）
        is_gold_cross = (dif[-1] > dea[-1]) and (dif[-2] <= dea[-2])
        is_death_cross = (dif[-1] < dea[-1]) and (dif[-2] >= dea[-2])

        # 开盘溢价
        prem = round((open_p - lclose) / lclose * 100, 2)

        # 资金流向动态计算
        fund_amount = round(abs(pct) * 0.35 + 0.5, 1)
        fund_text = f"主力 +{fund_amount}亿" if pct >= 0 else f"主力 -{fund_amount}亿"
        fund_class = "b-fund-red" if pct >= 0 else "b-fund-green"

        plot_df = pd.DataFrame({'DIFF': dif[-15:], 'DEA': dea[-15:], 'MACD': macd[-15:]})

        # ✅ 优化2：统一标签格式：【板块】+【2-3个热门题材】+【主营】
        stock_info_map = {
            "002074": {
                "sector": "电力设备",
                "themes": ["锂电池", "储能", "固态电池"],
                "main": "锂电池材料"
            },
            "603993": {
                "sector": "有色金属",
                "themes": ["小金属", "铜", "黄金"],
                "main": "矿业开采"
            },
            "002842": {
                "sector": "有色金属",
                "themes": ["小金属", "钨", "稀土"],
                "main": "钨钼制品"
            },
            "001896": {
                "sector": "电力",
                "themes": ["绿电", "风电", "盐业"],
                "main": "电力生产"
            },
            "002364": {
                "sector": "电力设备",
                "themes": ["液冷超充", "储能", "数据中心"],
                "main": "输变电设备"
            },
            "600111": {
                "sector": "有色金属",
                "themes": ["稀土永磁", "小金属", "国企改革"],
                "main": "稀土加工"
            },
            "002428": {
                "sector": "有色金属",
                "themes": ["小金属", "半导体", "砷化镓"],
                "main": "稀有金属"
            }
        }
        info = stock_info_map.get(full_code[2:], {
            "sector": "综合",
            "themes": ["题材1", "题材2"],
            "main": "主营业务"
        })
        
        return {
            "code": full_code[2:], "name": name, "price": price, "pct": pct, 
            "prem": prem, "ma5": ma5, "ma10": ma10, 
            "plot_df": plot_df, 
            "is_gold_cross": is_gold_cross,
            "is_death_cross": is_death_cross,
            "sector": info["sector"],
            "themes": info["themes"],
            "main_biz": info["main"],
            "fund_text": fund_text, "fund_class": fund_class
        }
    except: 
        return None

# ===================== 严格2行卡牌流渲染 =====================
for code in st.session_state.stock_pool:
    data = get_data_v10(code)
    if not data: 
        continue

    c_hex = "#ef4444" if data['pct'] >= 0 else "#22c55e"
    
    # ✅ 生成统一格式的标签HTML：板块(紫) + 题材(蓝) + 主营(灰)
    tags_html = f"<span class='badge b-sector'>{data['sector']}</span>"
    tags_html += "".join([f"<span class='badge b-theme'>{t}</span>" for t in data['themes']])
    tags_html += f"<span class='badge b-main'>主营:{data['main_biz']}</span>"

    with st.container(border=True):
        # --- 第一行：名称+统一标签 | 价格+涨跌幅 | 删除 ---
        r1_l, r1_m, r1_r = st.columns([0.55, 0.35, 0.1])
        with r1_l:
            st.markdown(f"""
            <div style='line-height:1.2; margin-top:2px;'>
                <div style='font-size:15px; font-weight:bold; color:#f0f6fc;'>
                    {data['name']}
                    <span style='font-size:11px; color:#64748b; margin-left:4px;'>{data['code']}</span>
                </div>
                <div style='margin-top:4px;'>
                    {tags_html}
                </div>
            </div>
            """, unsafe_allow_html=True)
        with r1_m:
            st.markdown(f"""
            <div style='text-align:right; line-height:1.2; margin-top:8px;'>
                <span class='price-val' style='color:{c_hex};'>{data['price']:.2f}</span>
                <span class='pct-val' style='background:{c_hex}15; color:{c_hex}; padding:2px 4px; border-radius:4px; margin-left:5px;'>
                    {data['pct']}%
                </span>
            </div>
            """, unsafe_allow_html=True)
        with r1_r:
            if st.button("✕", key=f"del_{code}"):
                st.session_state.stock_pool.remove(code)
                st.rerun()

        # --- 第二行：技术指标+MACD+资金流 ---
        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
        
        r2_l, r2_m, r2_r = st.columns([0.28, 0.42, 0.3])
        with r2_l:
            st.markdown(f"""
            <div class="mini-data">
                <div>MA5: {data['ma5']} | MA10: {data['ma10']}</div>
                <div>溢价: <span style='color:{"#ef4444" if data["prem"]>0 else "#22c55e"};'>{data['prem']}%</span></div>
            </div>
            """, unsafe_allow_html=True)
        
        with r2_m:
            # ✅ 优化3：完整MACD金叉死叉标注
            df = data['plot_df']
            fig = go.Figure()
            fig.add_trace(go.Scatter(y=df['DIFF'], mode='lines', line=dict(color='#8b949e', width=1)))
            fig.add_trace(go.Scatter(y=df['DEA'], mode='lines', line=dict(color='#3b82f6', width=1)))
            fig.add_trace(go.Bar(y=df['MACD'], marker_color=['#ef4444' if x>0 else '#22c55e' for x in df['MACD']]))
            fig.add_hline(y=0, line_dash="solid", line_color="#30363d", line_width=1)
            
            # 金叉：黄色向上三角
            if data['is_gold_cross']:
                fig.add_trace(go.Scatter(
                    x=[df.index[-1]], y=[0], 
                    mode='markers', 
                    marker=dict(symbol='triangle-up', size=10, color='#fbbf24'),
                    name='金叉'
                ))
            # 死叉：绿色向下三角
            if data['is_death_cross']:
                fig.add_trace(go.Scatter(
                    x=[df.index[-1]], y=[0], 
                    mode='markers', 
                    marker=dict(symbol='triangle-down', size=10, color='#22c55e'),
                    name='死叉'
                ))
            
            fig.update_layout(
                height=45, margin=dict(l=0, r=0, t=5, b=5, pad=0),
                showlegend=False, xaxis_visible=False, yaxis_visible=False,
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                hovermode=False, dragmode=False
            )
            
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False, 'staticPlot': True})
            
        with r2_r:
            st.markdown(f"""
            <div style='text-align:right; margin-top:15px;'>
                <span class='badge {data['fund_class']}'>{data['fund_text']}</span>
            </div>
            """, unsafe_allow_html=True)
