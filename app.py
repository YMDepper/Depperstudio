import streamlit as st
import requests

# ===================== 1. 全局配置 =====================
st.set_page_config(
    page_title="鹰眼股票诊断",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items=None
)

# 强制移动端适配
st.markdown('<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">', unsafe_allow_html=True)

# 初始化股票池
if 'stock_pool' not in st.session_state:
    st.session_state.stock_pool = ["sh600111", "sz002428", "sh600137"]

# ===================== 2. iPhone专属UI样式 =====================
st.markdown("""
<style>
    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
        -webkit-font-smoothing: antialiased;
        -webkit-text-size-adjust: 100%;
        font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Helvetica Neue", sans-serif;
    }

    .stApp {
        background-color: #0a0a0a;
        color: #ffffff;
        padding: 12px 16px !important;
        max-width: 100vw !important;
        overflow-x: hidden !important;
    }

    #MainMenu, header, footer {visibility: hidden;}
    .block-container {padding: 0 !important; max-width: 100% !important;}
    .stVerticalBlock {gap: 0 !important;}

    .stButton button {
        width: 44px !important;
        height: 44px !important;
        background-color: #2c2c2e !important;
        border-radius: 10px !important;
        border: none !important;
        color: #ffffff !important;
        font-size: 22px !important;
        font-weight: 600 !important;
        padding: 0 !important;
        margin: 0 !important;
        position: absolute !important;
        top: 16px !important;
        right: 16px !important;
        z-index: 999 !important;
    }
    .stButton button:hover {background-color: #3a3a3c !important;}

    .stock-card {
        position: relative;
        width: 100% !important;
        border-radius: 20px;
        background-color: #17171a;
        padding: 20px 16px 16px 16px;
        margin-bottom: 16px !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
    }

    .signal-border {
        position: absolute;
        top: 0;
        left: 0;
        width: 6px;
        height: 100%;
        z-index: 1;
    }
    .signal-buy {background: linear-gradient(180deg, #ff3b30, #ff2d55);}
    .signal-sell {background: linear-gradient(180deg, #34c759, #30d158);}

    .card-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        width: 100%;
        margin-bottom: 12px;
        padding-right: 50px;
    }

    .header-left {
        display: flex;
        flex-direction: column;
        gap: 6px;
        max-width: 55%;
    }
    .name-row {
        display: flex;
        align-items: center;
        gap: 12px;
        flex-wrap: wrap;
    }
    .score-badge {
        background-color: #ff3b30;
        border-radius: 12px;
        padding: 6px 14px;
        font-size: 20px;
        font-weight: 800;
        color: #ffffff;
        white-space: nowrap;
    }
    .stock-name {
        font-size: 28px;
        font-weight: 800;
        color: #ffffff;
        line-height: 1.1;
    }
    .stock-code {
        font-size: 16px;
        color: #8e8e93;
        font-weight: 500;
    }

    .header-right {
        display: flex;
        flex-direction: column;
        align-items: flex-end;
        gap: 6px;
        max-width: 40%;
    }
    .main-price {
        font-size: 32px;
        font-weight: 900;
        line-height: 1;
        font-variant-numeric: tabular-nums;
    }
    .price-change {
        background-color: #3a1a1a;
        border-radius: 8px;
        padding: 4px 10px;
        font-size: 18px;
        font-weight: 700;
        line-height: 1;
        font-variant-numeric: tabular-nums;
        white-space: nowrap;
    }

    .diagnosis-box {
        width: 100%;
        background-color: #1e293b;
        border-radius: 16px;
        border-left: 6px solid #3b82f6;
        padding: 16px 20px;
        margin: 16px 0;
    }
    .diagnosis-title {
        color: #60a5fa;
        font-size: 18px;
        font-weight: 800;
    }
    .diagnosis-text {
        color: #ffffff;
        font-size: 18px;
        line-height: 1.6;
        margin-top: 4px;
    }

    .metrics-grid {
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        gap: 6px;
        width: 100%;
        margin-bottom: 16px;
    }
    .metric-item {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
        min-width: 0;
    }
    .metric-value {
        font-size: 20px;
        font-weight: 700;
        font-variant-numeric: tabular-nums;
        margin-bottom: 4px;
        white-space: nowrap;
    }
    .metric-label {
        font-size: 13px;
        color: #8e8e93;
        font-weight: 500;
        line-height: 1.2;
        white-space: nowrap;
    }

    .up-color {color: #ff3b30;}
    .down-color {color: #34c759;}

    .search-box {
        width: 100%;
        margin-bottom: 20px;
    }
    .stTextInput {width: 100% !important;}
    .stTextInput input {
        width: 100% !important;
        height: 48px;
        background-color: #17171a;
        border: 1px solid #2c2c2e;
        border-radius: 12px;
        padding: 0 16px;
        color: #ffffff;
        font-size: 16px;
    }
    .stTextInput input::placeholder {color: #8e8e93;}
</style>
""", unsafe_allow_html=True)

# ===================== 3. 顶部搜索栏 =====================
st.title("📈 鹰眼MRI · 股票卡片对比系统")
col_input, col_clear = st.columns([0.8, 0.2])
with col_input:
    new_stock = st.text_input(
        "",
        placeholder="🔍 输入股票代码（回车添加）",
        label_visibility="collapsed"
    )
    if new_stock:
        code_input = new_stock.strip().lower()
        if len(code_input) == 6:
            code_input = "sh" + code_input if code_input.startswith(('6', '9')) else "sz" + code_input
        if code_input not in st.session_state.stock_pool:
            st.session_state.stock_pool.insert(0, code_input)
            st.rerun()

with col_clear:
    if st.button("清空", use_container_width=True):
        st.session_state.stock_pool = []
        st.rerun()

# 手动刷新按钮（替代自动刷新，彻底解决死循环）
refresh_btn = st.button("🔄 刷新最新数据", type="primary", use_container_width=True)
if refresh_btn:
    st.cache_data.clear()
    st.rerun()

st.divider()

# ===================== 4. 数据获取（修复HTTPS问题） =====================
@st.cache_data(ttl=60)  # 缓存1分钟，手动点击刷新
def get_stock_data(code):
    try:
        # ✅ 改用HTTPS接口，彻底解决混合内容拦截
        response = requests.get(f"https://qt.gtimg.cn/q={code}", timeout=3)
        response.encoding = "gbk"
        raw_data = response.text.split("~")
        
        if len(raw_data) < 40:
            return None
        
        stock_name = raw_data[1]
        current_price = raw_data[3]
        yesterday_close = float(raw_data[4])
        open_price = float(raw_data[5])
        high_price = raw_data[33]
        change_percent = float(raw_data[32]) if raw_data[32] else 0.0
        
        open_premium = round((open_price - yesterday_close) / yesterday_close * 100, 2)
        intraday_entity = round((float(current_price) - open_price) / open_price * 100, 2)
        target_price = round(yesterday_close * 1.1, 2)
        
        is_buy_signal = change_percent >= 0
        
        return {
            "name": stock_name,
            "code": code,
            "short_code": code.replace("sh", "").replace("sz", ""),
            "price": current_price,
            "change": change_percent,
            "open_premium": open_premium,
            "intraday_entity": intraday_entity,
            "high_price": high_price,
            "target_price": target_price,
            "score": 90,
            "is_buy": is_buy_signal
        }
    except:
        return None

# ===================== 5. 股票卡片渲染 =====================
for stock_code in st.session_state.stock_pool:
    stock_info = get_stock_data(stock_code)
    if not stock_info:
        st.warning(f"⚠️ {stock_code} 数据获取失败，请检查代码")
        continue
    
    is_up = stock_info["change"] >= 0
    text_color = "up-color" if is_up else "down-color"
    signal_class = "signal-buy" if stock_info["is_buy"] else "signal-sell"
    
    with st.container():
        st.markdown(f'<div class="stock-card">', unsafe_allow_html=True)
        st.markdown(f'<div class="signal-border {signal_class}"></div>', unsafe_allow_html=True)
        
        if st.button("✕", key=f"del_{stock_code}"):
            st.session_state.stock_pool.remove(stock_code)
            st.rerun()
        
        st.markdown(f"""
        <div class="card-header">
            <div class="header-left">
                <div class="name-row">
                    <span class="score-badge">评分 {stock_info['score']}</span>
                    <span class="stock-name">{stock_info['name']}</span>
                </div>
                <div class="stock-code">{stock_info['short_code']}</div>
            </div>
            <div class="header-right">
                <div class="main-price {text_color}">{stock_info['price']}</div>
                <div class="price-change {text_color}">{stock_info['change']}%</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class="diagnosis-box">
            <span class="diagnosis-title">🎯✈️ 诊断推演：</span>
            <span class="diagnosis-text">属于典型的反核博弈信号。资金逆势扫货迹象明显，关注午后承接力度。</span>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class="metrics-grid">
            <div class="metric-item">
                <div class="metric-value {text_color}">{stock_info['open_premium']}%</div>
                <div class="metric-label">开盘溢价</div>
            </div>
            <div class="metric-item">
                <div class="metric-value up-color">{stock_info['intraday_entity']}%</div>
                <div class="metric-label">盘中实体</div>
            </div>
            <div class="metric-item">
                <div class="metric-value">{stock_info['high_price']}</div>
                <div class="metric-label">今日最高</div>
            </div>
            <div class="metric-item">
                <div class="metric-value up-color">{stock_info['target_price']}</div>
                <div class="metric-label">目标价</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div style="height: 80px;"></div>', unsafe_allow_html=True)
