import streamlit as st
import requests

st.set_page_config(page_title="鹰眼作战终端", layout="wide")

if 'pool' not in st.session_state:
    st.session_state.pool = ["sz002428", "sh600519", "sz000001"] # 预设几个标的

st.markdown("""
    <style>
    .stApp { background-color: #f8fafc; }
    .index-bar { background: white; padding: 12px; border-radius: 8px; margin-bottom: 15px; border: 1px solid #e2e8f0; }
    .stock-card { background: white; border-radius: 10px; padding: 15px; border-left: 6px solid #cbd5e1; margin-bottom: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.02); }
    .score-badge { font-size: 16px; font-weight: bold; padding: 3px 12px; border-radius: 15px; color: white; margin-bottom: 8px; display: inline-block; }
    .price-text { font-size: 24px; font-weight: bold; }
    .data-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 10px; text-align: center; background: #f1f5f9; padding: 12px; border-radius: 8px; margin-top: 10px; }
    .data-item { display: flex; flex-direction: column; }
    .data-val { font-size: 16px; font-weight: bold; color: #1e293b; }
    .data-label { font-size: 11px; color: #64748b; }
    /* 优化折叠面板样式 */
    .stExpander { border: none !important; box-shadow: none !important; margin-top: 5px !important; }
    </style>
    """, unsafe_allow_html=True)

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
    # 核心计算逻辑
    premium = round((s['open'] - s['last_close']) / s['last_close'] * 100, 2) if s['last_close'] > 0 else 0
    intraday_body = round((s['price'] - s['open']) / s['open'] * 100, 2) if s['open'] > 0 else 0
    range_val = (s['high'] - s['low'])
    wr = round((s['high'] - s['price']) / range_val * 100, 2) if range_val != 0 else 50

    score = 60
    advice = "区间震荡，主力意图不明确"
    logic_detail = "当前价格处于日内波动中部，换手与实体涨跌处于平衡态。"

    # 逻辑推演
    if premium > 2 and intraday_body < -1.5:
        score -= 25; advice = "⚠️ 高开低走（诱多陷阱）"; logic_detail = "典型的开盘抢筹失败，上方抛压沉重。主力利用高开空间完成日内派发，建议减仓或规避。"
    elif premium < -1 and intraday_body > 1.5:
        score += 30; advice = "🔥 低开高走（弱转强）"; logic_detail = "恐慌盘杀出后获得强力承接，资金逆势扫货。属于典型的反核博弈信号，具备走强潜力。"
    elif premium > 0 and intraday_body > 1:
        score += 15; advice = "📈 稳步推升（强趋势）"; logic_detail = "价格始终运行在开盘价上方，买盘力量持续释放，主力锁筹良好。"
    elif premium < 0 and intraday_body < -1:
        score -= 20; advice = "🧊 阴跌向下（弃庄状态）"; logic_detail = "无任何抵抗力量，资金流出明显，大概率继续向下寻底。"

    if wr > 85: score += 10; advice += " + 超跌反抽预测"
    if wr < 15: score -= 10; advice += " + 超买回调警示"

    score = max(0, min(100, score))
    badge_bg = "#f21b2b" if score >= 80 else ("#00a800" if score <= 40 else "#ff9800")
    main_color = "#f21b2b" if s['change'] >= 0 else "#00a800"
    
    return score, badge_bg, advice, logic_detail, premium, intraday_body, wr, main_color

# --- 界面排版 ---
st.title("🦅 鹰眼实时监控系统")
c1, c2 = st.columns([4, 1])
with c1:
    new_stock = st.text_input("", placeholder="🔍 输入股票代码（如 002428）", label_visibility="collapsed")
with c2:
    if st.button("🚀 挂载监控", use_container_width=True):
        if new_stock:
            c = new_stock.strip()
            if len(c) == 6 and c.isdigit(): c = f"sh{c}" if c.startswith(('6', '9')) else f"sz{c}"
            st.session_state.pool.insert(0, c)
            st.session_state.pool = list(dict.fromkeys(st.session_state.pool))
            st.rerun()

data = get_data(st.session_state.pool)
if data:
    # 渲染指数
    idx_cols = st.columns(3)
    for i, s in enumerate(data[:3]):
        with idx_cols[i]:
            c_color = "#f21b2b" if s['change'] >= 0 else "#00a800"
            st.markdown(f'<div class="index-bar"><small>{s["name"]}</small><br><b style="color:{c_color}; font-size:18px;">{s["price"]} ({s["change"]}%)</b></div>', unsafe_allow_html=True)

    st.markdown("### 📋 监控池状态")
    for s in data[3:]:
        score, badge_bg, advice, logic_detail, premium, ib, wr, main_color = analyze_logic(s)
        
        # 1. 简要卡牌（只展示分数和当前价格）
        st.markdown(f"""
            <div class="stock-card" style="border-left-color:{badge_bg}">
                <div style="display:flex; justify-content:space-between; align-items:start;">
                    <div>
                        <div class="score-badge" style="background:{badge_bg}">🦅 综合评分: {score}</div>
                        <div style="font-size:18px; font-weight:bold;">{s['name']} <small style="color:#94a3b8; font-weight:normal;">{s['code']}</small></div>
                    </div>
                    <div style="text-align:right;">
                        <div class="price-text" style="color:{main_color}">{s['price']}</div>
                        <div style="font-weight:bold; color:{main_color}">{'+' if s['change']>0 else ''}{s['change']}%</div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # 2. 详情折叠区（点击展开分析）
        with st.expander(f"📊 查看 {s['name']} 实时诊断报告"):
            st.info(f"**核心建议：** {advice}")
            st.write(f"**逻辑推演：** {logic_detail}")
            
            # 详情指标矩阵
            ib_color = "#f21b2b" if ib >= 0 else "#00a800"
            wr_color = "#00a800" if wr >= 50 else "#f21b2b"
            
            st.markdown(f"""
                <div class="data-grid">
                    <div class="data-item"><div class="data-val">{premium}%</div><div class="data-label">开盘溢价</div></div>
                    <div class="data-item"><div class="data-val" style="color:{ib_color}">{'+' if ib>0 else ''}{ib}%</div><div class="data-label">盘中实体</div></div>
                    <div class="data-item"><div class="data-val" style="color:{wr_color}">{wr}</div><div class="data-label">W&R指标</div></div>
                    <div class="data-item"><div class="data-val">{s['amplitude']}%</div><div class="data-label">今日振幅</div></div>
                    <div class="data-item"><div class="data-val" style="color:#f21b2b">{s['limit_up']}</div><div class="data-label">涨停目标</div></div>
                </div>
            """, unsafe_allow_html=True)
            
            if st.button(f"🗑️ 移出监控 {s['code']}", key=f"del_{s['code']}"):
                st.session_state.pool.remove(s['code'])
                st.rerun()

if st.button("🔄 全局手动刷新"):
    st.rerun()
