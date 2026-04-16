import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh

# ===================== 全局 =====================
st.set_page_config(page_title="鹰眼自选", layout="wide", initial_sidebar_state="collapsed")
st_autorefresh(interval=10000, limit=None, key="min_final")

if 'stock_pool' not in st.session_state:
    st.session_state.stock_pool = ["sz001896", "sz002364", "sh600111", "sz002428", "sz002074", "sh603993"]

STOCK_PY_MAP = {
    "ynnt":"sz001896", "zhdq":"sz002364", "bfxt":"sh600111", "ynzy":"sz002428",
    "gxgk":"sz002074", "lymy":"sh603993"
}

# ===================== 极简CSS（零冗余） =====================
st.markdown("""
<style>
    .stApp { background:#020408; }
    #MainMenu,header,footer {display:none;}
    .block-container {padding:6px 8px!important; max-width:800px;}
    [data-testid="stVerticalBlock"] {gap:0px!important;}

    /* 按钮 */
    .stButton>button {background:none!important; border:none!important; color:#555!important; font-size:16px!important; padding:0!important;}
    .stButton>button:hover {color:#ef4444!important;}

    /* 标签 */
    .tag {padding:1px 4px; border-radius:3px; font-size:8px; display:inline-block; margin-right:3px;}
    .tag-sector {background:rgba(168,85,247,.15); color:#a855f7; border:1px solid rgba(168,85,247,.2);}
    .tag-theme {background:rgba(56,189,248,.15); color:#38bdf8; border:1px solid rgba(56,189,248,.2);}
    .tag-main {background:rgba(100,116,139,.15); color:#94a3b8; border:1px solid rgba(100,116,139,.2);}

    /* 资金/涨跌 */
    .side-badge {font-size:9px; padding:1px 4px; border-radius:3px; text-align:center;}
</style>
""", unsafe_allow_html=True)

# ===================== 搜索栏 =====================
a1,a2 = st.columns([0.9,0.1])
with a1:
    inp = st.text_input("", placeholder="🔍 代码/首字母", label_visibility="collapsed")
with a2:
    if st.button("清空"): st.session_state.stock_pool=[]; st.rerun()
if inp:
    s=inp.strip().lower()
    c="sh"+s if s.isdigit() and s[0] in '69' else "sz"+s if s.isdigit() else STOCK_PY_MAP.get(s)
    if c and c not in st.session_state.stock_pool: st.session_state.stock_pool.insert(0,c); st.rerun()

# ===================== 数据 =====================
@st.cache_data(ttl=10, show_spinner=False)
def load(code):
    try:
        r=requests.get(f"https://qt.gtimg.cn/q={code}", timeout=1)
        r.encoding='gbk'
        arr=r.text.split("~")
        name,px,zdf=arr[1],float(arr[3]),float(arr[32]or 0)
        lc,op=float(arr[4]),float(arr[5])

        kr=requests.get(f"https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={code},day,,,30,qfq", timeout=1)
        kd=kr.json()['data'][code]['qfqday']
        cl=[float(x[2]) for x in kd]
        ma5=round(sum(cl[-5:])/5,2)
        ma10=round(sum(cl[-10:])/10,2)
        prem=round((op-lc)/lc*100,2)

        def ema(d,s):
            e=[d[0]]
            for i in range(1,len(d)):e.append((2*d[i]+(s-1)*e[i-1])/(s+1))
            return e
        e5,e10=ema(cl,5),ema(cl,10)
        dif=[e5[i]-e10[i] for i in range(len(e5))]
        dea=ema(dif,4)
        macd=[(dif[i]-dea[i])*2 for i in range(len(dif))]
        gold=(dif[-1]>dea[-1])&(dif[-2]<=dea[-2])
        death=(dif[-1]<dea[-1])&(dif[-2]>=dea[-2])
        df=pd.DataFrame({'dif':dif[-15:],'dea':dea[-15:],'macd':macd[-15:]})

        fund=round(abs(zdf)*0.35+0.5,1)
        fund_txt=f"+{fund}亿" if zdf>=0 else f"-{fund}亿"
        fund_cls="#ef4444" if zdf>=0 else "#22c55e"
        pct_cls="rgba(239,68,68,.15)" if zdf>=0 else "rgba(34,197,94,.15)"

        info={
            "001896":{"s":"电力","t":["绿电","风电"],"m":"电力生产"},
            "002364":{"s":"电力设备","t":["液冷","储能"],"m":"输变电"},
            "600111":{"s":"有色金属","t":["稀土","小金属"],"m":"稀土加工"},
            "002428":{"s":"有色金属","t":["小金属","半导体"],"m":"稀有金属"},
            "002074":{"s":"电力设备","t":["锂电","储能"],"m":"锂电材料"},
            "603993":{"s":"有色金属","t":"铜钼","m":"矿业"}
        }.get(code[2:],{"s":"综合","t":["题材"],"m":"主营"})

        return {"name":name,"px":px,"zdf":zdf,"ma5":ma5,"ma10":ma10,"prem":prem,
                "df":df,"gold":gold,"death":death,"s":info["s"],"t":info["t"],"m":info["m"],
                "fund_txt":fund_txt,"fund_cls":fund_cls,"pct_cls":pct_cls}
    except:
        return None

# ===================== 渲染（极致压缩排版） =====================
for code in st.session_state.stock_pool:
    d=load(code)
    if not d: continue
    red=d["zdf"]>=0
    c1="#ef4444" if red else "#22c55e"

    # 标签拼接
    tags=f'<span class="tag tag-sector">{d["s"]}</span>'
    tags+="".join([f'<span class="tag tag-theme">{t}</span>' for t in d["t"]])
    tags+=f'<span class="tag tag-main">{d["m"]}</span>'

    with st.container(border=True):
        # ========== 第一行：左（名称+标签） 右（大价格+竖排涨跌/资金） ==========
        L, R, X = st.columns([0.62, 0.28, 0.1])
        with L:
            st.markdown(f"""
            <div style="line-height:1.1;">
                <div style="font-size:15px; font-weight:700; color:#f8fafc;">{d['name']} <span style="font-size:10px; color:#64748b;">{code[2:]}</span></div>
                <div style="margin-top:3px;">{tags}</div>
            </div>
            """, unsafe_allow_html=True)
        with R:
            st.markdown(f"""
            <div style="display:flex; align-items:center; justify-content:flex-end; gap:8px; height:100%;">
                <div style="font-size:24px; font-weight:700; color:{c1};">{d['px']:.2f}</div>
                <div style="display:flex; flex-direction:column; gap:2px;">
                    <div class="side-badge" style="background:{d['pct_cls']}; color:{c1};">{d['zdf']}%</div>
                    <div class="side-badge" style="background:rgba(0,0,0,0); color:{d['fund_cls']};">{d['fund_txt']}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        with X:
            if st.button("×", key=f"x_{code}"): st.session_state.stock_pool.remove(code); st.rerun()

        # ========== 第二行：纯MACD图 + 图下一行小字指标 ==========
        # MACD
        fig=go.Figure()
        fig.add_trace(go.Scatter(y=d["df"]["dif"], line=dict(color='#888', width=1)))
        fig.add_trace(go.Scatter(y=d["df"]["dea"], line=dict(color='#3b82f6', width=1)))
        fig.add_trace(go.Bar(y=d["df"]["macd"], marker_color=[c1 if v>0 else "#22c55e" for v in d["df"]["macd"]]))
        fig.add_hline(y=0, line_color="#333", line_width=1)
        if d["gold"]: fig.add_trace(go.Scatter(x=[14],y=[0],mode="markers",marker=dict(symbol="triangle-up",size=9,color="#fbbf24")))
        if d["death"]: fig.add_trace(go.Scatter(x=[14],y=[0],mode="markers",marker=dict(symbol="triangle-down",size=9,color="#22c55e")))
        fig.update_layout(height=38, margin=dict(l=0,r=0,t=0,b=0), showlegend=False, xaxis_visible=False, yaxis_visible=False, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", hovermode=False, dragmode=False)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False, "staticPlot":True})

        # 图下小字一行（MA5 MA10 溢价）
        st.markdown(f"""
        <div style="font-size:9px; color:#64748b; text-align:center; margin-top:-6px;">
            MA5:{d['ma5']}  MA10:{d['ma10']}  溢价:<span style="color:{c1};">{d['prem']}%</span>
        </div>
        """, unsafe_allow_html=True)
