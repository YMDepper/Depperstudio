import streamlit as st
import requests
import time
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="鹰眼作战终端", layout="wide")

# 0.5秒极速脉冲
count = st_autorefresh(interval=500, limit=None, key="fast_flicker")

if 'pool' not in st.session_state:
    st.session_state.pool = ["sz002428"]
if 'page' not in st.session_state:
    st.session_state.page = "home"

st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; } /* 暗黑模式，更像交易终端 */
    .stock-card { background: #1e293b; border-radius: 8px; padding: 12px; margin-bottom: 10px; border-top: 3px solid #3b82f6; }
    .chart-container { display: flex; justify-content: space-between; gap: 5px; margin-top: 10px; }
    .chart-box { flex: 1; text-align: center; background: #0f172a; padding: 5px; border-radius: 4px; }
    .chart-img { width: 100%; height: auto; border-radius: 2px; }
    .mini-label { font-size: 10px; color: #94a3b8; margin-bottom: 2px; }
    .stat-row { display: flex; justify-content: space-between; margin-top: 8px; border-top: 1px solid #334155; padding-top: 8px; }
    .stat-item { text-align: center; flex: 1; }
    .val { font-size: 14px; font-weight: bold; }
    .lbl { font-size: 10px; color: #64748b; }
    </style>
    """, unsafe_allow_html=True)

def get_data(codes):
    if not codes: return []
    # 包含上证指数(sh000001)作为大盘参考
    all_codes = ["sh000001"] + codes
    url = f"http://qt.gtimg.cn/q={','.join(all_codes)}&_t={int(time.time())}"
    try:
        res = requests.get(url, timeout=1)
        res.encoding = 'gbk'
        data_list = []
        for line in res.text.strip().split(';'):
            if '="' not in line: continue
            v = line.split('=')[1].strip('"').split('~')
            if len(v) < 48: continue
            data_list.append({
                "name": v[1], "code": v[2], "price": float(v[3]),
                "last_close": float(v[4]), "open": float(v[5]),
                "change": float(v[32]), "high": float(v[33]), "low": float(v[34]),
                "industry": v[28] if v[28] else "全A个股" # 所属板块信息
            })
        return data_list
    except: return []

stocks = get_data(st.session_state.pool)

if st.session_state.page == "home":
    st.title("🦅 鹰眼·分时战场 (0.5s)")
    
    # 顶部添加
    with st.expander("➕ 添加监控标的"):
        new_stock = st.text_input("输入代码")
        if new_stock:
            c = new_stock.strip()
            if len(c) == 6: c = f"sh{c}" if c.startswith(('6', '9')) else f"sz{c}"
            if c not in st.session_state.pool:
                st.session_state.pool.insert(0, c); st.rerun()

    if stocks:
        market = stocks[0] # 大盘数据
        targets = stocks[1:]
        
        for s in targets:
            # 计算核心参数
            prem = round((s['open'] - s['last_close']) / s['last_close'] * 100, 2)
            ib = round((s['price'] - s['open']) / s['open'] * 100, 2) if s['open'] > 0 else 0
            m_color = "#ef4444" if s['change'] >= 0 else "#22c55e"
            
            # 渲染卡牌
            st.markdown(f"""
                <div class="stock-card">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <div>
                            <span style="font-size:18px; font-weight:bold;">{s['name']}</span>
                            <span style="color:#94a3b8; font-size:12px;">{s['code']} | {s['industry']}</span>
                        </div>
                        <div style="text-align:right;">
                            <span style="font-size:20px; font-weight:bold; color:{m_color}">{s['price']}</span>
                            <span style="color:{m_color}; margin-left:5px;">{s['change']}%</span>
                        </div>
                    </div>
                    
                    <div class="chart-container">
                        <div class="chart-box">
                            <div class="mini-label">个股分时</div>
                            <img class="chart-img" src="http://image.sinajs.cn/newchart/min/n/{s['code']}.gif?t={int(time.time())}">
                        </div>
                        <div class="chart-box">
                            <div class="mini-label">上证分时</div>
                            <img class="chart-img" src="http://image.sinajs.cn/newchart/min/n/sh000001.gif?t={int(time.time())}">
                        </div>
                    </div>
                    
                    <div class="stat-row">
                        <div class="stat-item"><div class="val">{prem}%</div><div class="lbl">开盘溢价</div></div>
                        <div class="stat-item"><div class="val" style="color:{m_color}">{ib}%</div><div class="lbl">盘中实体</div></div>
                        <div class="stat-item"><div class="val">{s['high']}</div><div class="lbl">今日最高</div></div>
                        <div class="stat-item"><div class="val">{s['low']}</div><div class="lbl">今日最低</div></div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            c1, c2 = st.columns(2)
            with c1:
                if st.button(f"🔎 深度分析及逻辑推演", key=f"det_{s['code']}", use_container_width=True):
                    st.session_state.current_target = s; st.session_state.page = "detail"; st.rerun()
            with c2:
                if st.button(f"🗑️ 移出监控", key=f"del_{s['code']}", use_container_width=True):
                    st.session_state.pool.remove(s['code']); st.rerun()

elif st.session_state.page == "detail":
    s = st.session_state.current_target
    if st.button("⬅️ 返回分时战术板"):
        st.session_state.page = "home"; st.rerun()
    
    st.header(f"📊 {s['name']} ({s['code']}) 诊断与推演")
    # 此处放置之前复杂的分析逻辑
    st.markdown("### 🧠 主力反人性博弈推演")
    st.warning("正在根据盘中实时分时波形计算逻辑...")
    # 可以把之前的 analyze_logic 函数搬过来
