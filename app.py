import streamlit as st
import requests
import time
import json
from streamlit_autorefresh import st_autorefresh
from streamlit_echarts import st_echarts

# 1. 基础配置
st.set_page_config(page_title="鹰眼战术终端", layout="wide")

# 2. 稳定性增强：建议先设为 1000ms（1秒），若稳定再尝试调回 500
st_autorefresh(interval=1000, limit=None, key="st_flicker")

if 'pool' not in st.session_state:
    st.session_state.pool = ["sz002428"]

# 极简暗黑样式
st.markdown("<style>.stApp{background-color:#0e1117;color:white;}.stock-card{background:#1e293b;border-radius:8px;padding:12px;margin-bottom:5px;border-top:3px solid #f21b2b;}.stat-grid{display:flex;justify-content:space-between;margin-top:10px;text-align:center;}</style>", unsafe_allow_html=True)

def get_data(code):
    ts = int(time.time() * 1000)
    headers = {'Referer': 'http://stock.qq.com/'}
    try:
        # 行情数据
        res_q = requests.get(f"http://qt.gtimg.cn/q={code}&_t={ts}", timeout=0.8)
        v = res_q.text.split('="')[1].split('~')
        # 分时数据
        res_t = requests.get(f"http://web.ifzq.gtimg.cn/appstock/app/minute/query?code={code}&_t={ts}", timeout=0.8, headers=headers)
        price_line = [float(item[1]) for item in json.loads(res_t.text)['data'][code]['minute']['minute']]
        return {
            "name": v[1], "code": v[2], "price": v[3], "change": v[32],
            "open": float(v[5]), "last_close": float(v[4]), 
            "line": price_line, "color": "#ef4444" if float(v[32]) >= 0 else "#22c55e"
        }
    except: return None

# 获取大盘走势作为暗线背景
market_data = get_data("sh000001")

st.title("🦅 鹰眼·极速战场")

for code in st.session_state.pool:
    s = get_data(code)
    if s and market_data:
        # 计算实战参数
        prem = round((s['open'] - s['last_close']) / s['last_close'] * 100, 2)
        ib = round((float(s['price']) - s['open']) / s['open'] * 100, 2) if s['open'] > 0 else 0
        
        # 渲染卡牌头部
        st.markdown(f"""
            <div class="stock-card" style="border-top-color:{s['color']}">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <span style="font-size:20px;font-weight:bold;">{s['name']} <small style="font-size:12px;color:#888;">{s['code']}</small></span>
                    <span style="font-size:22px;font-weight:bold;color:{s['color']}">{s['price']} ({s['change']}%)</span>
                </div>
            </div>
        """, unsafe_allow_html=True)

        # 核心：ECharts 渲染（给一个极其稳定的 Key）
        options = {
            "animation": False,
            "grid": {"top": 5, "bottom": 5, "left": 0, "right": 0},
            "xAxis": {"show": False, "type": "category"},
            "yAxis": {"show": False, "type": "value", "scale": True},
            "series": [
                {"type": "line", "data": s['line'], "symbol": "none", "lineStyle": {"color": s['color'], "width": 2}},
                {"type": "line", "data": market_data['line'], "symbol": "none", "lineStyle": {"color": "rgba(255,255,255,0.1)", "width": 1}}
            ]
        }
        # 使用独立的 container 包裹图表，减少 DOM 冲突
        with st.container():
            st_echarts(options=options, height="100px", key=f"chart_v2_{code}")

        # 参数行
        st.markdown(f"""
            <div class="stat-grid">
                <div><div style="font-size:14px;font-weight:bold;">{prem}%</div><div style="font-size:10px;color:#888;">开盘溢价</div></div>
                <div><div style="font-size:14px;font-weight:bold;color:{s['color']}">{ib}%</div><div style="font-size:10px;color:#888;">盘中实体</div></div>
            </div>
            <div style="margin-bottom:20px;"></div>
        """, unsafe_allow_html=True)

        if st.button(f"🗑️ 移除 {s['name']}", key=f"del_{code}"):
            st.session_state.pool.remove(code)
            st.rerun()
