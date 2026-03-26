import streamlit as st
import requests

# 1. 页面极简配置
st.set_page_config(page_title="鹰眼体检终端", layout="wide")

# 2. 注入 CSS：强化“体检报告”的视觉感
st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    .score-circle { 
        width: 60px; height: 60px; line-height: 60px; border-radius: 50%; 
        text-align: center; font-size: 20px; font-weight: bold; color: white;
    }
    .report-card { 
        background: white; padding: 15px; border-radius: 10px; 
        margin-bottom: 10px; border: 1px solid #eee; 
    }
    .metric-label { color: #888; font-size: 12px; }
    </style>
    """, unsafe_allow_html=True)

# --- 核心函数：自动体检评分算法 ---
def analyze_stock(s, chip_target, weekly_target):
    score = 50 # 初始分
    details = []
    
    # 维度1：偏离度（日线筹码位）
    if s['change'] <= chip_target:
        score += 20
        details.append(f"✅ 触及日线筹码支撑 ({s['change']}%)，主力反人性诱空概率大。")
    elif s['change'] > 3.0:
        score -= 10
        details.append("⚠️ 短期涨幅过快，远离筹码密集区，不宜追高。")
        
    # 维度2：量价博弈
    if s['turnover'] < 2.0 and s['change'] < 0:
        score += 15
        details.append(f"✅ 缩量下跌 (换手{s['turnover']}%)，属于无量空跌，洗盘特征明显。")
    elif s['turnover'] > 8.0:
        score -= 10
        details.append(f"❌ 换手率异常 ({s['turnover']}%)，主力分歧加大，谨防放量滞涨。")

    # 维度3：周线战略位
    if s['change'] <= weekly_target:
        score += 15
        details.append("💎 确认进入周线级别战略区，具备长线反博弈价值。")

    # 最终评分修正
    score = min(max(score, 0), 100)
    
    # 颜色判定
    color = "#f21b2b" if score >= 70 else ("#00a800" if score <= 40 else "#666")
    status = "极佳" if score >= 80 else ("风险" if score <= 40 else "中性")
    
    return score, details, color, status

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
            if len(info) < 38: continue
            results.append({
                "name": info[1], "code": info[2], "price": info[3],
                "change": float(info[32]), "turnover": float(info[38]),
                "high": info[33], "low": info[34], "amount": info[37]
            })
        return results
    except: return []

# --- 侧边栏：同步默认股票与参数 ---
with st.sidebar:
    st.header("🦅 鹰眼扫描配置")
    if 'pool' not in st.session_state:
        # 这里预设你最关注的票
        st.session_state.pool = ["sz002428", "sh600930", "sh600584", "sh600219"]
    
    chip_zone = st.slider("日线筹码触发位 (%)", -10.0, 0.0, -3.0)
    weekly_zone = st.slider("周线战略触发位 (%)", -20.0, -5.0, -10.0)
    
    st.divider()
    new_code = st.text_input("添加新股票代码")
    if st.button("添加到监控列表"):
        c = new_code.strip()
        if len(c) == 6 and c.isdigit():
            c = f"sh{c}" if c.startswith(('6', '9')) else f"sz{c}"
        st.session_state.pool.append(c)
        st.session_state.pool = list(set(st.session_state.pool))
        st.rerun()

# --- 主界面：体检报告清单 ---
st.title("🎯 鹰眼系统：实时体检看板")

stocks = get_data(st.session_state.pool)

if stocks:
    for s in stocks:
        score, details, color, status = analyze_stock(s, chip_zone, weekly_zone)
        
        # 这一块模仿“体检报告”的卡片
        with st.container():
            col_score, col_info, col_btn = st.columns([1, 4, 1])
            
            with col_score:
                st.markdown(f"""<div class="score-circle" style="background:{color}">{score}</div>""", unsafe_allow_html=True)
                st.markdown(f"<div style='text-align:center; color:{color}; font-weight:bold;'>{status}</div>", unsafe_allow_html=True)
            
            with col_info:
                st.markdown(f"**{s['name']}** ({s['code']})")
                st.markdown(f"""
                <span class="metric-label">最新:</span> <b style="color:{color}">¥{s['price']}</b> | 
                <span class="metric-label">涨跌:</span> <b style="color:{color}">{s['change']}%</b> | 
                <span class="metric-label">换手:</span> {s['turnover']}%
                """, unsafe_allow_html=True)
            
            with col_btn:
                # 点击展开详细分析
                with st.expander("查看详情"):
                    st.write("---")
                    st.subheader("🏥 鹰眼深度分析")
                    for d in details:
                        st.write(d)
                    st.write(f"📊 **今日博弈数据**：最高 {s['high']} / 最低 {s['low']} / 成交额 {round(float(s['amount'])/10000, 2)}亿")
            
            st.markdown("<hr style='margin:10px 0; opacity:0.1'>", unsafe_allow_html=True)

else:
    st.info("监控池为空，请在左侧边栏添加股票。")

if st.button("🔄 全局刷新体检数据"):
    st.rerun()
