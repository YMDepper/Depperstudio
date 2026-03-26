import streamlit as st
import requests

# 1. 页面极简配置
st.set_page_config(page_title="行情监控", layout="wide")

# 2. 注入 CSS：复刻截图中的黑白灰高对比色
st.markdown("""
    <style>
    .stApp { background-color: white; }
    .index-card { text-align: center; padding: 5px; border-radius: 5px; border: 1px solid #f0f0f0; }
    .price-up { color: #f21b2b; font-weight: bold; font-size: 20px; }
    .price-down { color: #00a800; font-weight: bold; font-size: 20px; }
    .label-gray { color: #666; font-size: 14px; }
    .stock-row { border-bottom: 1px solid #f8f8f8; padding: 10px 0; }
    [data-testid="column"] { padding: 0 5px !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 核心逻辑：代码自动识别 ---
def format_code(c):
    c = c.strip()
    if len(c) == 6 and c.isdigit():
        if c.startswith(('6', '9')): return f"sh{c}"
        else: return f"sz{c}"
    return c

def get_data(codes):
    if not codes: return []
    url = f"http://qt.gtimg.cn/q={','.join(codes)}"
    try:
        res = requests.get(url, timeout=2)
        res.encoding = 'gbk'
        results = []
        for line in res.text.strip().split(';'):
            if '="' not in line: continue
            info = line.split('=')[1].strip('"').split('~')
            if len(info) > 38:
                results.append({
                    "name": info[1],
                    "price": float(info[3]),
                    "change": float(info[32]),
                    "amount": f"{round(float(info[37])/10000, 1)}亿" if float(info[37]) > 10000 else f"{info[37]}万",
                    "code": info[2]
                })
        return results
    except: return []

# --- 状态管理：自选股记忆 ---
if 'watch_list' not in st.session_state:
    # 默认放几个你关注的，可以随时清空
    st.session_state.watch_list = ["sh600930", "sh600584", "sh600219", "sz000878"]

# --- 侧边栏：搜索添加 ---
with st.sidebar:
    st.subheader("🔍 添加股票")
    input_code = st.text_input("输入代码 (如 002428)", placeholder="输入后点添加...")
    if st.button("➕ 添加到自选"):
        if input_code:
            formatted = format_code(input_code)
            st.session_state.watch_list.insert(0, formatted) # 新加的在最上面
            st.session_state.watch_list = list(dict.fromkeys(st.session_state.watch_list))
            st.rerun()
    
    if st.button("🗑️ 清空所有列表"):
        st.session_state.watch_list = []
        st.rerun()

# --- 主界面开始 ---

# 1. 顶部指数区 (上证, 深证, A50)
indices = get_data(["sh000001", "sz399001", "sh510100"]) # A50用510100ETF代替行情或直接找期货接口
idx_names = ["上证指数", "深证成指", "富时A50"]

if len(indices) >= 3:
    idx_cols = st.columns(3)
    for i, s in enumerate(indices):
        with idx_cols[i]:
            color = "price-up" if s['change'] >= 0 else "price-down"
            st.markdown(f"""
                <div class="index-card">
                    <div class="label-gray">{idx_names[i]}</div>
                    <div class="{color}">{s['price']}</div>
                    <div class="{color}" style="font-size:14px;">{s['change']}%</div>
                </div>
            """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# 2. 自选股表头
h1, h2, h3, h4 = st.columns([2, 1.2, 1.2, 1.5])
h1.markdown("<span class='label-gray'>名称</span>", unsafe_allow_html=True)
h2.markdown("<span class='label-gray'>最新</span>", unsafe_allow_html=True)
h3.markdown("<span class='label-gray'>涨幅</span>", unsafe_allow_html=True)
h4.markdown("<span class='label-gray'>成交额</span>", unsafe_allow_html=True)

# 3. 自选股列表
stocks_data = get_data(st.session_state.watch_list)
for s in stocks_data:
    c1, c2, c3, c4 = st.columns([2, 1.2, 1.2, 1.5])
    color = "price-up" if s['change'] >= 0 else "price-down"
    
    c1.markdown(f"**{s['name']}**<br><small style='color:#999'>{s['code']}</small>", unsafe_allow_html=True)
    c2.markdown(f"<div class='{color}' style='padding-top:10px'>{s['price']}</div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='{color}' style='padding-top:10px'>{'+' if s['change']>0 else ''}{s['change']}%</div>", unsafe_allow_html=True)
    c4.markdown(f"<div style='padding-top:10px'>{s['amount']}</div>", unsafe_allow_html=True)
    st.markdown("<div class='stock-row'></div>", unsafe_allow_html=True)

# 自动刷新按钮（放底部不挡路）
if st.button("🔄 刷新行情"):
    st.rerun()
