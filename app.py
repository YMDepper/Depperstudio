import streamlit as st
import requests
from streamlit_autorefresh import st_autorefresh

# ===================== 全局配置（同花顺风格） =====================
st.set_page_config(
    page_title="鹰眼自选行情",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown('<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">', unsafe_allow_html=True)

# 自动刷新 5秒（无闪烁）
st_autorefresh(interval=5000, limit=None, key="auto_refresh_final")

# 初始化自选股
if 'stock_pool' not in st.session_state:
    st.session_state.stock_pool = [
        "sz002364", "sh603986", "sh600410", "sz001896",
        "sh600566", "sz000988", "sh603629", "sz002463"
    ]

# ===================== 同花顺极简样式（1:1复刻） =====================
st.markdown("""
<style>
    body, .stApp {
        background-color: #ffffff !important;
        color: #111111;
        font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", sans-serif;
    }
    #MainMenu, header, footer {visibility: hidden;}
    .block-container {padding: 12px 10px !important; max-width: 100% !important;}

    /* 整行容器：和同花顺一样的单行布局 */
    .stock-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        height: 56px;
        padding: 0 10px;
        border-bottom: 1px solid #f2f2f2;
    }

    /* 左侧：竖线 + 名称 + 代码 */
    .row-left {
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .line-tag {
        width: 3px;
        height: 24px;
        border-radius: 2px;
        background-color: #ff4444;
    }
    .name-area {
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    .stock-name {
        font-size: 17px;
        font-weight: 500;
        color: #111;
    }
    .stock-code {
        font-size: 13px;
        color: #888;
    }

    /* 中间：现价 */
    .row-price {
        font-size: 18px;
        font-weight: 500;
        text-align: center;
    }

    /* 右侧：涨幅 */
    .row-change {
        font-size: 17px;
        font-weight: 500;
        min-width: 70px;
        text-align: right;
        border-radius: 4px;
        padding: 3px 6px;
    }

    /* 涨跌颜色 */
    .up {color: #f23c32;}
    .down {color: #02b262;}

    /* 搜索栏 */
    .search-input input {
        height: 40px !important;
        border-radius: 8px !important;
        background: #f5f5f5 !important;
        border: none !important;
    }
</style>
""", unsafe_allow_html=True)

# ===================== 顶部搜索添加（同花顺风格） =====================
col_add, col_btn = st.columns([4, 1])
with col_add:
    new_code = st.text_input("", placeholder="输入股票代码添加", label_visibility="collapsed")
with col_btn:
    if st.button("清空", use_container_width=True):
        st.session_state.stock_pool = []
        st.rerun()

# 添加逻辑
if new_code and len(new_code.strip()) == 6:
    code = new_code.strip().lower()
    code = "sh" + code if code.startswith(('6', '9')) else "sz" + code
    if code not in st.session_state.stock_pool:
        st.session_state.stock_pool.append(code)
        st.rerun()

st.divider()

# ===================== 数据接口 =====================
@st.cache_data(ttl=3)
def get_price(code):
    try:
        res = requests.get(f"https://qt.gtimg.cn/q={code}", timeout=2)
        res.encoding = "gbk"
        arr = res.text.split("~")
        if len(arr) < 40:
            return None
        return {
            "name": arr[1],
            "code": code[2:],
            "price": arr[3],
            "change": float(arr[32])
        }
    except:
        return None

# ===================== 渲染：同花顺列表布局（核心） =====================
view = st.container()
with view:
    for code in st.session_state.stock_pool:
        data = get_price(code)
        if not data:
            continue

        # 颜色
        color = "up" if data["change"] >= 0 else "down"

        # 单行布局 = 左(竖线+名称+代码) + 中(价格) + 右(涨幅)
        st.markdown(f"""
        <div class="stock-row">
            <div class="row-left">
                <div class="line-tag"></div>
                <div class="name-area">
                    <div class="stock-name">{data['name']}</div>
                    <div class="stock-code">{data['code']}</div>
                </div>
            </div>
            <div class="row-price {color}">{data['price']}</div>
            <div class="row-change {color}">{data['change']}%</div>
        </div>
        """, unsafe_allow_html=True)

# 底部留白
st.markdown("<div style='height:60px'></div>", unsafe_allow_html=True)
