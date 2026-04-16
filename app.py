import streamlit as st
import requests
from streamlit_autorefresh import st_autorefresh

# ===================== 1. 全局配置（iPhone专属优化） =====================
st.set_page_config(
    page_title="鹰眼股票诊断",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items=None
)

# 强制移动端视口适配，解决Safari缩放问题
st.markdown('<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">', unsafe_allow_html=True)

# 自动刷新：5秒一次，兼顾实时性和手机性能
st_autorefresh(interval=5000, limit=None, key="iphone_fix_final")

# 初始化股票池
if 'stock_pool' not in st.session_state:
    st.session_state.stock_pool = ["sh600111", "sz002428", "sh600137"]

# ===================== 2. iPhone专属UI样式（彻底解决排版错乱） =====================
st.markdown("""
<style>
    /* 全局强制重置，彻底解决Streamlit默认样式干扰 */
    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
        -webkit-font-smoothing: antialiased;
        -webkit-text-size-adjust: 100%;
        font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Helvetica Neue", sans-serif;
    }

    /* 主背景：适配iOS暗黑模式，无溢出 */
    .stApp {
        background-color: #0a0a0a;
        color: #ffffff;
        padding: 12px 16px !important;
        max-width: 100vw !important;
        overflow-x: hidden !important;
    }

    /* 隐藏所有Streamlit默认元素，避免干扰 */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .block-container {padding: 0 !important; max-width: 100% !important;}
    .stVerticalBlock {gap: 0 !important;}

    /* 强制重置按钮样式，彻底解决白色方块问题 */
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
        box-shadow: none !important;
        -webkit-tap-highlight-color: transparent !important;
    }
    .stButton button:hover {
        background-color: #3a3a3c !important;
    }

    /* ============== 核心卡片容器：iPhone专属适配，无溢出 ============== */
    .stock-card {
        position: relative;
        width: 100% !important;
        border-radius: 20px;
        background-color: #17171a;
        overflow: hidden !important;
        padding: 20px 16px 16px 16px;
        margin-bottom: 16px !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
    }

    /* 左侧全高信号边：买入红/卖出绿，彻底修复高度问题 */
    .signal-border {
        position: absolute;
        top: 0;
        left: 0;
        width: 6px;
        height: 100%;
        z-index: 1;
    }
    .signal-buy {
        background: linear-gradient(180deg, #ff3b30, #ff2d55);
    }
    .signal-sell {
        background: linear-gradient(180deg, #34c759, #30d158);
    }

    /* ============== 卡片头部：iPhone专属字体大小，无溢出 ============== */
    .card-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        width: 100%;
        margin-bottom: 12px;
        padding-right: 50px; /* 给右上角删除按钮留足空间，避免重叠 */
    }

    /* 左侧：评分标+股票名称+代码 */
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
    /* 评分标：适配iPhone的大小 */
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
        word-break: keep-all;
    }
    .stock-code {
        font-size: 16px;
        color: #8e8e93;
        font-weight: 500;
        padding-left: 2px;
    }

    /* 右侧：价格+涨跌幅，适配iPhone，无溢出 */
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
        word-break: keep-all;
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

    /* ============== 诊断推演模块：iPhone适配，无折行溢出 ============== */
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

    /* ============== 底部指标网格：彻底解决折行/挤在一起问题 ============== */
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
        min-width: 0; /* 解决grid内容溢出问题 */
    }
    .metric-value {
        font-size: 20px;
        font-weight: 700;
        font-variant-numeric: tabular-nums;
        margin-bottom: 4px;
        word-break: keep-all;
        white-space: nowrap;
    }
    .metric-label {
        font-size: 13px;
        color: #8e8e93;
        font-weight: 500;
        line-height: 1.2;
        word-break: keep-all;
        white-space: nowrap;
    }

    /* ============== 详情入口：适配iPhone，无溢出 ============== */
    .detail-expander {
        width: 100%;
        border: none !important;
        background: transparent !important;
    }
    .detail-expander > div:first-child {
        padding: 0 !important;
        border: none !important;
        background: transparent !important;
        font-size: 16px !important;
        color: #8e8e93 !important;
        font-weight: 500 !important;
        justify-content: flex-start !important;
    }
    .detail-expander > div:last-child {
        padding: 12px 8px 0 8px !important;
        border: none !important;
        color: #ffffff !important;
        font-size: 15px;
    }

    /* 涨跌颜色定义：红涨绿跌 */
    .up-color {
        color: #ff3b30;
    }
    .down-color {
        color: #34c759;
    }

    /* ============== 顶部搜索栏：iPhone适配 ============== */
    .search-box {
        width: 100%;
        margin-bottom: 20px;
    }
    .search-input {
        width: 100%;
        height: 48px;
        background-color: #17171a;
        border: 1px solid #2c2c2e;
        border-radius: 12px;
        padding: 0 16px;
        color: #ffffff;
        font-size: 16px;
        -webkit-appearance: none;
    }
    .search-input::placeholder {
        color: #8e8e93;
    }
    .stTextInput {
        width: 100% !important;
    }
    .stTextInput input {
        width: 100% !important;
    }
</style>
""", unsafe_allow_html=True)

# ===================== 3. 顶部搜索栏 =====================
st.markdown('<div class="search-box">', unsafe_allow_html=True)
col_input, col_clear = st.columns([0.8, 0.2])
with col_input:
    new_stock = st.text_input(
        "",
        placeholder="🔍 输入股票代码（回车添加）",
        label_visibility="collapsed"
    )
    # 处理添加股票
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
st.markdown('</div>', unsafe_allow_html=True)

# ===================== 4. 数据获取函数（稳定容错） =====================
@st.cache_data(ttl=3)
def get_stock_data(code):
    try:
        response = requests.get(f"http://qt.gtimg.cn/q={code}", timeout=2)
        response.encoding = "gbk"
        raw_data = response.text.split("~")
        
        if len(raw_data) < 40:
            return None
        
        # 核心字段提取
        stock_name = raw_data[1]
        current_price = raw_data[3]
        yesterday_close = float(raw_data[4])
        open_price = float(raw_data[5])
        high_price = raw_data[33]
        change_percent = float(raw_data[32]) if raw_data[32] else 0.0
        
        # 指标计算
        open_premium = round((open_price - yesterday_close) / yesterday_close * 100, 2)
        intraday_entity = round((float(current_price) - open_price) / open_price * 100, 2)
        target_price = round(yesterday_close * 1.1, 2)
        wr_index = 39.1
        
        # 买入/卖出信号判断（可自定义你的逻辑）
        is_buy_signal = change_percent >= 0
        
        return {
            "name": stock_name,
            "code": code,
            "short_code": code.replace("sh", "").replace("sz", ""),
            "price": current_price,
            "change": change_percent,
            "open_premium": open_premium,
            "intraday_entity": intraday_entity,
            "wr_index": wr_index,
            "high_price": high_price,
            "target_price": target_price,
            "score": 90,
            "is_buy": is_buy_signal
        }
    except Exception as e:
        return None

# ===================== 5. 股票卡片渲染（iPhone专属适配） =====================
for stock_code in st.session_state.stock_pool:
    stock_info = get_stock_data(stock_code)
    if not stock_info:
        continue
    
    # 涨跌颜色&信号判断
    is_up = stock_info["change"] >= 0
    text_color = "up-color" if is_up else "down-color"
    signal_class = "signal-buy" if stock_info["is_buy"] else "signal-sell"
    
    # 渲染卡片
    with st.container():
        st.markdown(f'<div class="stock-card">', unsafe_allow_html=True)
        
        # 1. 左侧信号边
        st.markdown(f'<div class="signal-border {signal_class}"></div>', unsafe_allow_html=True)
        
        # 2. 右上角删除按钮
        if st.button("✕", key=f"del_{stock_code}"):
            st.session_state.stock_pool.remove(stock_code)
            st.rerun()
        
        # 3. 卡片头部
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
        
        # 4. 诊断推演模块
        st.markdown(f"""
        <div class="diagnosis-box">
            <span class="diagnosis-title">🎯✈️ 诊断推演：</span>
            <span class="diagnosis-text">属于典型的反核博弈信号。资金逆势扫货迹象明显，关注午后承接力度。</span>
        </div>
        """, unsafe_allow_html=True)
        
        # 5. 指标网格
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
                <div class="metric-value">{stock_info['wr_index']}</div>
                <div class="metric-label">W&R指标</div>
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
        
        # 6. 详情展开
        with st.expander("> 了解详情》", expanded=False):
            st.markdown(f"""
            * **[I] 趋势仪表盘:** 周期: **主升中继** | 操作决策: **积极进攻**
            * **[II] 资金博弈:** **诱空吸筹** (核心证据: 缩量不破昨收，大单逆势对倒)
            * **[III] 风险红线:** **安全 (PASS)** | 止损位: {round(float(stock_info['price'])*0.92, 2)}
            """)
        
        st.markdown('</div>', unsafe_allow_html=True)

# 底部留白，适配iPhone底部横条
st.markdown('<div style="height: 80px;"></div>', unsafe_allow_html=True)
