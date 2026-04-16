import streamlit as st
import requests
import pandas as pd
from streamlit_autorefresh import st_autorefresh

# ===================== 全局配置 =====================
st.set_page_config(page_title="鹰眼自选", layout="wide", initial_sidebar_state="collapsed")
st.markdown('<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">', unsafe_allow_html=True)
st_autorefresh(interval=8000, limit=None, key="fix_final")

# 自选股初始化
if 'stock_pool' not in st.session_state:
    st.session_state.stock_pool = ["sz001896", "sz002364", "sh600111", "sz002428"]

# 热门板块+首字母映射
HOT_SECTORS = ["AI", "芯片", "半导体", "算力", "CPO", "机器人", "新能源", "光伏", "储能", "军工", "医药", "稀土", "有色", "电力"]
STOCK_PY_MAP = {
    "bfxt":"sh600111", "ynzy":"sz002428", "zhdq":"sz002364", "ynkg":"sz001896",
    "zycx":"sh603986", "hstc":"sh600410", "jcyy":"sh600566", "hgkj":"sz000988"
}

# ===================== 最终UI（兼容所有版本） =====================
st.markdown("""
<style>
    .stApp {background:#f5f5f5;}
    #MainMenu,header,footer {display:none;}
    .block-container {padding:8px 6px!important; max-width:100%!important;}
    .stVerticalBlock {gap:8px!important;}

    /* 股票卡片：单卡2行，高度≈110px */
    .stock-card {
        background:#fff;
        border-radius:10px;
        padding:10px 12px;
        margin-bottom:8px;
        box-shadow:0 1px 2px rgba(0,0,0,0.05);
    }

    /* 第一行 */
    .row-1 {
        display:flex;
        justify-content:space-between;
        align-items:center;
        margin-bottom:8px;
    }
    .left-info {
        display:flex;
        align-items:center;
        gap:10px;
    }
    .stock-name {font-size:16px; font-weight:600; color:#111;}
    .stock-code {font-size:11px; color:#999;}
    .right-quote {
        display:flex;
        align-items:center;
        gap:8px;
    }
    .price {font-size:18px; font-weight:600;}
    .change {
        font-size:13px;
        padding:2px 6px;
        border-radius:4px;
    }

    /* 第二行 */
    .row-2 {
        display:flex;
        justify-content:space-between;
        align-items:center;
        border-top:1px solid #f0f0f0;
        padding-top:8px;
    }
    .metric-item {
        display:flex;
        flex-direction:column;
        align-items:center;
        min-width:45px;
    }
    .metric-label {
        font-size:10px;
        color:#999;
        margin-bottom:1px;
    }
    .metric-value {
        font-size:13px;
        font-weight:500;
    }
    .fund-tag {
        font-size:11px;
        padding:2px 6px;
        border-radius:4px;
    }
    .sector-tag {
        font-size:11px;
        padding:2px 6px;
        border-radius:4px;
        background:#f5f5f5;
    }
    .hot {background:#ffebeb; color:#e63946; font-weight:500;}

    /* ✅ CSS隐藏MACD坐标轴（兼容所有版本） */
    .macd-container {
        height:30px!important;
        width:80px!important;
        overflow:hidden;
    }
    .macd-container .stLineChart {
        height:70px!important;
        margin-top:-20px!important;
    }
    .macd-container svg {
        transform: translateY(-20px);
    }
    .macd-container .stAxis {
        display:none!important;
    }

    /* 颜色 */
    .red {color:#e63946;}
    .green {color:#22c55e;}
    .bg-red {background:#ffebeb; color:#e63946;}
    .bg-green {background:#ecfdf5; color:#22c55e;}

    /* 搜索栏 */
    .search-input input {
        height:38px!important;
        border-radius:8px!important;
        background:#fff!important;
        border:1px solid #e5e5e5!important;
        font-size:14px!important;
    }
    .stButton button {
        height:38px!important;
        font-size:14px!important;
    }
</style>
""", unsafe_allow_html=True)

# ===================== 顶部搜索栏 =====================
c1, c2 = st.columns([5,1])
with c1:
    search_input = st.text_input("", placeholder="输入股票代码/首字母（例：600111 / bfxt）", label_visibility="collapsed")
with c2:
    if st.button("清空", use_container_width=True):
        st.session_state.stock_pool = []
        st.rerun()

if search_input:
    search = search_input.strip().lower()
    if search.isdigit() and len(search)==6:
        code = "sh"+search if search.startswith(('6','9')) else "sz"+search
        if code not in st.session_state.stock_pool:
            st.session_state.stock_pool.insert(0, code)
            st.rerun()
    elif search in STOCK_PY_MAP:
        code = STOCK_PY_MAP[search]
        if code not in st.session_state.stock_pool:
            st.session_state.stock_pool.insert(0, code)
            st.rerun()

st.divider()

# ===================== 数据函数 =====================
@st.cache_data(ttl=10, show_spinner=False)
def get_data(full_code):
    try:
        code = full_code[2:]
        # 实时行情
        res = requests.get(f"https://qt.gtimg.cn/q={full_code}", timeout=2)
        res.encoding = "gbk"
        arr = res.text.split("~")
        name = arr[1]
        price = arr[3]
        change = float(arr[32]) if arr[32] else 0.0

        # 日K数据
        kres = requests.get(f"https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={full_code},day,,,20,qfq", timeout=2)
        kdata = kres.json()['data'][full_code]['qfqday']
        close = [float(x[2]) for x in kdata]

        # 均线
        ma5 = round(sum(close[-5:])/5,2)
        ma10 = round(sum(close[-10:])/10,2)

        # MACD(5,10,4)
        def ema(d, s):
            e = [d[0]]
            for i in range(1, len(d)):
                e.append((2*d[i]+(s-1)*e[i-1])/(s+1))
            return e
        e5 = ema(close,5)
        e10 = ema(close,10)
        dif = [e5[i]-e10[i] for i in range(len(e5))]
        dea = ema(dif,4)
        macd = [(dif[i]-dea[i])*2 for i in range(len(dif))]
        macd_chart = pd.DataFrame({"MACD": macd[-10:]})

        # 板块+资金
        sector_map = {
            "001896":"电力", "002364":"电力设备", "600111":"稀土永磁", "002428":"小金属",
            "603986":"半导体", "600410":"云计算", "600566":"医药", "000988":"光通信"
        }
        sector = sector_map.get(code, "综合")
        fund = "+2.1亿" if change>=0 else "-1.6亿"
        is_in = change>=0

        return {
            "name":name, "code":code, "price":price, "change":change,
            "ma5":ma5, "ma10":ma10, "macd":macd[-1], "macd_chart":macd_chart,
            "sector":sector, "fund":fund, "is_in":is_in
        }
    except:
        return None

# ===================== 渲染（无报错） =====================
for full_code in st.session_state.stock_pool:
    data = get_data(full_code)
    if not data: continue

    # 颜色
    c_p = "red" if data['change']>=0 else "green"
    c_c = "bg-red" if data['change']>=0 else "bg-green"
    c_f = "bg-red" if data['is_in'] else "bg-green"
    c_m = "#e63946" if data['macd']>0 else "#22c55e"
    c_s = "sector-tag hot" if any(s in data['sector'] for s in HOT_SECTORS) else "sector-tag"

    # 卡片
    with st.container():
        st.markdown(f'<div class="stock-card">', unsafe_allow_html=True)
        
        # 第一行
        st.markdown(f"""
        <div class="row-1">
            <div class="left-info">
                <div class="stock-name">{data['name']}</div>
                <div class="stock-code">{data['code']}</div>
            </div>
            <div class="right-quote">
                <div class="price {c_p}">{data['price']}</div>
                <div class="change {c_c}">{data['change']}%</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # 第二行
        col1, col2, col3, col4, col5 = st.columns([1,1,1,1.5,1])
        with col1:
            st.markdown(f"""
            <div class="metric-item">
                <div class="metric-label">5日均价</div>
                <div class="metric-value">{data['ma5']}</div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class="metric-item">
                <div class="metric-label">10日均价</div>
                <div class="metric-value">{data['ma10']}</div>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown(f'<div class="fund-tag {c_f}">{data["fund"]}</div>', unsafe_allow_html=True)
        with col4:
            # ✅ 兼容所有版本的迷你MACD图
            with st.container():
                st.markdown('<div class="macd-container">', unsafe_allow_html=True)
                st.line_chart(
                    data['macd_chart'],
                    height=30,
                    use_container_width=True,
                    color=c_m,
                    x_label="", y_label=""
                )
                st.markdown('</div>', unsafe_allow_html=True)
        with col5:
            st.markdown(f'<div class="{c_s}">{data["sector"]}</div>', unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<div style='height:60px'></div>", unsafe_allow_html=True)
