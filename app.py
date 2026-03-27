import streamlit as st
import requests

st.set_page_config(page_title="鹰眼作战终端", layout="wide")

# 初始化监控池
if 'pool' not in st.session_state:
    st.session_state.pool = ["sz002428"]
# 初始化页面状态
if 'page' not in st.session_state:
    st.session_state.page = "home"
if 'current_target' not in st.session_state:
    st.session_state.current_target = None

st.markdown("""
    <style>
    .stApp { background-color: #f8fafc; }
    .stock-card { background: white; border-radius: 12px; padding: 18px; border-left: 8px solid; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    .score-badge { font-size: 18px; font-weight: bold; padding: 5px 15px; border-radius: 20px; color: white; display: inline-block; margin-bottom: 10px; }
    .data-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; background: #f1f5f9; padding: 15px; border-radius: 10px; margin: 15px 0; }
    .data-item { text-align: center; }
    .data-val { font-size: 18px; font-weight: bold; color: #1e293b; }
    .data-label { font-size: 12px; color: #64748b; }
    .logic-box { background: #fffcf0; border: 1px solid #ffecb3; padding: 12px; border-radius: 8px; margin-top: 10px; font-size: 14px; line-height: 1.5; }
    </style>
    """, unsafe_allow_html=True)

def get_data(codes):
    if not codes: return []
    url = f"http://qt.gtimg.cn/q={','.join(codes)}"
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
                "volume": float(v[37]), "turnover": float(v[38]),
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
        score = 40; advice = "⚠️ 高开低走（诱多）"; detail = "主力开盘拉高吸引跟风后反手派发，实体走弱，警惕风险。"
    elif premium < -1 and ib > 1.5:
        score = 90; advice = "🔥 低开高走（承接）"; detail = "恐慌盘充分释放，抄底资金进场明显，具备反核弹性。"
    elif ib > 2:
        score = 85; advice = "📈 强力突破"; detail = "盘中扫货积极，突破分时压力位，趋势加速中。"

    badge_bg = "#f21b2b" if score >= 80 else ("#00a800" if score <= 40 else "#ff9800")
    main_color = "#f21b2b" if s['change'] >= 0 else "#00a800"
    return score, badge_bg, advice, detail, premium, ib, wr, main_color

# --- 页面切换逻辑 ---
if st.session_state.page == "home":
    st.title("🦅 鹰眼·监控池")
    
    # 顶部挂载
    new_stock = st.text_input("", placeholder="🔍 输入代码挂载 (如 002428)", label_visibility="collapsed")
    if new_stock:
        c = new_stock.strip()
        if len(c) == 6: c = f"sh{c}" if c.startswith(('6', '9')) else f"sz{c}"
        if c not in st.session_state.pool:
            st.session_state.pool.insert(0, c)
            st.rerun()

    stocks = get_data(st.session_state.pool)
    for s in stocks:
        score, badge_bg, advice, detail, premium, ib, wr, m_color = analyze_logic(s)
        
        # 首页卡牌全平铺展示
        st.markdown(f"""
            <div class="stock-card" style="border-left-color:{badge_bg}">
                <div style="display:flex; justify-content:space-between; align-items:start;">
                    <div>
                        <div class="score-badge" style="background:{badge_bg}">综合评分: {score}</div>
                        <div style="font-size:20px; font-weight:bold;">{s['name']} <small style="color:#94a3b8;">{s['code']}</small></div>
                    </div>
                    <div style="text-align:right;">
                        <div style="font-size:24px; font-weight:bold; color:{m_color}">{s['price']}</div>
                        <div style="font-weight:bold; color:{m_color}">{s['change']}%</div>
                    </div>
                </div>
                <div class="data-grid">
                    <div class="data-item"><div class="data-val">{premium}%</div><div class="data-label">开盘溢价</div></div>
                    <div class="data-item"><div class="data-val" style="color:{m_color}">{ib}%</div><div class="data-label">盘中实体</div></div>
                    <div class="data-item"><div class="data-val">{wr}</div><div class="data-label">W&R</div></div>
                </div>
                <div class="logic-box">
                    <b>🎯 核心建议：</b>{advice}<br>
                    <b>💡 逻辑推演：</b>{detail}
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # 跳转按钮
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button(f"🔎 深度多维分析", key=f"det_{s['code']}", use_container_width=True):
                st.session_state.current_target = s
                st.session_state.page = "detail"
                st.rerun()
        with col_btn2:
            if st.button(f"🗑️ 移出", key=f"del_{s['code']}", use_container_width=True):
                st.session_state.pool.remove(s['code'])
                st.rerun()

# --- 深度分析页面 ---
elif st.session_state.page == "detail":
    s = st.session_state.current_target
    if st.button("⬅️ 返回监控池"):
        st.session_state.page = "home"
        st.rerun()
    
    st.header(f"📊 {s['name']} ({s['code']}) 多维度深度分析")
    
    # 这里可以根据你的“思维跳跃”随意增加维度
    t1, t2, t3 = st.tabs(["核心筹码", "反人性博弈", "量价异动"])
    
    with t1:
        st.subheader("📍 筹码分布推演")
        st.write("此处接入该标的的筹码集中度分析...")
        st.metric("今日涨停目标", s['limit_up'])
        
    with t2:
        st.subheader("🧠 主力反人性逻辑报告")
        score, _, advice, detail, _, _, _, _ = analyze_logic(s)
        st.error(f"当前鹰眼评级：{score}分")
        st.info(f"博弈核心点：{detail}")
        st.write("历史同类形态胜率：72.5% (模拟数据)")
        
    with t3:
        st.subheader("⚡ 实时异动监控")
        st.write(f"今日振幅：{s['amplitude']}%")
        st.write(f"当前成交额：{round(s['turnover']/10000, 2)} 万")

    st.button("🔄 刷新此标的深度数据", on_click=st.rerun)
