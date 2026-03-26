import streamlit as st
import requests

# 1. 页面极简专业配置
st.set_page_config(page_title="鹰眼作战终端", layout="wide")

# 2. 注入 CSS：打造紧凑、重点突出的“实战卡牌”视觉
st.markdown("""
    <style>
    .stApp { background-color: #f4f7f6; }
    .index-bar { background: white; padding: 15px; border-radius: 10px; margin-bottom: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
    .stock-card { 
        background: white; border-radius: 12px; padding: 15px 20px; 
        box-shadow: 0 4px 10px rgba(0,0,0,0.08); margin-bottom: 20px;
    }
    .price-large { font-size: 32px; font-weight: bold; line-height: 1.1; }
    .premium-bar { padding: 8px 12px; border-radius: 6px; margin: 10px 0; font-size: 14px; font-weight: bold; border-left: 5px solid; }
    .data-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; text-align: center; margin-top: 15px; padding-top: 15px; border-top: 1px dashed #eee; }
    .data-item { display: flex; flex-direction: column; }
    .data-val { font-size: 18px; font-weight: bold; }
    .data-label { font-size: 12px; color: #888; }
    </style>
    """, unsafe_allow_html=True)

# --- 数据抓取核心 ---
def get_data(codes):
    if not codes: return []
    fixed = ["sh000001", "sz399001", "sh510100"] 
    all_codes = list(dict.fromkeys(fixed + codes))
    url = f"http://qt.gtimg.cn/q={','.join(all_codes)}"
    try:
        res = requests.get(url, timeout=2)
        res.encoding = 'gbk'
        results = []
        for line in res.text.strip().split(';'):
            if '="' not in line: continue
            v = line.split('=')[1].strip('"').split('~')
            if len(v) < 40: continue
            results.append({
                "name": v[1], "code": v[2], "price": float(v[3]),
                "last_close": float(v[4]), "open": float(v[5]),
                "change": float(v[32]), "high": float(v[33]), "low": float(v[34]),
                "volume": float(v[37]), "turnover": float(v[38])
            })
        return results
    except: return []

# --- 核心逻辑推演 ---
def analyze_logic(s):
    # 1. 开盘溢价率计算 (当天开盘价 - 昨天收盘价) ÷ 昨天收盘价 × 100%
    if s['last_close'] > 0:
        premium = round((s['open'] - s['last_close']) / s['last_close'] * 100, 2)
    else: premium = 0
    
    # 溢价率逻辑判定
    if premium > 5:
        p_color, p_bg, p_text, p_advice = "#f21b2b", "#fff0f0", f"溢价 {premium}% | 主力抢筹", "开盘不破-3%大概率冲高连板"
    elif premium >= 3:
        p_color, p_bg, p_text, p_advice = "#ff9800", "#fff8e1", f"溢价 {premium}% | 健康走势", "盘中冲高>7%建议减半落袋"
    elif premium >= 0:
        p_color, p_bg, p_text, p_advice = "#607d8b", "#eceff1", f"溢价 {premium}% | 弱势信号", "半小时内不放量上攻直接走人"
    else:
        p_color, p_bg, p_text, p_advice = "#00a800", "#e8f5e9", f"溢价 {premium}% | 主力出货", "开盘就跑，谨防被套！"

    # 2. 模拟日内 W&R
    range_val = (s['high'] - s['low'])
    wr = round((s['high'] - s['price']) / range_val * 100, 2) if range_val != 0 else 50
    
    if wr >= 50:
        wr_display = f"<span style='color:#00a800'>{wr} 🟢↓ 逢高卖出</span>"
    else:
        wr_display = f"<span style='color:#f21b2b'>{wr} 🔴↑ 逢低买入</span>"

    # 3. 主颜色
    main_color = "#f21b2b" if s['change'] >= 0 else "#00a800"
    
    return premium, p_color, p_bg, p_text, p_advice, wr_display, main_color

# --- 主界面布局 ---

st.title("🦅 鹰眼作战终端")
c1, c2 = st.columns([4, 1])
with c1:
    new_stock = st.text_input("", placeholder="🔍 输入代码直接挂载 (如 002428)", label_visibility="collapsed")
with c2:
    if st.button("🚀 实时挂载", use_container_width=True):
        if 'pool' not in st.session_state: st.session_state.pool = []
        if new_stock:
            c = new_stock.strip()
            if len(c) == 6 and c.isdigit(): c = f"sh{c}" if c.startswith(('6', '9')) else f"sz{c}"
            st.session_state.pool.insert(0, c)
            st.session_state.pool = list(dict.fromkeys(st.session_state.pool))
            st.rerun()

data = get_data(st.session_state.get('pool', []))
if data:
    idx_data, stocks_data = data[:3], data[3:]
    
    # 顶部指数
    cols = st.columns(3)
    idx_names = ["上证指数", "深证成指", "富时A50"]
    for i, s in enumerate(idx_data):
        with cols[i]:
            c_color = "#f21b2b" if s['change'] >= 0 else "#00a800"
            st.markdown(f"""
                <div class="index-bar">
                    <div style="color:#666; font-size:14px;">{idx_names[i]}</div>
                    <div style="color:{c_color}; font-size:22px; font-weight:bold;">{s['price']} <small>{s['change']}%</small></div>
                </div>
            """, unsafe_allow_html=True)

    st.markdown("##### 💹 资金博弈热力云图")
    hot_cols = st.columns(6)
    sectors = [("半导体", 2.5), ("低空经济", -1.2), ("有色金属", 3.8), ("白酒", -0.5), ("医药", 1.1), ("电力", -2.1)]
    for i, (name, val) in enumerate(sectors):
        bg, tc = ("#ffebee", "#f44336") if val > 0 else ("#e8f5e9", "#4caf50")
        hot_cols[i].markdown(f"<div style='background:{bg}; color:{tc}; padding:8px; border-radius:5px; text-align:center; font-size:13px;'>{name}<br><b>{val}%</b></div>", unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("📋 实时狙击卡牌")

    # 股票卡牌遍历
    for s in stocks_data:
        premium, p_color, p_bg, p_text, p_advice, wr_display, main_color = analyze_logic(s)
        
        st.markdown(f"""
            <div class="stock-card">
                <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                    <div>
                        <span style="font-size:22px; font-weight:bold; color:#333;">{s['name']}</span> 
                        <span style="color:#999; font-size:14px; margin-left:5px;">{s['code']}</span>
                    </div>
                    <div style="text-align:right;">
                        <div class="price-large" style="color:{main_color};">{s['price']}</div>
                        <div style="color:{main_color}; font-weight:bold;">{'+' if s['change']>0 else ''}{s['change']}%</div>
                    </div>
                </div>
                
                <div class="premium-bar" style="background-color:{p_bg}; border-left-color:{p_color}; color:{p_color};">
                    <div>🎯 {p_text}</div>
                    <div style="font-size:12px; margin-top:3px; font-weight:normal; color:#555;">💡 战法纪律：{p_advice}</div>
                </div>
                
                <div class="data-grid">
                    <div class="data-item">
                        <div class="data-val">{wr_display}</div>
                        <div class="data-label">日内 W&R 指标</div>
                    </div>
                    <div class="data-item">
                        <div class="data-val" style="color:#333;">{s['turnover']}%</div>
                        <div class="data-label">实时换手率</div>
                    </div>
                    <div class="data-item">
                        <div class="data-val" style="color:#333;">{s['open']}</div>
                        <div class="data-label">今日开盘价</div>
                    </div>
                    <div class="data-item">
                        <div class="data-val" style="color:#333;">{s['last_close']}</div>
                        <div class="data-label">昨日收盘价</div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

else:
    st.info("监控池为空。请在上方输入代码（如 002428）挂载实战卡牌。")

if st.button("🔄 同步刷新行情"):
    st.rerun()
