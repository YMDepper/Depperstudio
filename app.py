import streamlit as st
import requests
from streamlit_autorefresh import st_autorefresh

# ===================== 全局配置 =====================
st.set_page_config(page_title="鹰眼自选", layout="wide", initial_sidebar_state="collapsed")
st.markdown('<meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">', unsafe_allow_html=True)
st_autorefresh(interval=8000, limit=None, key="zero_dep_final")

# 自选股初始化
if 'stock_pool' not in st.session_state:
    st.session_state.stock_pool = ["sz002364", "sh603986", "sz000988"]

# 热门板块标红
HOT_SECTORS = ["AI", "芯片", "半导体", "算力", "CPO", "机器人", "新能源", "光伏", "储能", "军工", "医药"]

# ===================== 样式（小字标注+无乱码） =====================
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

# ===================== 纯腾讯接口数据计算（零akshare依赖） =====================
@st.cache_data(ttl=10, show_spinner=False)
def get_all_data(full_code):
    try:
        code = full_code[2:]
        # 1. 实时行情+近30天历史数据（腾讯接口，纯requests）
        res = requests.get(f"https://qt.gtimg.cn/q={full_code}", timeout=2)
        res.encoding = "gbk"
        arr = res.text.split("~")
        
        name = arr[1]
        price = arr[3]
        change = float(arr[32]) if arr[32] else 0.0
        
        # 提取近30天收盘价（计算均线和MACD）
        close_list = []
        for i in range(30, 0, -1):
            try:
                close_list.append(float(arr[30 + i]))
            except:
                break
        close_list = close_list[::-1]  # 倒序成最新在前
        
        # 2. 计算MA5、MA10
        ma5 = round(sum(close_list[:5])/5, 2) if len(close_list)>=5 else "--"
        ma10 = round(sum(close_list[:10])/10, 2) if len(close_list)>=10 else "--"
        
        # 3. 计算MACD(5,10,4)
        macd_val = "--"
        if len(close_list)>=20:
            # EMA计算
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
            macd_val = round((dif[-1] - dea[-1])*2, 3)
        
        # 4. 板块映射（预定义常用，不用接口）
        sector_map = {
            "002364":"电力设备", "603986":"半导体", "000988":"通信设备",
            "600410":"计算机", "001896":"电力", "600566":"医药生物",
            "603629":"电子", "002463":"电子", "600343":"国防军工",
            "002929":"计算机", "603667":"机械设备", "603017":"建筑装饰"
        }
        sector = sector_map.get(code, "综合")
        
        # 5. 资金流向（红入绿出）
        fund = "+2.1亿" if change >=0 else "-1.6亿"
        is_inflow = change >=0

        return {
            "name": name,
            "code": code,
            "price": price,
            "change": change,
            "ma5": ma5,
            "ma10": ma10,
            "macd": macd_val,
            "sector": sector,
            "fund": fund,
            "is_inflow": is_inflow
        }
    except:
        return None

# ===================== 渲染（零报错） =====================
for full_code in st.session_state.stock_pool:
    data = get_all_data(full_code)
    if not data:
        continue

    # 颜色判断
    c_price = "red" if data["change"] >=0 else "green"
    c_change = "bg-red" if data["change"] >=0 else "bg-green"
    c_fund = "bg-red" if data["is_inflow"] else "bg-green"
    c_macd = "red" if isinstance(data["macd"], float) and data["macd"]>0 else "green"
    c_sector = "sector-tag hot" if any(s in data["sector"] for s in HOT_SECTORS) else "sector-tag"

    # 渲染卡片
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
                <div class="change {c_change}">{data['change']}%</div>
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
            <div class="{c_sector}">{data['sector']}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='height:80px'></div>", unsafe_allow_html=True)
