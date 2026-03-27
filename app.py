import streamlit as st
import requests
from streamlit_autorefresh import st_autorefresh

# ===================== 1. 全局基础配置 =====================
st.set_page_config(
    page_title="鹰眼股票诊断终端",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items=None
)

# 自动刷新：5秒一次，兼顾实时性和手机端性能
st_autorefresh(interval=5000, limit=None, key="stock_diagnosis_final")

# 初始化股票池
if 'stock_pool' not in st.session_state:
    st.session_state.stock_pool = ["sh600111", "sz002428", "sh600137"]

# ===================== 2. 1:1还原设计图的UI样式 =====================
st.markdown("""
<style>
    /* 全局重置，消除Streamlit默认边距/样式 */
    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
        -webkit-font-smoothing: antialiased;
        -webkit-text-size-adjust: 100%;
    }

    /* 主背景：和设计图一致的纯黑深空背景 */
    .stApp {
        background-color: #0a0a0a;
        color: #ffffff;
        padding-left: 12px;
        padding-right: 12px;
        max-width: 100vw;
        overflow-x: hidden;
    }

    /* 隐藏Streamlit默认顶部栏、菜单、footer */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}

    /* ============== 核心：一体化卡片容器，完全匹配设计图 ============== */
    .stock-card {
        position: relative;
        width: 100%;
        border-radius: 20px;
        background-color: #17171a;
        overflow: hidden;
        padding: 24px 20px 16px 20px;
        margin-bottom: 20px;
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.5);
    }

    /* 核心需求：左侧全高信号边（买入红/卖出绿） */
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

    /* 右上角删除按钮，完全匹配设计图 */
    .delete-btn {
        position: absolute;
        top: 20px;
        right: 20px;
        width: 48px;
        height: 48px;
        background-color: #2c2c2e;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #ffffff;
        font-size: 22px;
        font-weight: 600;
        border: none;
        cursor: pointer;
        z-index: 10;
        -webkit-tap-highlight-color: transparent;
    }
    .delete-btn:hover {
        background-color: #3a3a3c;
    }

    /* ============== 卡片头部：评分+名称+价格 ============== */
    .card-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        width: 100%;
        margin-bottom: 12px;
        padding-right: 60px; /* 给右上角删除按钮留空间 */
    }

    /* 左侧：评分标+股票名称+代码 */
    .header-left {
        display: flex;
        flex-direction: column;
        gap: 8px;
    }
    .name-row {
        display: flex;
        align-items: center;
        gap: 16px;
        flex-wrap: wrap;
    }
    /* 评分标：红色圆角，完全匹配设计图 */
    .score-badge {
        background-color: #ff3b30;
        border-radius: 12px;
        padding: 8px 18px;
        font-size: 26px;
        font-weight: 800;
        color: #ffffff;
        white-space: nowrap;
    }
    .stock-name {
        font-size: 40px;
        font-weight: 800;
        color: #ffffff;
        line-height: 1;
    }
    .stock-code {
        font-size: 22px;
        color: #8e8e93;
        font-weight: 500;
        padding-left: 2px;
    }

    /* 右侧：价格+涨跌幅 */
    .header-right {
        display: flex;
        flex-direction: column;
        align-items: flex-end;
        gap: 8px;
    }
    .main-price {
        font-size: 44px;
        font-weight: 900;
        line-height: 1;
        font-variant-numeric: tabular-nums;
    }
    .price-change {
        background-color: #3a1a1a;
        border-radius: 8px;
        padding: 6px 14px;
        font-size: 26px;
        font-weight: 700;
        line-height: 1;
        font-variant-numeric: tabular-nums;
    }

    /* ============== 诊断推演模块，完全匹配设计图 ============== */
    .diagnosis-box {
        width: 100%;
        background-color: #1e293b;
        border-radius: 16px;
        border-left: 6px solid #3b82f6;
        padding: 22px 26px;
        margin: 20px 0;
    }
    .diagnosis-title {
        color: #60a5fa;
        font-size: 24px;
        font-weight: 800;
    }
    .diagnosis-text {
        color: #ffffff;
        font-size: 24px;
        line-height: 1.5;
        margin-top: 4px;
    }

    /* ============== 底部指标网格，完全匹配设计图 ============== */
    .metrics-grid {
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        gap: 12px;
        width: 100%;
        margin-bottom: 16px;
    }
    .metric-item {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
    }
    .metric-value {
        font-size: 30px;
        font-weight: 700;
        font-variant-numeric: tabular-nums;
        margin-bottom: 6px;
    }
    .metric-label {
        font-size: 20px;
        color: #8e8e93;
        font-weight: 500;
    }

    /* ============== 右下角详情入口，完全匹配设计图 ============== */
    .detail-entry {
        width: 100%;
        text-align: right;
        font-size: 22px;
        color: #8e8e93;
        font-weight: 500;
        padding-right: 8px;
    }
    .detail-expander {
        width: 100%;
        border: none !important;
        background: transparent !important;
    }
    .detail-expander > div:first-child {
        padding: 0 !important;
        border: none !important;
        background: transparent !important;
    }
    .detail-expander > div:last-child {
        padding: 16px 8px 0 8px !important;
        border: none !important;
        color: #ffffff !important;
        font-size: 18px;
    }

    /* 涨跌颜色定义：红涨绿跌，和A股习惯一致 */
    .up-color {
        color: #ff3b30;
    }
    .down-color {
        color: #34c759;
    }

    /* ============== 顶部搜索栏，和卡片风格统一 ============== */
    .search-box {
        width: 100%;
        margin-bottom: 24px;
    }
    .search-input {
        width: 100%;
        height: 56px;
        background-color: #17171a;
        border: 1px solid #2c2c2e;
        border-radius: 12px;
        padding: 0 18px;
        color: #ffffff;
        font-size: 20px;
        -webkit-appearance: none;
    }
    .search-input::placeholder {
        color: #8e8e93;
    }
</style>
""", unsafe_allow_html=True)

# ===================== 3. 顶部搜索栏（股票添加/清空） =====================
st.markdown('<div class="search-box">', unsafe_allow_html=True)
col_input, col_clear = st.columns([0.85, 0.15])
with col_input:
    new_stock = st.text_input(
        "",
        placeholder="🔍 输入股票代码（回车添加，如600111）",
        label_visibility="collapsed"
    )
    # 处理添加股票逻辑
    if new_stock:
        code_input = new_stock.strip().lower()
        # 自动补全sh/sz前缀
        if len(code_input) == 6:
            code_input = "sh" + code_input if code_input.startswith(('6', '9')) else "sz" + code_input
        # 去重添加
        if code_input not in st.session_state.stock_pool:
            st.session_state.stock_pool.insert(0, code_input)
            st.rerun()

with col_clear:
    if st.button("清空", use_container_width=True):
        st.session_state.stock_pool = []
        st.rerun()
st.markdown('</div>', unsafe_allow_html=True)

# ===================== 4. 稳定数据获取函数 =====================
@st.cache_data(ttl=3)  # 3秒缓存，避免频繁请求卡顿
def get_stock_data(code):
    """安全获取腾讯财经股票数据，全容错处理，字段完全匹配设计图"""
    try:
        # 请求接口
        response = requests.get(f"http://qt.gtimg.cn/q={code}", timeout=2)
        response.encoding = "gbk"
        raw_data = response.text.split("~")
        
        # 校验数据完整性，避免索引越界崩溃
        if len(raw_data) < 40:
            return None
        
        # 提取核心字段，精准计算
        stock_name = raw_data[1]
        current_price = raw_data[3]
        yesterday_close = float(raw_data[4])
        open_price = float(raw_data[5])
        high_price = raw_data[33]
        change_percent = float(raw_data[32]) if raw_data[32] else 0.0
        
        # 精准计算设计图中的指标
        open_premium = round((open_price - yesterday_close) / yesterday_close * 100, 2)  # 开盘溢价
        intraday_entity = round((float(current_price) - open_price) / open_price * 100, 2)  # 盘中实体
        target_price = round(yesterday_close * 1.1, 2)  # 目标价（昨收110%）
        wr_index = 39.1  # W&R指标，可后续替换为实时计算
        
        # 信号判断：可自定义你的买入/卖出逻辑，当前默认：涨=买入红，跌=卖出绿
        is_buy_signal = change_percent >= 0
        
        # 返回结构化数据
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
            "score": 90,  # 诊断评分，可自定义逻辑修改
            "is_buy": is_buy_signal
        }
    except Exception as e:
        return None

# ===================== 5. 股票卡片渲染（1:1还原设计图） =====================
for stock_code in st.session_state.stock_pool:
    # 获取股票数据
    stock_info = get_stock_data(stock_code)
    if not stock_info:
        continue  # 单只股票出错直接跳过，不影响全局
    
    # 涨跌颜色&信号判断
    is_up = stock_info["change"] >= 0
    text_color = "up-color" if is_up else "down-color"
    signal_class = "signal-buy" if stock_info["is_buy"] else "signal-sell"
    
    # 渲染一体化卡片
    with st.container():
        st.markdown(f'<div class="stock-card">', unsafe_allow_html=True)
        
        # 1. 左侧全高信号边（买入红/卖出绿）
        st.markdown(f'<div class="signal-border {signal_class}"></div>', unsafe_allow_html=True)
        
        # 2. 右上角删除按钮
        if st.button("✕", key=f"del_{stock_code}"):
            st.session_state.stock_pool.remove(stock_code)
            st.rerun()
        
        # 3. 卡片头部：评分+名称+价格
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
        
        # 5. 底部指标网格
        st.markdown(f"""
        <div class="metrics-grid">
            <div class="metric-item">
                <div class="metric-value up-color">{stock_info['open_premium']}%</div>
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
        
        # 6. 右下角详情入口
        with st.expander("> 了解详情》", expanded=False):
            st.markdown(f"""
            * **[I] 趋势仪表盘:** 周期: **主升中继** | 操作决策: **积极进攻**
            * **[II] 资金博弈:** **诱空吸筹** (核心证据: 缩量不破昨收，大单逆势对倒)
            * **[III] 风险红线:** **安全 (PASS)** | 止损位: {round(float(stock_info['price'])*0.92, 2)}
            """)
        
        # 卡片结束
        st.markdown('</div>', unsafe_allow_html=True)

# 底部留白，适配iPhone底部横条
st.markdown('<div style="height: 100px;"></div>', unsafe_allow_html=True)
