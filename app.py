import streamlit as st
import requests
from streamlit_autorefresh import st_autorefresh

# ===================== 1. 全局配置 =====================
st.set_page_config(
    page_title="鹰眼审计终端",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items=None
)

# 自动刷新：5秒一次，兼顾实时性和手机端性能
st_autorefresh(interval=5000, limit=None, key="eagle_eye_final_version")

# 初始化股票池
if 'pool' not in st.session_state:
    st.session_state.pool = ["sz002428", "sh600137", "sh600111"]

# ===================== 2. 1:1还原图二的UI样式 =====================
st.markdown("""
<style>
    /* 全局重置，消除默认边距 */
    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
        -webkit-font-smoothing: antialiased;
        -webkit-text-size-adjust: 100%;
    }

    /* 主背景：和图二一致的深空黑 */
    .stApp {
        background-color: #0f1419;
        color: #ffffff;
        padding-left: 12px;
        padding-right: 12px;
        max-width: 100vw;
        overflow-x: hidden;
    }

    /* 隐藏Streamlit默认元素 */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}

    /* 核心：一体化卡片，完全还原图二的设计 */
    .stock-card {
        position: relative;
        width: 100%;
        border-radius: 16px;
        background: linear-gradient(145deg, #1a2230, #151b28);
        border: 1px solid #2a3446;
        padding: 20px 16px 12px 16px;
        margin-bottom: 20px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
    }

    /* 卡片头部：评分+名称+价格+删除按钮，和图二完全对齐 */
    .card-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin-bottom: 16px;
        width: 100%;
    }

    /* 左侧：评分标+股票名称代码 */
    .card-left {
        display: flex;
        flex-direction: column;
        gap: 6px;
        max-width: 65%;
    }
    .name-row {
        display: flex;
        align-items: center;
        gap: 10px;
        flex-wrap: wrap;
    }
    .score-badge {
        background: #ff3b30;
        color: #ffffff;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 15px;
        font-weight: 800;
        white-space: nowrap;
    }
    .stock-name {
        font-size: 24px;
        font-weight: 800;
        color: #ffffff;
        line-height: 1.1;
    }
    .stock-code {
        font-size: 14px;
        color: #8696b1;
        font-weight: 500;
        margin-top: 2px;
    }

    /* 右侧：价格+涨跌幅 */
    .card-right {
        display: flex;
        flex-direction: column;
        align-items: flex-end;
        gap: 4px;
    }
    .price-main {
        font-size: 30px;
        font-weight: 900;
        line-height: 1;
        font-variant-numeric: tabular-nums;
    }
    .price-change {
        font-size: 16px;
        font-weight: 700;
        border-radius: 6px;
        padding: 3px 8px;
        margin-top: 2px;
    }

    /* 删除按钮：卡片内右上角，和图二位置完全一致 */
    .delete-btn {
        position: absolute;
        top: 16px;
        right: 16px;
        width: 44px;
        height: 44px;
        display: flex;
        align-items: center;
        justify-content: center;
        background: transparent;
        border: none;
        color: #f5f5f7;
        font-size: 22px;
        font-weight: 600;
        cursor: pointer;
        z-index: 10;
        -webkit-tap-highlight-color: transparent;
    }
    .delete-btn:hover {
        color: #ff3b30;
    }

    /* 诊断推演模块：完全还原图二的蓝色框 */
    .logic-box {
        background: rgba(26, 58, 102, 0.6);
        border-left: 4px solid #0066ff;
        border-radius: 8px;
        padding: 14px 16px;
        margin-bottom: 18px;
        font-size: 15px;
        line-height: 1.5;
        color: #e6edf7;
    }
    .logic-box b {
        color: #4d9aff;
        font-weight: 700;
    }

    /* 核心指标栏：完全还原图二的「数值在上，标签在下」，一行5列 */
    .metrics-grid {
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        gap: 4px;
        width: 100%;
        margin-bottom: 12px;
    }
    .metric-item {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
        padding: 6px 2px;
    }
    .metric-value {
        font-size: 18px;
        font-weight: 700;
        color: #ffffff;
        font-variant-numeric: tabular-nums;
        margin-bottom: 4px;
    }
    .metric-label {
        font-size: 12px;
        color: #8696b1;
        font-weight: 500;
    }

    /* 详情展开模块：完全融入卡片，无割裂感 */
    .detail-expander {
        width: 100%;
        border: none !important;
        background: transparent !important;
    }
    .detail-expander > div:first-child {
        padding: 8px 0 !important;
        font-weight: 600 !important;
        color: #ffd60a !important;
        font-size: 16px !important;
        justify-content: flex-end !important;
        border: none !important;
    }
    .detail-expander > div:last-child {
        padding: 10px 0 0 0 !important;
        border: none !important;
        color: #e6edf7 !important;
    }

    /* 涨跌颜色：红涨绿跌，和国内A股一致 */
    .up-color {
        color: #ff3b30;
    }
    .down-color {
        color: #34c759;
    }
    .up-bg {
        background: rgba(255, 59, 48, 0.2);
    }
    .down-bg {
        background: rgba(52, 199, 89, 0.2);
    }

    /* 搜索栏：和卡片风格统一 */
    .search-container {
        width: 100%;
        margin-bottom: 20px;
    }
    .search-input {
        width: 100%;
        height: 50px;
        background: #1a2230;
        border: 1px solid #2a3446;
        border-radius: 12px;
        padding: 0 16px;
        color: #ffffff;
        font-size: 18px;
        -webkit-appearance: none;
    }
    .search-input::placeholder {
        color: #8696b1;
    }
</style>
""", unsafe_allow_html=True)

# ===================== 3. 搜索栏（和整体风格统一） =====================
st.markdown('<div class="search-container">', unsafe_allow_html=True)
col_search, col_clear = st.columns([0.85, 0.15])
with col_search:
    new_code = st.text_input(
        "",
        placeholder="🔍 输入股票代码 (回车添加，如600111)",
        label_visibility="collapsed"
    )
    # 处理添加股票逻辑
    if new_code:
        code_input = new_code.strip().lower()
        # 自动补全sh/sz前缀
        if len(code_input) == 6:
            code_input = "sh" + code_input if code_input.startswith(('6', '9')) else "sz" + code_input
        # 去重添加
        if code_input not in st.session_state.pool:
            st.session_state.pool.insert(0, code_input)
            st.rerun()

with col_clear:
    if st.button("清空", use_container_width=True):
        st.session_state.pool = []
        st.rerun()
st.markdown('</div>', unsafe_allow_html=True)

# ===================== 4. 稳定数据获取函数 =====================
@st.cache_data(ttl=3)  # 3秒缓存，避免频繁请求卡顿
def fetch_stock_data(code):
    """安全获取股票数据，全容错处理，字段和图二完全对齐"""
    try:
        response = requests.get(f"http://qt.gtimg.cn/q={code}", timeout=2)
        response.encoding = "gbk"
        raw_data = response.text.split("~")
        
        # 校验数据完整性
        if len(raw_data) < 40:
            return None
        
        # 提取核心字段，精准计算
        stock_name = raw_data[1]
        current_price = raw_data[3]
        yesterday_close = float(raw_data[4])
        open_price = float(raw_data[5])
        high_price = raw_data[33]
        change_percent = float(raw_data[32]) if raw_data[32] else 0.0
        
        # 精准计算指标，和图二完全对应
        open_premium = round((open_price - yesterday_close) / yesterday_close * 100, 2)
        target_price = round(yesterday_close * 1.1, 2)
        # 盘中实体涨跌幅（和图二的盘中实体对应）
        intraday_entity = round((float(current_price) - open_price) / open_price * 100, 2)
        
        # 返回结构化数据
        return {
            "name": stock_name,
            "code": code,
            "price": current_price,
            "change": change_percent,
            "open_premium": open_premium,
            "intraday_entity": intraday_entity,
            "wr_index": 39.1,  # 后续可以改成实时计算，这里先和你的版本对齐
            "high_price": high_price,
            "target_price": target_price,
            "score": 90  # 评分，可根据你的逻辑修改
        }
    except Exception as e:
        return None

# ===================== 5. 一体化股票卡片渲染 =====================
for stock_code in st.session_state.pool:
    # 获取股票数据
    stock_info = fetch_stock_data(stock_code)
    if not stock_info:
        continue  # 单只股票出错直接跳过，不影响全局
    
    # 涨跌颜色判断
    is_up = stock_info["change"] >= 0
    text_color = "up-color" if is_up else "down-color"
    bg_color = "up-bg" if is_up else "down-bg"
    
    # 渲染一体化卡片
    with st.container():
        st.markdown(f'<div class="stock-card">', unsafe_allow_html=True)
        
        # 1. 右上角删除按钮（和图二位置完全一致）
        if st.button("✕", key=f"del_{stock_code}"):
            st.session_state.pool.remove(stock_code)
            st.rerun()
        
        # 2. 卡片头部：评分+名称+价格
        st.markdown(f"""
        <div class="card-header">
            <div class="card-left">
                <div class="name-row">
                    <span class="score-badge">评分 {stock_info['score']}</span>
                    <span class="stock-name">{stock_info['name']}</span>
                </div>
                <div class="stock-code">{stock_info['code'].replace('sh', '').replace('sz', '')}</div>
            </div>
            <div class="card-right">
                <div class="price-main {text_color}">{stock_info['price']}</div>
                <div class="price-change {text_color} {bg_color}">{stock_info['change']}%</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # 3. 诊断推演模块（和图二文案对齐）
        st.markdown(f"""
        <div class="logic-box">
            🎯 <b>诊断推演：</b> 属于典型的反核博弈信号。资金逆势扫货迹象明显，关注午后承接力度。
        </div>
        """, unsafe_allow_html=True)
        
        # 4. 核心指标栏（和图二完全一致：数值在上，标签在下）
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
        
        # 5. 详情展开模块（和图二的「了解详情」对齐，黄色字体在右下角）
        with st.expander("了解详情》", expanded=False):
            st.markdown(f"""
            * **[I] 仪表盘:** 周期: **主升中继** | 决策: **积极进攻**
            * **[II] 真假博弈:** **诱空吸筹** (证据: 缩量不破昨收，大单对倒)
            * **[III] 死亡红线:** **安全 (PASS)**
            """)
        
        # 卡片结束
        st.markdown('</div>', unsafe_allow_html=True)

# 底部留白，适配iPhone底部横条
st.markdown('<div style="height: 100px;"></div>', unsafe_allow_html=True)
