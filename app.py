import streamlit as st
import requests
from streamlit_autorefresh import st_autorefresh # 导入自动刷新组件

st.set_page_config(page_title="鹰眼作战终端", layout="wide")

# --- 核心配置：每 5 秒自动刷新全站数据 ---
# limit 是刷新次数限制，设为 None 表示无限次，直到关闭网页
count = st_autorefresh(interval=5000, limit=None, key="flicker")

if 'pool' not in st.session_state:
    st.session_state.pool = ["sz002428"]
if 'page' not in st.session_state:
    st.session_state.page = "home"
if 'current_target' not in st.session_state:
    st.session_state.current_target = None

st.markdown("""
    <style>
    .stApp { background-color: #f8fafc; }
    .refresh-tag { color: #94a3b8; font-size: 12px; text-align: right; margin-bottom: 10px; }
    .stock-card { background: white; border-radius: 12px; padding: 18px; border-left: 8px solid; margin-bottom: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    .score-badge { font-size: 18px; font-weight: bold; padding: 5px 15px; border-radius: 20px; color: white; display: inline-block; margin-bottom: 10px; }
    .data-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; background: #f1f5f9; padding: 15px; border-radius: 10px; margin: 15px 0; }
    .data-item { text-align: center; }
    .data-val { font-size: 18px; font-weight: bold; color: #1e293b; }
    .data-label { font-size: 11px; color: #64748b; }
    .logic-box { background: #fffcf0; border: 1px solid #ffecb3; padding: 12px; border-radius: 8px; margin-top: 5px; font-size: 14px; }
    </style>
    """, unsafe_allow_html=True)

def get_data(codes):
    if not codes: return []
    # 增加随机参数防止 API 缓存
    import time
    url = f"http://qt.gtimg.cn/q={','.join(codes)}&_t={int(time.time())}"
    try:
        res = requests.get(url, timeout=2)
        res.encoding = 'gbk'
        results = []
        for line in res.text.strip().split(';'):
            if '="' not in line: continue
            v = line.split('=')[1].strip('"').split('~')
            if len(v) < 48: continue
            results.append({
                "name": v[1], "code": v[2], "price": float(v[3]),
                "last_close": float(v[4]), "open": float(v[5]),
                "change": float(v[32]), "high": float(v[33]), "low": float(v[34]),
                "amplitude": float(v[43]), "limit_up": float(v[47]) 
            })
        return results
    except: return []

def analyze_logic(s):
    premium = round((s['open'] - s['last_close']) / s['last_close'] * 100, 2)
    ib = round((s['price'] - s['open']) / s['open'] * 100, 2) if s['open'] > 0 else 0
    wr = round((s['high'] - s['price']) / (s['high'] - s['low']) * 100, 2) if s['high']!=s['low'] else 50
    
    score = 60
    advice = "区间震荡"
    detail = "盘中力量均衡，建议观察关键位突破。"
    if premium > 2 and ib < -1.5:
        score = 40; advice = "⚠️ 高开低走（诱多）"; detail = "主力拉高派发，实体走弱，警惕风险。"
    elif premium < -1 and ib > 1.5:
        score = 90; advice = "🔥 低开高走（承接）"; detail = "反核博弈点，低位买盘积极。"
    elif ib > 2:
        score = 85; advice = "📈 强力突破"; detail = "扫货积极，突破分时压力位。"

    badge_bg = "#f21b2b" if score >= 80 else ("#00a800" if score <= 40 else "#ff9800")
    main_color = "#f21b2b" if s['change'] >= 0 else "#00a800"
    return score, badge_bg, advice, detail, premium, ib, wr, main_color

# --- 页面逻辑 ---
st.markdown(f'<div class="refresh-tag">📡 鹰眼系统运行中 | 自动刷新计数: {count}</div>', unsafe_allow_html=True)

if st.session_state.page == "home":
    st.title("🦅 鹰眼·实时战术板")
    
    new_stock = st.text_input("", placeholder="🔍 输入代码挂载 (如 002428)", label_visibility="collapsed")
    if new_stock:
        c = new_stock.strip()
        if len(c) == 6: c = f"sh{c}" if c.startswith(('6', '9')) else f"sz{c}"
        if c not in st.session_state.pool:
            st.session_state.pool.insert(0, c); st.rerun()

    stocks = get_data(st.session_state.pool)
    for s in stocks:
        score, badge_bg, advice, detail, prem, ib, wr, m_color = analyze_logic(s)
        
        # 首页直接全展示
        st.markdown(f"""
            <div class="stock-card" style="border-left-color:{badge_bg}">
                <div style="display:flex; justify-content:space-between;">
                    <div>
                        <div class="score-badge" style="background:{badge_bg}">鹰眼评分: {score}</div>
                        <div style="font-size:20px; font-weight:bold;">{s['name']} <small>{s['code']}</small></div>
                    </div>
                    <div style="text-align:right;">
                        <div style="font-size:26px; font-weight:bold; color:{m_color}">{s['price']}</div>
                        <div style="font-weight:bold; color:{m_color}">{s['change']}%</div>
                    </div>
                </div>
                <div class="data-grid">
                    <div class="data-item"><div class="data-val">{prem}%</div><div class="data-label">开盘溢价</div></div>
                    <div class="data-item"><div class="data-val" style="color:{m_color}">{ib}%</div><div class="data-label">盘中实体</div></div>
                    <div class="data-item"><div class="data-val">{wr}</div><div class="data-label">W&R指标</div></div>
                </div>
                <div class="logic-box">
                    <b>🎯 诊断：</b>{advice}<br><b>💡 推演：</b>{detail}
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        c1, c2 = st.columns(2)
        with c1:
            if st.button(f"🔎 深度分析 {s['name']}", key=f"det_{s['code']}", use_container_width=True):
                st.session_state.current_target = s; st.session_state.page = "detail"; st.rerun()
        with c2:
            if st.button(f"🗑️ 移除", key=f"del_{s['code']}", use_container_width=True):
                st.session_state.pool.remove(s['code']); st.rerun()

elif st.session_state.page == "detail":
    s = st.session_state.current_target
    if st.button("⬅️ 返回列表"):
        st.session_state.page = "home"; st.rerun()
    
    st.header(f"📊 {s['name']} ({s['code']}) 深度诊断报告")
    st.write("---")
    # 自动刷新在详情页也生效，保证分析数据也是最新的
    st.metric("实时价", s['price'], f"{s['change']}%")
    st.info(f"此处后续可接入【{s['name']}】的筹码、量能、分时等多维度分析逻辑...")
