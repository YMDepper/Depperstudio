import streamlit as st
import requests
import time
import pandas as pd
import json
from streamlit_autorefresh import st_autorefresh

# 1. 基础设定
st.set_page_config(page_title="鹰眼战术终端", layout="wide")

# 2. 0.5秒极速脉冲
st_autorefresh(interval=500, limit=None, key="stable_flicker")

# 初始化监控池
if 'pool' not in st.session_state:
    st.session_state.pool = ["sz002428"]

# 黑色战场风格 CSS
st.markdown("<style>.stApp{background-color:#0e1117;color:white;}.stock-card{background:#1e293b;border-radius:10px;padding:15px;margin-bottom:10px;border-left:5px solid #f21b2b;}</style>", unsafe_allow_html=True)

def fetch_data(code):
    ts = int(time.time() * 1000)
    headers = {'Referer': 'http://stock.qq.com/'}
    try:
        # 抓取行情快照
        res_q = requests.get(f"http://qt.gtimg.cn/q={code}&_t={ts}", timeout=0.5)
        v = res_q.text.split('="')[1].split('~')
        # 抓取分时线
        res_t = requests.get(f"http://web.ifzq.gtimg.cn/appstock/app/minute/query?code={code}&_t={ts}", timeout=0.5, headers=headers)
        raw_data = json.loads(res_t.text)['data'][code]['minute']['minute']
        # 提取价格并转为相对于昨收的涨跌幅(%)
        last_close = float(v[4])
        norm_line = [(float(x[1])/last_close - 1) * 100 for x in raw_data]
        return {
            "name": v[1], "code": v[2], "price": v[3], "change": v[32],
            "open": float(v[5]), "last_close": last_close,
            "line": norm_line, "color": "#ef4444" if float(v[32]) >= 0 else "#22c55e"
        }
    except: return None

# 获取大盘基准线
market = fetch_data("sh000001")

st.title("🦅 鹰眼·极速分时 (0.5s)")

for code in st.session_state.pool:
    s = fetch_data(code)
    if s and market:
        # 对齐数据长度
        min_len = min(len(s['line']), len(market['line']))
        chart_df = pd.DataFrame({
            "个股走势(%)": s['line'][:min_len],
            "大盘参考(%)": market['line'][:min_len]
        })

        # 渲染极简卡牌
        st.markdown(f"""
            <div class="stock-card" style="border-left-color:{s['color']}">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <span style="font-size:22px;font-weight:bold;">{s['name']} <small style="color:#666;font-size:12px;">{s['code']}</small></span>
                    <span style="font-size:26px;font-weight:bold;color:{s['color']}">{s['price']} <small style="font-size:14px;">{s['change']}%</small></span>
                </div>
            </div>
        """, unsafe_allow_html=True)

        # 核心：原生图表，稳定性100%
        st.line_chart(chart_df, height=200)

        # 底部数据指标
        prem = round((s['open'] - s['last_close']) / s['last_close'] * 100, 2)
        ib = round((float(s['price']) - s['open']) / s['open'] * 100, 2) if s['open'] > 0 else 0
        
        c1, c2, c3 = st.columns([1,1,1])
        c1.metric("开盘溢价", f"{prem}%")
        c2.metric("盘中实体", f"{ib}%")
        if c3.button(f"🗑️ 移出监控", key=f"del_{code}"):
            st.session_state.pool.remove(code)
            st.rerun()
        st.write("---")
