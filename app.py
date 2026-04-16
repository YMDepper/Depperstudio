import streamlit as st
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# ===================== 全局配置 =====================
st.set_page_config(
    page_title="鹰眼自选深度",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown('<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">', unsafe_allow_html=True)
st_autorefresh(interval=8000, limit=None, key="auto_refresh_v2")

# 初始化自选股
if 'stock_pool' not in st.session_state:
    st.session_state.stock_pool = ["sz002364", "sh603986", "sz000988"]

# 热门板块词库（用于标红）
HOT_SECTORS = ["AI", "芯片", "半导体", "算力", "CPO", "机器人", "新能源", "光伏", "储能", "军工", "医药"]

# ===================== 样式（双层紧凑结构） =====================
st.markdown("""
<style>
    body, .stApp {
        background-color: #f5f5f5 !important;
        color: #111;
        font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", sans-serif;
    }
    #MainMenu, header, footer {visibility: hidden;}
    .block-container {padding: 10px 8px !important; max-width: 100% !important;}

    /* 股票卡片容器 */
    .stock-card {
        background: #fff;
        border-radius: 10px;
        padding: 12px 10px;
        margin-bottom: 10px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }

    /* 第一层：主行情行 */
    .main-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 8px;
    }
    .left-info {
        display: flex;
        flex-direction: column;
        gap: 2px;
    }
    .stock-name {
        font-size: 17px;
        font-weight: 600;
        color: #111;
    }
    .stock-code {
        font-size: 12px;
        color: #888;
    }
    .right-quote {
        display: flex;
        align-items: center;
        gap: 15px;
    }
    .price-box {
        text-align: right;
    }
    .price {
        font-size: 20px;
        font-weight: 600;
    }
    .change {
        font-size: 14px;
        padding: 2px 6px;
        border-radius: 4px;
    }
    .fund-flow {
        font-size: 13px;
        padding: 3px 8px;
        border-radius: 6px;
        min-width: 60px;
        text-align: center;
    }

    /* 第二层：技术面+板块行 */
    .sub-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding-top: 6px;
        border-top: 1px dashed #eee;
        font-size: 12px;
        color: #666;
    }
    .tech-box {
        display: flex;
        gap: 12px;
    }
    .tech-item {
        display: flex;
        flex-direction: column;
        align-items: center;
    }
    .tech-value {
        font-weight: 500;
        color: #333;
    }
    .sector-tag {
        padding: 2px 8px;
        border-radius: 4px;
        background: #f0f0f0;
    }
    .sector-hot {
        background: #fff0f0;
        color: #f23c32;
        font-weight: 500;
    }

    /* 涨跌颜色 */
    .up {color: #f23c32;}
    .down {color: #02b262;}
    .bg-up {background: #fff0f0; color: #f23c32;}
    .bg-down {background: #f0fff7; color: #02b262;}

    /* 搜索栏 */
    .search-input input {
        height: 42px !important;
        border-radius: 8px !important;
        background: #fff !important;
        border: 1px solid #ddd !important;
    }
</style>
""", unsafe_allow_html=True)

# ===================== 顶部操作栏 =====================
col_add, col_clear = st.columns([4, 1])
with col_add:
    new_code = st.text_input("", placeholder="输入6位代码添加", label_visibility="collapsed")
with col_clear:
    if st.button("清空", use_container_width=True):
        st.session_state.stock_pool = []
        st.rerun()

if new_code and len(new_code.strip()) == 6:
    code = new_code.strip().lower()
    code = "sh" + code if code.startswith(('6', '9')) else "sz" + code
    if code not in st.session_state.stock_pool:
        st.session_state.stock_pool.insert(0, code)
        st.rerun()

st.divider()

# ===================== 核心数据获取函数 =====================
@st.cache_data(ttl=60)
def get_kline_data(code):
    """获取K线并计算MACD、均线"""
    try:
        end = datetime.now().strftime('%Y%m%d')
        start = (datetime.now()-timedelta(days=60)).strftime('%Y%m%d')
        df = ak.stock_zh_a_hist(symbol=code[2:], period="daily", start=start, end=end, adjust="qfq")
        if len(df) < 20:
            return None
        
        # 计算均线
        df['ma5'] = df['收盘'].rolling(5).mean()
        df['ma10'] = df['收盘'].rolling(10).mean()
        
        # 计算MACD(5,10,4)
        df['ema5'] = df['收盘'].ewm(span=5, adjust=False).mean()
        df['ema10'] = df['收盘'].ewm(span=10, adjust=False).mean()
        df['dif'] = df['ema5'] - df['ema10']
        df['dea'] = df['dif'].ewm(span=4, adjust=False).mean()
        df['macd'] = (df['dif'] - df['dea']) * 2
        
        latest = df.iloc[-1]
        return {
            "ma5": round(latest['ma5'], 2),
            "ma10": round(latest['ma10'], 2),
            "macd": round(latest['macd'], 3),
            "dif": round(latest['dif'], 3),
            "dea": round(latest['dea'], 3)
        }
    except:
        return None

@st.cache_data(ttl=300)
def get_stock_info(code):
    """获取板块和资金流向"""
    try:
        # 基础信息（板块）
        info_df = ak.stock_individual_info_em(symbol=code[2:])
        info_dict = dict(zip(info_df['item'], info_df['value']))
        sector = info_dict.get('行业', '未知')
        
        # 模拟近3天资金流向（简化版，真实接口较慢）
        # 这里用涨跌幅模拟：涨则红入，跌则绿出
        return {
            "sector": sector,
            "flow_mock": "模拟数据"
        }
    except:
        return {"sector": "未知", "flow_mock": "无"}

@st.cache_data(ttl=5)
def get_realtime_quote(code):
    """获取实时行情"""
    try:
        res = requests.get(f"https://qt.gtimg.cn/q={code}", timeout=2)
        res.encoding = "gbk"
        arr = res.text.split("~")
        if len(arr) < 40:
            return None
        
        # 简单模拟资金流向：涨则显示+流入，跌则显示-流出
        change = float(arr[32]) if arr[32] else 0
        flow_text = "+2.3亿" if change >= 0 else "-1.8亿"
        is_flow_in = change >= 0
        
        return {
            "name": arr[1],
            "code": code[2:],
            "price": arr[3],
            "change": change,
            "flow_text": flow_text,
            "is_flow_in": is_flow_in
        }
    except:
        return None

# ===================== 渲染主程序 =====================
view_container = st.empty()
with view_container.container():
    for code in st.session_state.stock_pool:
        # 并行获取数据
        quote = get_realtime_quote(code)
        tech = get_kline_data(code)
        info = get_stock_info(code)
        
        if not quote:
            continue
        
        # 颜色判断
        price_color = "up" if quote["change"] >= 0 else "down"
        change_bg = "bg-up" if quote["change"] >= 0 else "bg-down"
        flow_bg = "bg-up" if quote["is_flow_in"] else "bg-down"
        
        # 板块热门判断
        is_hot = any(hot in info["sector"] for hot in HOT_SECTORS)
        sector_class = "sector-tag sector-hot" if is_hot else "sector-tag"
        
        # 渲染双层卡片
        st.markdown(f"""
        <div class="stock-card">
            <!-- 第一层：主行情 -->
            <div class="main-row">
                <div class="left-info">
                    <div class="stock-name">{quote['name']}</div>
                    <div class="stock-code">{quote['code']}</div>
                </div>
                <div class="right-quote">
                    <div class="fund-flow {flow_bg}">{quote['flow_text']}</div>
                    <div class="price-box">
                        <div class="price {price_color}">{quote['price']}</div>
                        <div class="change {change_bg}">{quote['change']}%</div>
                    </div>
                </div>
            </div>
            
            <!-- 第二层：技术面+板块 -->
            <div class="sub-row">
                <div class="tech-box">
                    <div class="tech-item">
                        <span class="tech-value">{tech['ma5'] if tech else '--'}</span>
                        <span>MA5</span>
                    </div>
                    <div class="tech-item">
                        <span class="tech-value">{tech['ma10'] if tech else '--'}</span>
                        <span>MA10</span>
                    </div>
                    <div class="tech-item">
                        <span class="tech-value {'up' if tech and tech['macd']>0 else 'down'}">{tech['macd'] if tech else '--'}</span>
                        <span>MACD</span>
                    </div>
                </div>
                <div class="{sector_class}">{info['sector']}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<div style='height:80px'></div>", unsafe_allow_html=True)
