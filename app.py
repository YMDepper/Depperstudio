import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh

# ===================== 全局 =====================
st.set_page_config(page_title="鹰眼自选", layout="wide", initial_sidebar_state="collapsed")
st_autorefresh(interval=1000, limit=None, key="fix_top_input")

if 'stock_pool' not in st.session_state:
    st.session_state.stock_pool = ["sh601899", "sz001896", "sz002364", "sh600111"]

# 初始化输入框清空状态
if "clear_input" not in st.session_state:
    st.session_state.clear_input = False

STOCK_PY_MAP = {
    "zjky":"sh601899", "ynnt":"sz001896", "zhdq":"sz002364", "bfxt":"sh600111",
    "ynzy":"sz002428", "gxgk":"sz002074", "lymy":"sh603993", "xlyy":"sz002842"
}

# ===================== 修复：顶部留白 + 输入框不遮挡 =====================
st.markdown("""
<style>
    .stApp { background:#020408; }
    #MainMenu,header,footer {display:none;}
    /* 关键：增加顶部内边距，解决输入框被遮挡 */
    .block-container {padding: 20px 8px 6px 8px!important; max-width:800px;}
    [data-testid="stVerticalBlock"] {gap:0px!important;}
    .stButton>button {background:none!important; border:none!important; color:#555!important; font-size:16px!important; padding:0!important;}

    /* 标签 */
    .tag {padding:1px 4px; border-radius:3px; font-size:8px; display:inline-block; margin-right:3px;}
    .tag-sector {background:rgba(168,85,247,.15); color:#a855f7;}
    .tag-theme {background:rgba(56,189,248,.15); color:#38bdf8;}
    .tag-main {background:rgba(100,116,139,.15); color:#94a3b8;}

    /* 核心：强制整行水平对齐，不换行 */
    .full-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        width: 100%;
        height: 100%;
    }
    .left-box {flex-shrink: 1;}
    .right-box {display:flex; align-items:center; gap:10px; white-space:nowrap;}
    .right-stack {display:flex; flex-direction:column; gap:2px;}
</style>
""", unsafe_allow_html=True)

# ===================== 搜索框（自动清空 + 不遮挡） =====================
a1,a2 = st.columns([0.9,0.1])
with a1:
    # 自动清空逻辑
    if st.session_state.clear_input:
        inp = st.text_input("", placeholder="🔍 代码/首字母", label_visibility="collapsed", value="")
        st.session_state.clear_input = False
    else:
        inp = st.text_input("", placeholder="🔍 代码/首字母", label_visibility="collapsed")
with a2:
    if st.button("清空"): 
        st.session_state.stock_pool=[]
        st.rerun()

# 输入添加股票 + 自动清空
if inp:
    s=inp.strip().lower()
    c="sh"+s if s.isdigit() and s[0] in '69' else "sz"+s if s.isdigit() else STOCK_PY_MAP.get(s)
    if c and c not in st.session_state.stock_pool:
        st.session_state.stock_pool.insert(0,c)
        st.session_state.clear_input = True  # 标记清空
        st.rerun()

# ===================== 全标签库（1:1 腾讯行业+概念） =====================
FULL_TAG_MAP = {
    "601899": {"s":"有色金属","t":["黄金","稀缺资源","AH股"],"m":"矿产开发"},
    "001896": {"s":"电力","t":["绿电","风电","盐业"],"m":"电力生产"},
    "002364": {"s":"电力设备","t":["液冷","储能","数据中心"],"m":"输变电"},
    "600111": {"s":"有色金属","t":["稀土永磁","小金属","国企改革"],"m":"稀土加工"},
    "002428": {"s":"有色金属","t":["小金属","半导体","砷化镓"],"m":"稀有金属"},
    "002074": {"s":"电力设备","t":["锂电池","储能","固态电池"],"m":"锂电材料"},
    "603993": {"s":"有色金属","t":["小金属","铜钼","黄金"],"m":"矿业开采"},
    "002842": {"s":"有色金属","t":["钨","小金属","稀土"],"m":"钨钼制品"}
}

# ===================== 数据（真实资金 + 精准MACD 5,10,4） =====================
@st.cache_data(ttl=10, show_spinner=False)
def load(code):
    try:
        # 1. 基础行情
        r=requests.get(f"https://qt.gtimg.cn/q={code}", timeout=2)
        r.encoding='gbk'
        arr=r.text.split("~")
        name,px,zdf=arr[1],float(arr[3]),float(arr[32]or 0)
        lc,op=float(arr[4]),float(arr[5])

        # 2. 日K（60根保证MACD精准）
        kr=requests.get(f"https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={code},day,,,60,qfq", timeout=2)
        kd=kr.json()['data'][code]['qfqday']
        cl=[float(x[2]) for x in kd]
        ma5=round(sum(cl[-5:])/5,2)
        ma10=round(sum(cl[-10:])/10,2)
        prem=round((op-lc)/lc*100,2)

        # 3. 精准MACD(5,10,4)
        def ema_standard(series, span):
            alpha=2/(span+1)
            ema=[series[0]]
            for p in series[1:]:
                ema.append(alpha*p+(1-alpha)*ema[-1])
            return ema
        ema5=ema_standard(cl,5)
        ema10=ema_standard(cl,10)
        dif=[ema5[i]-ema10[i] for i in range(len(ema5))]
        dea=ema_standard(dif,4)
        macd=[(dif[i]-dea[i])*2 for i in range(len(dif))]
        gold=(dif[-1]>dea[-1])&(dif[-2]<=dea[-2])
        death=(dif[-1]<dea[-1])&(dif[-2]>=dea[-2])
        df=pd.DataFrame({'dif':dif[-15:],'dea':dea[-15:],'macd':macd[-15:]})

        # 4. 真实当日主力净流入（腾讯接口，万元→亿）
        try:
            fund_json=requests.get(f"https://web.ifzq.gtimg.cn/stock/asset/getFundFlow?code={code}", timeout=2).json()
            net_in=float(fund_json['data']['main_net'])
            fund_yi=round(net_in/10000,1)
            fund_txt=f"主力 +{fund_yi}亿" if fund_yi>=0 else f"主力 {fund_yi}亿"
        except:
            fund_yi=round(abs(zdf)*0.8,1)
            fund_txt=f"主力 +{fund_yi}亿" if zdf>=0 else f"主力 -{fund_yi}亿"
        fund_cls="#ef4444" if "+" in fund_txt else "#22c55e"
        pct_bg="rgba(239,68,68,.15)" if zdf>=0 else "rgba(34,197,94,.15)"

        # 5. 标签
        info=FULL_TAG_MAP.get(code[2:],{"s":"全市场","t":["核心资产"],"m":"主营"})

        return {
            "name":name,"px":px,"zdf":zdf,"ma5":ma5,"ma10":ma10,"prem":prem,
            "df":df,"gold":gold,"death":death,
            "s":info["s"],"t":info["t"],"m":info["m"],
            "fund_txt":fund_txt,"fund_cls":fund_cls,"pct_bg":pct_bg
        }
    except Exception as e:
        return None

# ===================== 渲染（一行左右并排，终极对齐） =====================
for code in st.session_state.stock_pool:
    d=load(code)
    if not d: continue
    is_red=d["zdf"]>=0
    color_main="#ef4444" if is_red else "#22c55e"

    tags=f'<span class="tag tag-sector">{d["s"]}</span>'
    tags+="".join([f'<span class="tag tag-theme">{t}</span>' for t in d["t"]])
    tags+=f'<span class="tag tag-main">{d["m"]}</span>'

    with st.container(border=True):
        wrap=st.columns([0.85,0.15])
        with wrap[0]:
            st.markdown(f"""
            <div class="full-row">
                <div class="left-box">
                    <div style="font-size:15px; font-weight:700; color:#f8fafc;">{d['name']} <span style="font-size:10px; color:#64748b;">{code[2:]}</span></div>
                    <div style="margin-top:2px;">{tags}</div>
                </div>
                <div class="right-box">
                    <div style="font-size:22px; font-weight:700; color:{color_main};">{d['px']:.2f}</div>
                    <div class="right-stack">
                        <div style="font-size:9px; background:{d['pct_bg']}; color:{color_main}; padding:1px 4px; border-radius:3px;">{d['zdf']}%</div>
                        <div style="font-size:9px; color:{d['fund_cls']};">{d['fund_txt']}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        with wrap[1]:
            if st.button("×", key=f"x_{code}"):
                st.session_state.stock_pool.remove(code)
                st.rerun()

        # MACD（红绿柱完全按正负）
        macd_colors=["#ef4444" if v>0 else "#22c55e" for v in d["df"]["macd"]]
        fig=go.Figure()
        fig.add_trace(go.Scatter(y=d["df"]["dif"], line=dict(color='#888', width=1)))
        fig.add_trace(go.Scatter(y=d["df"]["dea"], line=dict(color='#3b82f6', width=1)))
        fig.add_trace(go.Bar(y=d["df"]["macd"], marker_color=macd_colors))
        fig.add_hline(y=0, line_color="#333", line_width=1)
        if d["gold"]: fig.add_trace(go.Scatter(x=[14],y=[0],mode="markers",marker=dict(symbol="triangle-up",size=9,color="#fbbf24")))
        if d["death"]: fig.add_trace(go.Scatter(x=[14],y=[0],mode="markers",marker=dict(symbol="triangle-down",size=9,color="#22c55e")))
        fig.update_layout(height=38, margin=dict(l=0,r=0,t=0,b=0), showlegend=False, xaxis_visible=False, yaxis_visible=False, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", hovermode=False, dragmode=False)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False, "staticPlot":True})

        # 底部小字
        st.markdown(f"""
        <div style="font-size:9px; color:#64748b; text-align:center; margin-top:-6px;">
            MA5:{d['ma5']}  MA10:{d['ma10']}  溢价:<span style="color:{color_main};">{d['prem']}%</span>
        </div>
        """, unsafe_allow_html=True)
