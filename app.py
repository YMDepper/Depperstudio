import streamlit as st
import requests
import time
import pandas as pd
import json
from streamlit_autorefresh import st_autorefresh

# 1. 设置
st.set_page_config(page_title="鹰眼生存模式", layout="wide")

# 2. 刷新频率稍微缓一缓，先确保能跑通，稳住后再调快
st_autorefresh(interval=2000, limit=None, key="safe_flicker")

if 'pool' not in st.session_state:
    st.session_state.pool = ["sz002428"]

def get_data(code):
    ts = int(time.time() * 1000)
    try:
        # 行情快照
        res_q = requests.get(f"http://qt.gtimg.cn/q={code}&_t={ts}", timeout=1)
        v = res_q.text.split('="')[1].split('~')
        # 分时线
        res_t = requests.get(f"http://web.ifzq.gtimg.cn/appstock/app/minute/query?code={code}&_t={ts}", timeout=1)
        raw_data = json.loads(res_t.text)['data'][code]['minute']['minute']
        # 换算成涨跌幅
        last_close = float(v[4])
        line = [(float(x[1])/last_close - 1) * 100 for x in raw_data]
        return {"name": v[1], "price": v[3], "change": v[32], "line": line}
    except: return None

st.title("🦅 鹰眼·战场自救模式")

# 获取大盘作为基准
market = get_data("sh000001")

for code in st.session_state.pool:
    s = get_data(code)
    if s and market:
        # 头部信息
        col_t1, col_t2 = st.columns([3, 1])
        with col_t1:
            st.subheader(f"{s['name']} ({code})")
        with col_t2:
            st.metric("实时价", s['price'], f"{s['change']}%")
        
        # 核心对比图：原生组件最稳
        min_len = min(len(s['line']), len(market['line']))
        df = pd.DataFrame({
            "个股(%)": s['line'][:min_len],
            "大盘(%)": market['line'][:min_len]
        })
        st.line_chart(df)
        
        if st.button(f"🗑️ 移出 {s['name']}", key=f"del_{code}"):
            st.session_state.pool.remove(code)
            st.rerun()
        st.write("---")

# 增加监控
new_c = st.text_input("添加代码")
if st.button("挂载") and new_c:
    st.session_state.pool.insert(0, new_c)
    st.rerun()
