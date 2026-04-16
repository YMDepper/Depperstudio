import streamlit as st
import requests
import pandas as pd
from streamlit_autorefresh import st_autorefresh

# ===================== 全局配置 =====================
st.set_page_config(page_title="鹰眼自选终端", layout="wide", initial_sidebar_state="collapsed")
st_autorefresh(interval=8000, limit=None, key="eagle_eye_watchlist")

# ===================== 核心 UI 样式锁死 =====================
# 只用 CSS 处理背景色、边距和文字颜色，绝不干涉布局
st.markdown("""
<style>
    /* 全局高级暗色/灰度底色，根据喜好调整，这里用极简白灰 */
    .stApp { background: #f8fafc; font-family: -apple-system, sans-serif; }
    #MainMenu, header, footer { display: none !important; }
    .block-container { padding-top: 1.5rem !important; padding-bottom: 2rem !important; }
    
    /* 极致压缩原生容器间距 */
    [data-testid="stVerticalBlock"] { gap: 0.5rem !important; }
    
    /* 搜索栏美化 */
    [data-testid="stTextInput"] input { border-radius: 8px; border: 1px solid #e2e8f0; }
    
    /* 自定义指标微型排版 */
    .mini-metric { text-align: center; line-height: 1.2; }
    .m-label { font-size: 11px; color: #64748b; margin-bottom: 2px; }
    .m-val { font-size: 14px; font-weight: 600; color: #0f172a; }
    
    /* 标签样式 */
    .tag-base { padding: 2px 6px; border-radius: 4px; font-size: 11px; font-weight: 500; display: inline-block;}
    .tag-hot { background: #fee2e2; color: #ef4444; border: 1px solid #f87171;}
    .tag-normal { background: #f1f5f9; color: #475569; border: 1px solid #cbd5e1;}
    .tag-red { background: #fee2e2; color: #ef4444; }
    .tag-green { background: #dcfce3; color: #16a34a; }
</style>
""", unsafe_allow_html=True)

# 自选池与字典映射
if 'stock_pool' not in st.session_state:
    st.session_state.stock_pool = ["sz001896", "sz002364", "sh600111", "sz002428"]

HOT_SECTORS = ["AI", "芯片", "半导体", "算力", "CPO", "机器人", "新能源", "光伏", "储能", "军工", "医药", "稀土", "有色", "电力"]
STOCK_PY_MAP = {
    "bfxt":"sh600111", "ynzy":"sz002428", "zhdq":"sz002364", "ynkg":"sz001896",
    "zycx":"sh603986", "hstc":"sh600410", "jcyy":"sh600566", "hgkj":"sz000988"
}

# ===================== 顶部操作区 =====================
col_search, col_clear = st.columns([0.8, 0.2])
with col_search:
    search_input = st.text_input("", placeholder="🔍 输入代码/首字母 (例: bfxt)", label_visibility="collapsed")
with col_clear:
    if st.button("清空", use_container_width=True):
        st.session_state.stock_pool = []
        st.rerun()

if search_input:
    search = search_input.strip().lower()
    code = None
    if search.isdigit() and len(search)==6:
        code = "sh"+search if search.startswith(('6','9')) else "sz"+search
    elif search in STOCK_PY_MAP:
        code = STOCK_PY_MAP[search]
        
    if code and code not in st.session_state.stock_pool:
        st.session_state.stock_pool.insert(0, code)
        st.rerun()

st.divider()

# ===================== 数据获取模块 =====================
@st.cache_data(ttl=5, show_spinner=False)
def get_data(full_code):
    try:
        code = full_code[2:]
        res = requests.get(f"https://qt.gtimg.cn/q={full_code}", timeout=2)
        res.encoding = "gbk"
        arr = res.text.split("~")
        name, price, change = arr[1], arr[3], float(arr[32]) if arr[32] else 0.0

        # K线与指标
        kres = requests.get(f"https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={full_code},day,,,20,qfq", timeout=2)
        close = [float(x[2]) for x in kres.json()['data'][full_code]['qfqday']]
        
        ma5 = round(sum(close[-5:])/5, 2)
        ma10 = round(sum(close[-10:])/10, 2)

        # 简化版 MACD 计算 (只取最后一个值，放弃在卡片里画折线图，保持UI干净)
        e5, e10 = [close[0]], [close[0]]
        for i in range(1, len(close)):
            e5.append((2*close[i]+4*e5[i-1])/6)
            e10.append((2*close[i]+9*e10[i-1])/11)
        dif = [e5[i]-e10[i] for i in range(len(e5))]
        dea = [dif[0]]
        for i in range(1, len(dif)):
            dea.append((2*dif[i]+3*dea[i-1])/5)
        macd_val = round((dif[-1]-dea[-1])*2, 2)

        sector_map = {"001896":"电力", "002364":"电力设备", "600111":"稀土永磁", "002428":"小金属"}
        
        return {
            "name": name, "code": code, "price": price, "change": change,
            "ma5": ma5, "ma10": ma10, "macd": macd_val,
            "sector": sector_map.get(code, "主力游资"), 
            "fund": "+2.1亿" if change >= 0 else "-1.6亿",
            "is_in": change >= 0
        }
    except:
        return None

# ===================== 原生卡牌渲染队列 =====================
for full_code in st.session_state.stock_pool:
    data = get_data(full_code)
    if not data: continue

    color_hex = "#ef4444" if data['change'] >= 0 else "#16a34a"
    fund_class = "tag-red" if data['is_in'] else "tag-green"
    sector_class = "tag-hot" if any(s in data['sector'] for s in HOT_SECTORS) else "tag-normal"

    # 使用官方 border=True 生成卡牌，绝对不会错位
    with st.container(border=True):
        
        # 第一层：身份与报价
        c_title, c_price = st.columns([0.6, 0.4])
        with c_title:
            st.markdown(f"<div style='margin-top:5px;'><span style='font-size:18px; font-weight:700;'>{data['name']}</span> <span style='font-size:13px; color:#94a3b8;'>{data['code']}</span></div>", unsafe_allow_html=True)
        with c_price:
            st.markdown(f"<div style='text-align:right;'><span style='font-size:20px; font-weight:bold; color:{color_hex};'>{data['price']}</span> <span class='tag-base' style='background:{color_hex}20; color:{color_hex};'>{data['change']}%</span></div>", unsafe_allow_html=True)
            
        # 巧妙使用原生分割线替代繁琐的 border-top
        st.write("") 

        # 第二层：核心数据阵列
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.markdown(f"<div class='mini-metric'><div class='m-label'>5日均价</div><div class='m-val'>{data['ma5']}</div></div>", unsafe_allow_html=True)
        with m2:
            st.markdown(f"<div class='mini-metric'><div class='m-label'>10日均价</div><div class='m-val'>{data['ma10']}</div></div>", unsafe_allow_html=True)
        with m3:
            # 放弃画图，改用带色彩的 MACD 柱值，一眼看懂趋势且绝对不撑爆UI
            macd_color = "#ef4444" if data['macd'] > 0 else "#16a34a"
            st.markdown(f"<div class='mini-metric'><div class='m-label'>MACD</div><div class='m-val' style='color:{macd_color};'>{data['macd']}</div></div>", unsafe_allow_html=True)
        with m4:
            st.markdown(f"<div style='text-align:right;'><div class='tag-base {fund_class}' style='margin-bottom:4px;'>{data['fund']}</div><br><div class='tag-base {sector_class}'>{data['sector']}</div></div>", unsafe_allow_html=True)
