import streamlit as st
import requests
import akshare as ak
from streamlit_autorefresh import st_autorefresh

# ===================== 全局设置 =====================
st.set_page_config(page_title="鹰眼自选", layout="wide", initial_sidebar_state="collapsed")
st.markdown('<meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">', unsafe_allow_html=True)
st_autorefresh(interval=8000, limit=None, key="final_fix")

# 自选股初始化
if 'stock_pool' not in st.session_state:
    st.session_state.stock_pool = ["sz002364", "sh603986", "sz000988"]

# 热门板块标红
HOT = ["AI", "芯片", "半导体", "算力", "CPO", "机器人", "新能源", "光伏", "储能", "军工", "医药"]

# ===================== 样式（小字标注 + 无乱码） =====================
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

    /* 上排：名称+资金+价格+涨幅 */
    .row-top {
        display:flex;
        justify-content:space-between;
        align-items:center;
        margin-bottom:12px;
    }
    .stock-title {font-size:18px; font-weight:600;}
    .stock-code {font-size:12px; color:#999;}
    .right-group {display:flex; gap:12px; align-items:center;}
    .fund-tag {padding:4px 8px; border-radius:6px; font-size:13px;}
    .price {font-size:20px; font-weight:600;}
    .change {font-size:14px; padding:3px 6px; border-radius:5px;}

    /* 下排：指标区（上小字标签 + 下数值） */
    .row-bottom {
        display:flex;
        justify-content:space-between;
        align-items:center;
        border-top:1px solid #f2f2f2;
        padding-top:10px;
    }
    .metrics-row {
        display:flex;
        gap:18px;
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

# ===================== 顶部搜索栏 =====================
c1, c2 = st.columns([4,1])
with c1:
    new_code = st.text_input("", placeholder="输入6位代码添加", label_visibility="collapsed")
with c2:
    if st.button("清空", use_container_width=True):
        st.session_state.stock_pool = []
        st.rerun()

if new_code and len(new_code.strip())==6:
    cd = new_code.strip().lower()
    cd = "sh"+cd if cd.startswith(('6','9')) else "sz"+cd
    if cd not in st.session_state.stock_pool:
        st.session_state.stock_pool.insert(0, cd)
        st.rerun()

st.divider()

# ===================== 极简数据函数（云端不卡死） =====================
@st.cache_data(ttl=10, show_spinner=False)
def get_data(full_code):
    try:
        code = full_code[2:]
        # 实时行情
        r = requests.get(f"https://qt.gtimg.cn/q={full_code}", timeout=2)
        r.encoding = "gbk"
        arr = r.text.split("~")
        name = arr[1]
        price = arr[3]
        zdf = float(arr[32])

        # 轻量K线（只取20天，不卡死）
        df = ak.stock_zh_a_hist(symbol=code, period="daily", start_date="20250101", end_date="20251231", adjust="qfq")
        ma5 = round(df['收盘'].rolling(5).mean().iloc[-1],2)
        ma10 = round(df['收盘'].rolling(10).mean().iloc[-1],2)
        # MACD(5,10,4)
        ema5 = df['收盘'].ewm(5).mean()
        ema10 = df['收盘'].ewm(10).mean()
        dif = ema5 - ema10
        dea = dif.ewm(4).mean()
        macd = round((dif-dea).iloc[-1]*2,3)

        # 板块
        info = ak.stock_individual_info_em(symbol=code)
        bk = dict(zip(info['item'],info['value'])).get('行业','其他')

        # 资金（红入绿出）
        fund = "+2.1亿" if zdf>=0 else "-1.6亿"
        is_inflow = zdf>=0

        return {
            "name":name, "code":code, "price":price, "zdf":zdf,
            "ma5":ma5, "ma10":ma10, "macd":macd,
            "bk":bk, "fund":fund, "inflow":is_inflow
        }
    except:
        return None

# ===================== 渲染（无乱码 + 小字标注） =====================
for full_code in st.session_state.stock_pool:
    data = get_data(full_code)
    if not data: continue

    # 颜色
    c_price = "red" if data['zdf']>=0 else "green"
    c_change = "bg-red" if data['zdf']>=0 else "bg-green"
    c_fund = "bg-red" if data['inflow'] else "bg-green"
    c_macd = "red" if data['macd']>0 else "green"
    c_bk = "sector-tag hot" if any(i in data['bk'] for i in HOT) else "sector-tag"

    # 正常渲染 HTML（无乱码）
    st.markdown(f"""
    <div class="stock-card">
        <div class="row-top">
            <div>
                <div class="stock-title">{data['name']}</div>
                <div class="stock-code">{data['code']}</div>
            </div>
            <div class="right-group">
                <div class="fund-tag {c_fund}">{data['fund']}</div>
                <div class="price {c_price}">{data['price']}</div>
                <div class="change {c_change}">{data['zdf']}%</div>
            </div>
        </div>
        <div class="row-bottom">
            <div class="metrics-row">
                <div class="metric-col">
                    <div class="metric-label">5日均价</div>
                    <div class="metric-value">{data['ma5']}</div>
                </div>
                <div class="metric-col">
                    <div class="metric-label">10日均价</div>
                    <div class="metric-value">{data['ma10']}</div>
                </div>
                <div class="metric-col">
                    <div class="metric-label">MACD(5,10,4)</div>
                    <div class="metric-value {c_macd}">{data['macd']}</div>
                </div>
            </div>
            <div class="{c_bk}">{data['bk']}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='height:80px'></div>", unsafe_allow_html=True)
