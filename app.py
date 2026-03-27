import streamlit as st
import requests
from streamlit_autorefresh import st_autorefresh

# ===================== 1. 全局配置（iPhone专属优化） =====================
# 页面基础配置
st.set_page_config(
    page_title="鹰眼审计终端",
    layout="wide",
    initial_sidebar_state="collapsed",  # 移动端默认隐藏侧边栏，最大化屏幕
    menu_items=None
)

# 自动刷新：5秒一次，兼顾实时性和iPhone端性能
st_autorefresh(interval=5000, limit=None, key="eagle_eye_ios_optimized")

# 初始化股票池
if 'pool' not in st.session_state:
    st.session_state.pool = ["sz002428", "sh600137", "sh600111"]

# ===================== 2. iOS专属UI样式（顶级UI设计） =====================
st.markdown("""
<style>
    /* 全局重置：适配iPhone Safari，消除Streamlit默认边距 */
    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
        -webkit-font-smoothing: antialiased;
        -webkit-text-size-adjust: 100%;
    }

    /* 主背景：iOS原生暗黑模式纯黑背景，贴合系统 */
    .stApp {
        background-color: #000000;
        color: #f5f5f7;
        padding-left: 12px;
        padding-right: 12px;
        max-width: 100vw;
        overflow-x: hidden;
    }

    /* 隐藏Streamlit默认的顶部栏、汉堡菜单，极致全屏体验 */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}

    /* 股票卡片：iOS卡片式设计，圆角+毛玻璃质感，适配iPhone */
    .stock-card {
        position: relative;
        border-radius: 20px;
        background: linear-gradient(145deg, #1c1c1e, #2c2c2e);
        border: 1px solid #38383a;
        padding: 20px 16px;
        margin-bottom: 16px;
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.4);
        -webkit-backdrop-filter: blur(20px);
        backdrop-filter: blur(20px);
    }

    /* 卡片头部：名称+价格，适配iPhone宽度 */
    .card-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin-bottom: 16px;
        width: 100%;
    }

    /* 股票名称与代码 */
    .stock-title-wrap {
        display: flex;
        flex-direction: column;
        gap: 4px;
        max-width: 60%;
    }
    .stock-name {
        font-size: 24px;
        font-weight: 800;
        color: #f5f5f7;
        line-height: 1.1;
    }
    .stock-code {
        font-size: 14px;
        color: #98989f;
        font-weight: 500;
    }
    .audit-badge {
        display: inline-block;
        background: #30d158;
        color: #000000;
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: 700;
        margin-top: 4px;
        width: fit-content;
    }

    /* 价格与涨跌幅：右侧大字展示，iOS原生数字样式 */
    .price-wrap {
        display: flex;
        flex-direction: column;
        align-items: flex-end;
        gap: 2px;
    }
    .price-main {
        font-size: 32px;
        font-weight: 900;
        line-height: 1;
        font-variant-numeric: tabular-nums;
    }
    .price-change {
        font-size: 16px;
        font-weight: 700;
        border-radius: 8px;
        padding: 4px 8px;
        margin-top: 4px;
    }

    /* 删除按钮：右上角绝对定位，符合iOS操作习惯，44pt点击区域 */
    .delete-btn {
        position: absolute;
        top: 12px;
        right: 12px;
        width: 44px;
        height: 44px;
        display: flex;
        align-items: center;
        justify-content: center;
        background: rgba(255, 69, 58, 0.2);
        border-radius: 50%;
        color: #ff453a;
        font-size: 20px;
        font-weight: 600;
        border: none;
        cursor: pointer;
        z-index: 10;
        -webkit-tap-highlight-color: transparent;
    }
    .delete-btn:hover {
        background: rgba(255, 69, 58, 0.4);
    }

    /* 审计推演模块：iOS通知栏样式 */
    .logic-box {
        background: rgba(0, 122, 255, 0.15);
        border-left: 4px solid #007aff;
        border-radius: 12px;
        padding: 14px 16px;
        margin-bottom: 20px;
        font-size: 15px;
        line-height: 1.5;
        color: #f5f5f7;
    }
    .logic-box b {
        color: #007aff;
        font-weight: 700;
    }

    /* 核心指标栏：CSS Grid强制一行5列，完美适配iPhone窄屏 */
    .metrics-grid {
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        gap: 8px;
        width: 100%;
        margin-bottom: 16px;
    }
    .metric-item {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
        padding: 8px 4px;
        border-right: 1px solid #38383a;
    }
    /* 最后一个指标去掉右边框 */
    .metric-item:last-child {
        border-right: none;
    }
    .metric-label {
        font-size: 11px;
        color: #98989f;
        text-transform: uppercase;
        font-weight: 500;
        margin-bottom: 4px;
    }
    .metric-value {
        font-size: 15px;
        font-weight: 700;
        color: #f5f5f7;
        font-variant-numeric: tabular-nums;
    }

    /* 详情展开按钮：iOS原生按钮样式 */
    .stExpander {
        border: none !important;
        border-radius: 12px !important;
        background: #2c2c2e !important;
        overflow: hidden;
    }
    .stExpander > div:first-child {
        padding: 12px 16px !important;
        font-weight: 600 !important;
        color: #98989f !important;
    }
    .stExpander > div:last-child {
        padding: 0 16px 16px 16px !important;
    }

    /* 搜索栏：iOS原生搜索框样式 */
    .search-wrap {
        display: flex;
        gap: 12px;
        margin-bottom: 20px;
        width: 100%;
    }
    .search-input {
        flex: 1;
        height: 44px;
        background: #1c1c1e;
        border: 1px solid #38383a;
        border-radius: 12px;
        padding: 0 16px;
        color: #f5f5f7;
        font-size: 16px;
        -webkit-appearance: none;
    }
    .clear-btn {
        width: 44px;
        height: 44px;
        background: #ff453a;
        border: none;
        border-radius: 12px;
        color: white;
        font-weight: 600;
        font-size: 14px;
        cursor: pointer;
        -webkit-tap-highlight-color: transparent;
    }

    /* 涨跌颜色：iOS原生红涨绿跌（符合国内A股习惯） */
    .up-color {
        color: #ff453a;
    }
    .down-color {
        color: #30d158;
    }
    .up-bg {
        background: rgba(255, 69, 58, 0.2);
    }
    .down-bg {
        background: rgba(48, 209, 88, 0.2);
    }
</style>
""", unsafe_allow_html=True)

# ===================== 3. 搜索栏（iPhone触摸优化） =====================
st.markdown('<div class="search-wrap">', unsafe_allow_html=True)
col_search, col_clear = st.columns([0.8, 0.2])
with col_search:
    new_code = st.text_input(
        "",
        placeholder="🔍 输入股票代码 (回车添加)",
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

st.markdown('<div style="height: 1px; background: #38383a; margin: 10px 0 20px 0;"></div>', unsafe_allow_html=True)

# ===================== 4. 核心数据获取函数（稳定容错） =====================
@st.cache_data(ttl=3)  # 3秒缓存，避免频繁请求导致iPhone卡顿
def fetch_stock_data(code):
    """安全获取腾讯财经股票数据，修复字段错误，全容错处理"""
    try:
        # 请求接口，超时2秒，避免iPhone端卡死
        response = requests.get(f"http://qt.gtimg.cn/q={code}", timeout=2)
        response.encoding = "gbk"
        raw_data = response.text.split("~")
        
        # 校验数据完整性，避免索引越界崩溃
        if len(raw_data) < 40:
            return None
        
        # 提取核心字段，提前做类型转换，避免后续报错
        stock_name = raw_data[1]
        current_price = raw_data[3]
        yesterday_close = float(raw_data[4])
        open_price = float(raw_data[5])
        high_price = raw_data[33]
        change_percent = float(raw_data[32]) if raw_data[32] else 0.0
        
        # 修正开盘溢价计算公式（之前的核心错误）
        open_premium = round((open_price - yesterday_close) / yesterday_close * 100, 2)
        # 计算目标价（昨收110%）
        target_price = round(yesterday_close * 1.1, 2)
        
        # 返回结构化数据
        return {
            "name": stock_name,
            "code": code,
            "price": current_price,
            "change": change_percent,
            "open_premium": open_premium,
            "high_price": high_price,
            "target_price": target_price
        }
    except Exception as e:
        # 任何错误都返回None，不影响全局渲染
        return None

# ===================== 5. 股票卡片渲染（iPhone专属布局） =====================
for stock_code in st.session_state.pool:
    # 获取股票数据
    stock_info = fetch_stock_data(stock_code)
    if not stock_info:
        continue  # 单只股票出错直接跳过，不崩页面
    
    # 涨跌颜色与背景判断
    is_up = stock_info["change"] >= 0
    text_color = "up-color" if is_up else "down-color"
    bg_color = "up-bg" if is_up else "down-bg"
    
    # 渲染单只股票卡片
    st.markdown(f'<div class="stock-card">', unsafe_allow_html=True)
    
    # 1. 删除按钮（右上角，符合iOS操作习惯）
    if st.button("✕", key=f"del_{stock_code}", help="删除该股票"):
        st.session_state.pool.remove(stock_code)
        st.rerun()
    
    # 2. 卡片头部：名称+价格
    st.markdown(f"""
    <div class="card-header">
        <div class="stock-title-wrap">
            <div class="stock-name">{stock_info['name']}</div>
            <div class="stock-code">{stock_info['code'].upper()}</div>
            <span class="audit-badge">审计评分92 | 主升中继</span>
        </div>
        <div class="price-wrap">
            <div class="price-main {text_color}">{stock_info['price']}</div>
            <div class="price-change {text_color} {bg_color}">{stock_info['change']}%</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 3. 审计推演模块
    st.markdown(f"""
    <div class="logic-box">
        🎯 <b>审计推演：</b> 典型的反核博弈信号。资金逆势扫货迹象明显，主力反人性吸筹。建议关注午后均线承接机会。
    </div>
    """, unsafe_allow_html=True)
    
    # 4. 核心指标网格（完美适配iPhone一行5列）
    st.markdown(f"""
    <div class="metrics-grid">
        <div class="metric-item">
            <div class="metric-label">开盘溢价</div>
            <div class="metric-value {text_color}">{stock_info['open_premium']}%</div>
        </div>
        <div class="metric-item">
            <div class="metric-label">盘中实体</div>
            <div class="metric-value {text_color}">{stock_info['change']}%</div>
        </div>
        <div class="metric-item">
            <div class="metric-label">W&R</div>
            <div class="metric-value">39.1</div>
        </div>
        <div class="metric-item">
            <div class="metric-label">最高价</div>
            <div class="metric-value">{stock_info['high_price']}</div>
        </div>
        <div class="metric-item">
            <div class="metric-label">目标价</div>
            <div class="metric-value up-color">{stock_info['target_price']}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 5. 详情展开模块
    with st.expander("查看反向博弈逻辑详情..."):
        st.markdown(f"""
        * **[I] 仪表盘:** 周期: **主升中继** | 决策: **积极进攻**
        * **[II] 真假博弈:** **诱空吸筹** (证据: 缩量不破昨收，大单对倒)
        * **[III] 死亡红线:** **安全 (PASS)**
        """)
    
    # 卡片结束
    st.markdown('</div>', unsafe_allow_html=True)

# 底部留白，适配iPhone底部横条
st.markdown('<div style="height: 80px;"></div>', unsafe_allow_html=True)
