import streamlit as st
import requests
import time
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="鹰眼作战终端", layout="wide")

# 0.5秒脉冲，这是战斗节奏
count = st_autorefresh(interval=500, limit=None, key="fast_flicker")

if 'pool' not in st.session_state:
    st.session_state.pool = ["sz002428"]
if 'page' not in st.session_state:
    st.session_state.page = "home"

# 这里的CSS做了简化，防止解析压力过大
st.markdown("<style>.stApp{background-color:#0e1117;color:white;}.stock-card{background:#1e293b;border-radius:8px;padding:12px;margin-bottom:10px;border-top:3px solid #3b82f6;}.chart-container{display:flex;justify-content:space-between;gap:5px;margin-top:10px;}.chart-box{flex:1;text-align:center;background:#0f172a;padding:5px;border-radius:4px;}.chart-img{width:100%;height:auto;border-radius:2px;}.mini-label{font-size:10px;color:#94a3b8;margin-bottom:2px;}.stat-row{display:flex;justify-content:space-between;margin-top:8px;border-top:1px solid #334155;padding-top:8px;}.stat-item{text-align:center;flex:1;}.val{font-size:14px;font-weight:bold;}.lbl{font-size:10px;color:#64748b;}</style>", unsafe_allow_html=True)

def get_data(codes):
    if not codes: return []
    # 增加上证指数和富时A50作为大盘参考
    all_codes = ["sh000001", "sh000300"] + codes 
    url = f"http://qt.gtimg.cn/q={','.join(all_codes)}&_t={int(time.time()*1000)}"
    try:
        res = requests.get(url, timeout=0.8)
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
                "industry": v[28] if v[28] else "全A个股"
            })
        return results
    except: return []

stocks_all = get_data(st.session_state.pool)

if st.session_state.page == "home":
    st.title("🦅 鹰眼·分时战场 (0.5s)")
    
    with st.expander("➕ 增加监控"):
        new_stock = st.text_input("代码 (如 002428)")
        if st.button("挂载") and new_stock:
            c = new_stock.strip()
            if len(c) == 6: c = f"sh{c}" if c.startswith(('6','9')) else f"sz{c}"
            if c not in st.session_state.pool:
                st.session_state.pool.insert(0, c); st.rerun()

    if stocks_all and len(stocks_all) > 2:
        targets = stocks_all[2:] # 跳过前两个指数
        
        for s in targets:
            prem = round((s['open'] - s['last_close']) / s['last_close'] * 100, 2)
            ib = round((s['price'] - s['open']) / s['open'] * 100, 2) if s['open'] > 0 else 0
            m_color = "#ef4444" if s['change'] >= 0 else "#22c55e"
            ts = int(time.time())
            
            # 【重要】HTML内部不允许有任何换行，必须紧凑排列
            html_card = f'<div class="stock-card"><div style="display:flex;justify-content:space-between;align-items:center;"><div><span style="font-size:18px;font-weight:bold;">{s["name"]}</span><span style="color:#94a3b8;font-size:12px;margin-left:8px;">{s["code"]} | {s["industry"]}</span></div><div style="text-align:right;"><span style="font-size:20px;font-weight:bold;color:{m_color}">{s["price"]}</span><span style="color:{m_color};margin-left:5px;font-weight:bold;">{s["change"]}%</span></div></div><div class="chart-container"><div class="chart-box"><div class="mini-label">个股分时</div><img class="chart-img" src="http://image.sinajs.cn/newchart/min/n/{s["code"]}.gif?t={ts}"></div><div class="chart-box"><div class="mini-label">上证分时</div><img class="chart-img" src="http://image.sinajs.cn/newchart/min/n/sh000001.gif?t={ts}"></div></div><div class="stat-row"><div class="stat-item"><div class="val">{prem}%</div><div class="lbl">开盘溢价</div></div><div class="stat-item"><div class="val" style="color:{m_color}">{ib}%</div><div class="lbl">盘中实体</div></div><div class="stat-item"><div class="val">{s["high"]}</div><div class="lbl">今日最高</div></div><div class="stat-item"><div class="val">{s["low"]}</div><div class="lbl">今日最低</div></div></div></div>'
            
            st.markdown(html_card, unsafe_allow_html=True)
            
            c1, c2 = st.columns(2)
            with c1:
                if st.button(f"🔎 逻辑分析", key=f"det_{s['code']}", use_container_width=True):
                    st.session_state.current_target = s; st.session_state.page = "detail"; st.rerun()
            with c2:
                if st.button(f"🗑️ 移出", key=f"del_{s['code']}", use_container_width=True):
                    st.session_state.pool.remove(s['code']); st.rerun()

elif st.session_state.page == "detail":
    s = st.session_state.current_target
    if st.button("⬅️ 返回战术板"):
        st.session_state.page = "home"; st.rerun()
    
    st.header(f"📊 {s['name']} ({s['code']}) 深度分析")
    st.markdown("---")
    # 这里放置你需要的反人性博弈逻辑
    st.info("💡 正在结合当前 0.5s 分时走势进行主力意图拆解...")
