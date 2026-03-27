import streamlit as st
import requests

st.set_page_config(page_title="鹰眼作战终端", layout="wide")

if 'pool' not in st.session_state:
    st.session_state.pool = ["sz002428"] # 默认保留云南锗业

st.markdown("""
    <style>
    .stApp { background-color: #f4f7f6; }
    .index-bar { background: white; padding: 15px; border-radius: 10px; margin-bottom: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
    .stock-card { background: white; border-radius: 12px; padding: 20px; box-shadow: 0 4px 10px rgba(0,0,0,0.08); margin-bottom: 20px; border-top: 5px solid; }
    .price-large { font-size: 34px; font-weight: bold; line-height: 1.1; }
    .score-badge { font-size: 20px; font-weight: bold; padding: 5px 15px; border-radius: 20px; color: white; }
    .data-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 15px; text-align: center; margin-top: 20px; padding-top: 15px; border-top: 1px dashed #eee; }
    .data-item { display: flex; flex-direction: column; background: #fafafa; padding: 10px; border-radius: 8px; }
    .data-val { font-size: 18px; font-weight: bold; }
    .data-label { font-size: 12px; color: #888; margin-top: 3px; }
    </style>
    """, unsafe_allow_html=True)

# --- 抓取更多高密度数据 ---
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
            if len(v) < 48: continue # 确保获取到足够多的字段
            results.append({
                "name": v[1], "code": v[2], "price": float(v[3]),
                "last_close": float(v[4]), "open": float(v[5]),
                "change": float(v[32]), "high": float(v[33]), "low": float(v[34]),
                "volume": float(v[37]), "turnover": float(v[38]),
                "amplitude": float(v[43]), "limit_up": float(v[47]) # 新增：振幅 和 涨停价
            })
        return results
    except: return []

# --- 鹰眼评分与反人性推演逻辑 ---
def analyze_logic(s):
    # 1. 基础指标计算
    premium = round((s['open'] - s['last_close']) / s['last_close'] * 100, 2) if s['last_close'] > 0 else 0
    # 盘中实体 (当前价对比开盘价的涨跌，判断主力是买是卖)
    intraday_body = round((s['price'] - s['open']) / s['open'] * 100, 2) if s['open'] > 0 else 0
    range_val = (s['high'] - s['low'])
    wr = round((s['high'] - s['price']) / range_val * 100, 2) if range_val != 0 else 50

    # 2. 鹰眼评分 & 反向博弈逻辑
    score = 60
    advice = "中性震荡，观望为主"
    card_color = "#ccc"

    if premium > 3 and intraday_body < -2:
        score -= 20
        advice = "⚠️ 高开低走！主力诱多出货，切勿追高"
        card_color = "#00a800"
    elif premium < 0 and intraday_body > 2:
        score += 25
        advice = "🔥 低开高走！资金逆势承接，反核博弈点出现"
        card_color = "#f21b2b"
    elif premium > 0 and intraday_body > 0:
        score += 15
        advice = "📈 稳步推升，趋势健康，可持有或逢低上车"
        card_color = "#f21b2b"
    elif premium < 0 and intraday_body < 0:
        score -= 15
        advice = "🧊 彻底弱势，毫无承接，坚决规避"
        card_color = "#00a800"

    # W&R 极限位置加减分
    if wr > 85: 
        score += 10; advice += " (极度超跌，留意反抽)"
    if wr < 15: 
        score -= 10; advice += " (极度超买，随时回调)"

    # 评分边界修正
    score = max(0, min(100, score))
    
    # 分数颜色
    if score >= 80: badge_bg = "#f21b2b" # 红
    elif score <= 40: badge_bg = "#00a800" # 绿
    else: badge_bg = "#ff9800" # 橙

    # 3. W&R 视觉处理
    wr_display = f"<span style='color:#00a800'>{wr} 🟢 买点</span>" if wr >= 50 else f"<span style='color:#f21b2b'>{wr} 🔴 卖点</span>"
    
    # 实体视觉处理 (K线红绿)
    ib_color = "#f21b2b" if intraday_body >= 0 else "#00a800"
    ib_display = f"<span style='color:{ib_color}'>{'+' if intraday_body>0 else ''}{intraday_body}%</span>"

    main_color = "#f21b2b" if s['change'] >= 0 else "#00a800"
    
    return score, badge_bg, advice, card_color, premium, ib_display, wr_display, main_color

# --- 主界面布局 ---
c1, c2 = st.columns([4, 1])
with c1:
    new_stock = st.text_input("", placeholder="🔍 输入代码直接挂载 (如 002428)", label_visibility="collapsed")
with c2:
    if st.button("🚀 实时挂载", use_container_width=True):
        if new_stock:
            c = new_stock.strip()
            if len(c) == 6 and c.isdigit(): c = f"sh{c}" if c.startswith(('6', '9')) else f"sz{c}"
            st.session_state.pool.insert(0, c)
            st.session_state.pool = list(dict.fromkeys(st.session_state.pool))
            st.rerun()

data = get_data(st.session_state.pool)
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

    st.markdown("---")
    st.subheader("📋 实时狙击卡牌")

    for s in stocks_data:
        score, badge_bg, advice, card_color, premium, ib_display, wr_display, main_color = analyze_logic(s)
        
        st.markdown(f"""
            <div class="stock-card" style="border-top-color:{card_color}">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div>
                        <span style="font-size:24px; font-weight:bold; color:#333;">{s['name']}</span> 
                        <span style="color:#999; font-size:14px; margin-left:5px;">{s['code']}</span>
                        <div style="margin-top:10px;">
                            <span class="score-badge" style="background-color:{badge_bg};">🦅 评分: {score}</span>
                            <span style="margin-left:15px; font-size:15px; font-weight:bold; color:#555;">💡 {advice}</span>
                        </div>
                    </div>
                    <div style="text-align:right;">
                        <div class="price-large" style="color:{main_color};">{s['price']}</div>
                        <div style="color:{main_color}; font-weight:bold; font-size:18px;">{'+' if s['change']>0 else ''}{s['change']}%</div>
                    </div>
                </div>
                
                <div class="data-grid">
                    <div class="data-item">
                        <div class="data-val" style="color:#333;">{premium}%</div>
                        <div class="data-label">开盘溢价率 (盘前)</div>
                    </div>
                    <div class="data-item">
                        <div class="data-val">{ib_display}</div>
                        <div class="data-label">盘中实体涨跌 (博弈)</div>
                    </div>
                    <div class="data-item">
                        <div class="data-val">{wr_display}</div>
                        <div class="data-label">日内 W&R (0-100)</div>
                    </div>
                    <div class="data-item">
                        <div class="data-val" style="color:#333;">{s['amplitude']}%</div>
                        <div class="data-label">今日振幅 (活跃度)</div>
                    </div>
                    <div class="data-item">
                        <div class="data-val" style="color:#f21b2b;">{s['limit_up']}</div>
                        <div class="data-label">涨停目标价</div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

else:
    st.info("监控池为空。请在上方输入代码挂载实战卡牌。")

if st.button("🔄 同步刷新行情"):
    st.rerun()
