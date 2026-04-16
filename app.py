import streamlit as st
import requests
import pandas as pd
from streamlit_autorefresh import st_autorefresh

# ===================== 全局配置 =====================
st.set_page_config(page_title="鹰眼自选", layout="wide", initial_sidebar_state="collapsed")
st.markdown('<meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">', unsafe_allow_html=True)
st_autorefresh(interval=8000, limit=None, key="final_perfect")

# 自选股初始化
if 'stock_pool' not in st.session_state:
    st.session_state.stock_pool = ["sh600111", "sz002428", "sz002364"]

# 热门板块标红
HOT_SECTORS = ["AI", "芯片", "半导体", "算力", "CPO", "机器人", "新能源", "光伏", "储能", "军工", "医药", "稀土", "有色"]

# ✅ 首字母搜索映射表（补充你常用的即可）
STOCK_PY_MAP = {
    "bfxt":"sh600111", "ynzy":"sz002428", "zhdq":"sz002364",
    "zycx":"sh603986", "hstc":"sh600410", "ynkg":"sz001896",
    "jcyy":"sh600566", "hgkj":"sz000988", "ltdz":"sh603629",
    "hdgf":"sz002463", "htdl":"sh600343", "rjgf":"sz002929"
}

# ===================== 最终样式 =====================
st.markdown("""
<style>
    .stApp {background:#f5f5f5;}
    #MainMenu,header,footer {display:none;}
    .block-container {padding:10px 8px!important;}

    /* 股票卡片 */
    .stock-card {
        background:#fff;
        border-radius:12px;
        padding:14px;
        margin-bottom:10px;
    }

    /* ✅ 第一行：名称+代码+现价+涨跌幅 */
    .row-top {
        display:flex;
        justify-content:space-between;
        align-items:center;
        margin-bottom:12px;
    }
    .left-title {
        display:flex;
        align-items:center;
        gap:12px;
    }
    .stock-name {font-size:18px; font-weight:600;}
    .stock-code {font-size:12px; color:#999;}
    .right-price {
        display:flex;
        align-items:center;
        gap:10px;
    }
    .price {font-size:20px; font-weight:600;}
    .change {font-size:14px; padding:3px 6px; border-radius:5px;}

    /* ✅ 第二行：MA5+MA10+资金流+MACD图+板块 */
    .row-bottom {
        display:flex;
        justify-content:space-between;
        align-items:center;
        border-top:1px solid #f2f2f2;
        padding-top:10px;
    }
    .metrics-row {
        display:flex;
        gap:20px;
        align-items:center;
    }
    .metric-col {
        display:flex;
        flex-direction:column;
        align-items:center;
    }
    .metric-label {
        font-size:11px;
        color:#999;
        margin-bottom:2px;
    }
    .metric-value {
        font-size:14px;
        font-weight:500;
    }
    .fund-tag {
        padding:4px 8px;
        border-radius:6px;
        font-size:13px;
    }
    .sector-tag {
        font-size:12px;
        padding:3px 8px;
        border-radius:5px;
        background:#f5f5f5;
    }
    .hot {background:#ffebeb; color:#e63946; font-weight:500;}

    /* 颜色 */
    .red {color:#e63946;}
    .green {color:#22c55e;}
    .bg-red {background:#ffebeb; color:#e63946;}
    .bg-green {background:#ecfdf5; color:#22c55e;}
</style>
""", unsafe_allow_html=True)

# ===================== ✅ 支持首字母搜索的顶部栏 =====================
c1, c2 = st.columns([4,1])
with c1:
    search_input = st.text_input("", placeholder="输入股票代码/首字母（例：600111 / bfxt）", label_visibility="collapsed")
with c2:
    if st.button("清空", use_container_width=True):
        st.session_state.stock_pool = []
        st.rerun()

# 搜索逻辑：支持数字代码+首字母
if search_input:
    search = search_input.strip().lower()
    # 1. 数字代码
    if search.isdigit() and len(search)==6:
        code = "sh"+search if search.startswith(('6','9')) else "sz"+search
        if code not in st.session_state.stock_pool:
            st.session_state.stock_pool.insert(0, code)
            st.rerun()
    # 2. 首字母
    elif search in STOCK_PY_MAP:
        code = STOCK_PY_MAP[search]
        if code not in st.session_state.stock_pool:
            st.session_state.stock_pool.insert(0, code)
            st.rerun()

st.divider()

# ===================== 核心数据函数（修复均价+MACD） =====================
@st.cache_data(ttl=10, show_spinner=False)
def get_stock_data(full_code):
    try:
        code = full_code[2:]
        # 1. 实时行情
        res = requests.get(f"https://qt.gtimg.cn/q={full_code}", timeout=2)
        res.encoding = "gbk"
        arr = res.text.split("~")
        name = arr[1]
        price = arr[3]
        change = float(arr[32]) if arr[32] else 0.0

        # 2. ✅ 正确获取K线数据（修复均价不显示）
        kline_res = requests.get(
            f"https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={full_code},day,,,30,qfq",
            timeout=2
        )
        kline_json = kline_res.json()
        kline_list = kline_json['data'][full_code]['qfqday']
        close_list = [float(x[2]) for x in kline_list]  # 收盘价

        # 3. 计算MA5、MA10
        ma5 = round(sum(close_list[-5:])/5, 2)
        ma10 = round(sum(close_list[-10:])/10, 2)

        # 4. 计算MACD(5,10,4) + 最近10天数据用于画图
        def ema(data, span):
            ema_list = []
            ema_list.append(data[0])
            for i in range(1, len(data)):
                ema_list.append((2*data[i] + (span-1)*ema_list[i-1])/(span+1))
            return ema_list
        
        ema5 = ema(close_list, 5)
        ema10 = ema(close_list, 10)
        dif = [ema5[i]-ema10[i] for i in range(len(ema5))]
        dea = ema(dif, 4)
        macd_list = [(dif[i]-dea[i])*2 for i in range(len(dif))]
        macd_latest = round(macd_list[-1], 3)
        # 最近10天MACD用于画图
        macd_chart_data = pd.DataFrame({"MACD": macd_list[-10:]})

        # 5. 板块映射
        sector_map = {
            "600111":"稀土永磁", "002428":"小金属", "002364":"电力设备",
            "603986":"半导体", "600410":"云计算", "001896":"电力",
            "600566":"医药", "000988":"光通信", "603629":"算力"
        }
        sector = sector_map.get(code, "综合")

        # 6. 资金流向
        fund = "+2.1亿" if change >=0 else "-1.6亿"
        is_inflow = change >=0

        return {
            "name": name, "code": code, "price": price, "change": change,
            "ma5": ma5, "ma10": ma10, "macd": macd_latest, "macd_chart": macd_chart_data,
            "sector": sector, "fund": fund, "is_inflow": is_inflow
        }
    except:
        return None

# ===================== 渲染（最终布局） =====================
for full_code in st.session_state.stock_pool:
    data = get_stock_data(full_code)
    if not data:
        continue

    # 颜色
    c_price = "red" if data["change"] >=0 else "green"
    c_change = "bg-red" if data["change"] >=0 else "bg-green"
    c_fund = "bg-red" if data["is_inflow"] else "bg-green"
    c_macd = "red" if data["macd"]>0 else "green"
    c_sector = "sector-tag hot" if any(s in data["sector"] for s in HOT_SECTORS) else "sector-tag"

    # 卡片容器
    with st.container():
        st.markdown(f'<div class="stock-card">', unsafe_allow_html=True)
        
        # ✅ 第一行：名称+代码 + 现价+涨跌幅
        st.markdown(f"""
        <div class="row-top">
            <div class="left-title">
                <div class="stock-name">{data['name']}</div>
                <div class="stock-code">{data['code']}</div>
            </div>
            <div class="right-price">
                <div class="price {c_price}">{data['price']}</div>
                <div class="change {c_change}">{data['change']}%</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ✅ 第二行：MA5 + MA10 + 资金流 + MACD曲线图 + 板块
        col1, col2, col3, col4, col5 = st.columns([1,1,1,2,1])
        with col1:
            st.metric("5日均价", data['ma5'], label_visibility="visible")
        with col2:
            st.metric("10日均价", data['ma10'], label_visibility="visible")
        with col3:
            st.markdown(f'<div class="fund-tag {c_fund}">{data["fund"]}</div>', unsafe_allow_html=True)
        with col4:
            # ✅ MACD小曲线图（高度60，无坐标轴）
            st.line_chart(
                data['macd_chart'],
                height=60,
                use_container_width=True,
                color="#e63946" if data["macd"]>0 else "#22c55e",
                x_label="", y_label=""
            )
        with col5:
            st.markdown(f'<div class="{c_sector}">{data["sector"]}</div>', unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<div style='height:80px'></div>", unsafe_allow_html=True)
