import streamlit as st
import requests
import time
import pandas as pd
import json
from streamlit_autorefresh import st_autorefresh

# 1. 极简配置
st.set_page_config(page_title="鹰眼战术终端", layout="wide")

# 2. 0.5秒极速脉冲 (稳定跑通后再调回500)
st_autorefresh(interval=500, limit=None, key="battle_flicker")

if 'pool' not in st.session_state:
    st.session_state.pool = ["sz002428"]

# 黑色战场风格
st.markdown("<style>.stApp{background-color:#0e1117;color:white;}.stock-card{background:#1e293b;border-radius:10px;padding:12px;margin-bottom:10px;border-left:5px solid #f21b2b;}.stat-val{font-size:18px;font-weight:bold;}.stat-lbl{font-size:11px;color:#888;}</style>", unsafe_allow_html=True)

def fetch_snapshot(code):
    ts = int(time.time() * 1000)
    headers = {'Referer': 'http://stock.qq.com/'}
    try:
        # 行情快照
        res_q = requests.get(f"http://qt.gtimg.cn/q={code}&_t={ts}", timeout=0.5)
        v = res_q.text.split('="')[1].split('~')
        # 分时线数据
        res_t = requests.get(f"http://web.ifzq.gtimg.cn/appstock/app/minute/query?code={code}&_t={ts}", timeout=0.5, headers=headers)
        raw_data = json.loads(res_t.text)['data'][code]['minute']['minute']
        price_list = [float(x[1]) for x in raw_data]
        return {
            "name": v[1], "code": v[2], "price": v[3], "change": v[32],
            "open": float(v[5]), "last_close": float(v[4]),
            "line": price_list, "color": "#ef4444" if float(v[32]) >= 0 else "#22c55e"
        }
    except: return None

# 获取大盘数据
market = fetch_snapshot("sh000001")

st.title("🦅 鹰眼·极速战场 (0.5s)")

for code in st.session_state.pool:
    s = fetch_snapshot(code)
    if s and market:
        # 数据归一化处理（为了让个股和大盘能在同一个高度显示对比）
        # 计算逻辑：将价格转化为相对于开盘价的百分比变化
        s_norm = [(p / s['last_close'] - 1) * 100 for p in s['line']]
        m_norm = [(p / market['last_close'] - 1) * 100 for p in market['line']]
        
        # 补齐长度对齐
        min_len = min(len(s_norm), len(m_norm))
        chart_df = pd.DataFrame({
            "个股走势": s_norm[:min_len],
            "大盘参考": m_norm[:min_len]
        })

        # 渲染卡牌信息
        st.markdown(f"""
            <div class="stock-card" style="border-left-color:{s['color']}">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <span style="font-size:20px;font-weight:bold;">{s['name']} <small style="color:#666;">{s['code']}</small></span>
                    <span style="font-size:24px;font-weight:bold;color:{s['color']}">{s['price']} <small>{s['change']}%</small></span>
                </div>
            </div>
        """, unsafe_allow_html=True)

        # 核心：原生双线图表 (不会闪崩)
        st.line_chart(chart_df, height=180, use_container_width=True)

        # 底部数据栏
        prem = round((s['open'] - s['last_close']) / s['last_close'] * 100, 2)
        ib = round((float(s['price']) - s['open']) / s['open'] * 100, 2) if s['open'] > 0 else 0
        
        col1, col2, col3 = st.columns(3)
        col1.metric("开盘溢价", f"{prem}%")
        col2.metric("盘中实体", f"{ib}%", delta_color="normal")
        if col3.button(f"🗑️ 移出监控", key=f"del_{code}"):
            st.session_state.pool.remove(code)
            st.rerun()
        st.write("---")
