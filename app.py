import streamlit as st
import requests
import pandas as pd
from streamlit_autorefresh import st_autorefresh

# ===================== 全局配置 =====================
st.set_page_config(page_title="鹰眼自选终端", layout="wide", initial_sidebar_state="collapsed")
st_autorefresh(interval=8000, limit=None, key="eagle_eye_v5")

if 'stock_pool' not in st.session_state:
    st.session_state.stock_pool = ["sz001896", "sz002364", "sh600111", "sz002428"]

HOT_SECTORS = ["AI", "芯片", "半导体", "算力", "CPO", "机器人", "新能源", "光伏", "储能", "军工", "医药", "稀土", "有色", "电力"]
STOCK_PY_MAP = {
    "bfxt":"sh600111", "ynzy":"sz002428", "zhdq":"sz002364", "ynkg":"sz001896"
}

# ===================== UI 样式锁死 =====================
st.markdown("""
<style>
    .stApp { background: #f0f2f5; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
    #MainMenu, header, footer { display: none !important; }
    .block-container { padding-top: 1rem !important; padding-bottom: 1rem !important; max-width: 800px; }
    
    /* 极致压缩间距 */
    [data-testid="stVerticalBlock"] { gap: 0.4rem !important; }
    
    /* 隐藏原生按钮边框，伪装成 X 图标 */
    .stButton > button {
        background: transparent; border: none; color: #94a3b8; font-size: 16px; padding: 0; height: auto; margin-top: 5px;
    }
    .stButton > button:hover { color: #ef4444; }

    /* 信号徽章样式 */
    .badge { padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: 600; display: inline-block; margin-right: 4px; border: 1px solid transparent; }
    .b-cross { background: #fee2e2; color: #ef4444; border-color: #fca5a5; } /* 水下金叉 */
    .b-sector { background: #e0f2fe; color: #0284c7; } /* 板块 */
    .b-fund { background: #f3f4f6; color: #475569; } /* 资金 */
</style>
""", unsafe_allow_html=True)

# ===================== 顶部搜索栏 =====================
col1, col2 = st.columns([0.85, 0.15])
with col1:
    search_input = st.text_input("", placeholder="🔍 输入代码/首字母快速添加", label_visibility="collapsed")
with col2:
    if st.button("清空"): st.session_state.stock_pool = []; st.rerun()

if search_input:
    search = search_input.strip().lower()
    code = "sh"+search if search.isdigit() and search.startswith(('6','9')) else "sz"+search if search.isdigit() else STOCK_PY_MAP.get(search)
    if code and code not in st.session_state.stock_pool:
        st.session_state.stock_pool.insert(0, code); st.rerun()

# ===================== 核心算法引擎 =====================
def get_macd_svg(macd_list):
    """手绘微型 SVG MACD 柱状图 (绝对不破坏排版)"""
    if not macd_list: return ""
    w, h = 60, 22
    mid_y = h / 2
    max_m = max([abs(m) for m in macd_list] + [0.01])
    
    svg = f"<svg width='{w}' height='{h}' style='display:block; margin-top: 2px;'>"
    svg += f"<line x1='0' y1='{mid_y}' x2='{w}' y2='{mid_y}' stroke='#cbd5e1' stroke-width='0.5'/>"
    
    bar_w = w / len(macd_list)
    for i, m in enumerate(macd_list):
        bar_h = (abs(m) / max_m) * (mid_y - 1)
        x = i * bar_w + 1
        color = "#ef4444" if m > 0 else "#10b981" # A股红绿
        y = mid_y - bar_h if m > 0 else mid_y
        svg += f"<rect x='{x}' y='{y}' width='{bar_w-1.5}' height='{bar_h}' fill='{color}' rx='1'/>"
    svg += "</svg>"
    return svg

@st.cache_data(ttl=5, show_spinner=False)
def get_data(full_code):
    try:
        # 1. 实时基础数据
        res = requests.get(f"https://qt.gtimg.cn/q={full_code}", timeout=1)
        arr = res.text.split("~")
        name, price, change = arr[1], float(arr[3]), float(arr[32] or 0)
        
        # 2. 获取近20日K线计算指标
        kres = requests.get(f"https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={full_code},day,,,20,qfq", timeout=1)
        close_prices = [float(x[2]) for x in kres.json()['data'][full_code]['qfqday']]
        
        ma5, ma10 = round(sum(close_prices[-5:])/5, 2), round(sum(close_prices[-10:])/10, 2)

        # 简易 MACD 计算
        e12, e26 = [close_prices[0]], [close_prices[0]]
        for p in close_prices[1:]:
            e12.append((2*p + 11*e12[-1])/13)
            e26.append((2*p + 25*e26[-1])/27)
        dif = [e12[i] - e26[i] for i in range(len(e12))]
        dea = [dif[0]]
        for d in dif[1:]: dea.append((2*d + 8*dea[-1])/10)
        macd = [(dif[i] - dea[i])*2 for i in range(len(dif))]

        # 3. 智能信号判定：水下金叉 (DIF<0, DEA<0, DIF上穿DEA)
        is_water_cross = (dif[-1] < 0 and dea[-1] < 0 and dif[-1] > dea[-1] and dif[-2] <= dea[-2])

        sector_map = {"001896":"电力", "002364":"电力设备", "600111":"稀土永磁", "002428":"小金属"}
        return {
            "code": full_code[2:], "name": name, "price": price, "change": change,
            "ma5": ma5, "ma10": ma10, "macd_list": macd[-12:], # 取近12天画图
            "is_water_cross": is_water_cross,
            "sector": sector_map.get(full_code[2:], "热门题材")
        }
    except:
        return None

# ===================== 两行卡牌渲染 =====================
for full_code in st.session_state.stock_pool:
    data = get_data(full_code)
    if not data: continue

    c_hex = "#ef4444" if data['change'] >= 0 else "#10b981"
    
    with st.container(border=True):
        # 第一行：身份与报价 (占比: 左50%, 中40%, 右10%)
        r1_left, r1_mid, r1_right = st.columns([0.5, 0.4, 0.1])
        with r1_left:
            st.markdown(f"<div style='line-height:1.2; margin-top:2px;'><span style='font-size:16px; font-weight:bold;'>{data['name']}</span> <span style='font-size:12px; color:#94a3b8;'>{data['code']}</span></div>", unsafe_allow_html=True)
        with r1_mid:
            st.markdown(f"<div style='text-align:right; line-height:1.2;'><span style='font-size:18px; font-weight:bold; color:{c_hex};'>{data['price']:.2f}</span> <span style='font-size:12px; padding:1px 4px; background:{c_hex}15; color:{c_hex}; border-radius:4px;'>{data['change']}%</span></div>", unsafe_allow_html=True)
        with r1_right:
            if st.button("✕", key=f"del_{full_code}"):
                st.session_state.stock_pool.remove(full_code); st.rerun()

        # 第二行：均线、微型图与智能标签 (占比: 左40%, 中20%, 右40%)
        r2_left, r2_mid, r2_right = st.columns([0.4, 0.2, 0.4])
        with r2_left:
            # 极简均线
            st.markdown(f"<div style='font-size:11px; color:#64748b; margin-top:4px;'>MA5: {data['ma5']} | MA10: {data['ma10']}</div>", unsafe_allow_html=True)
        with r2_mid:
            # 渲染 Python 手绘的微型 SVG MACD 图
            st.markdown(get_macd_svg(data['macd_list']), unsafe_allow_html=True)
        with r2_right:
            # 标签渲染逻辑
            tags_html = f"<div style='text-align:right; margin-top:4px;'>"
            if data['is_water_cross']:
                tags_html += f"<span class='badge b-cross'>⚡水下金叉</span>"
            tags_html += f"<span class='badge b-sector'>{data['sector']}</span>"
            tags_html += f"</div>"
            st.markdown(tags_html, unsafe_allow_html=True)
