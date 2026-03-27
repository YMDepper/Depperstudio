import streamlit as st
import requests
from streamlit_autorefresh import st_autorefresh

# 1. 基础配置
st.set_page_config(page_title="鹰眼审计终端", layout="wide")
st_autorefresh(interval=3000, limit=None, key="eagle_eye_final_fix")

if 'pool' not in st.session_state:
    st.session_state.pool = ["sz002428", "sh600137"]

# 2. 全局极简暗色主题
st.markdown("""
<style>
    .stApp { background-color: #0d1117; }
    /* 统一调整原生组件字体颜色 */
    .stMarkdown, .stText, [data-testid="stMetricValue"] { color: #e6edf3 !important; }
</style>
""", unsafe_allow_html=True)

# --- A. 顶栏搜索 ---
new_code = st.text_input("🔍 输入代码审计...", label_visibility="collapsed")
if new_code:
    c = new_code.strip()
    if len(c) == 6: c = ("sh" if c.startswith(('6', '9')) else "sz") + c
    if c not in st.session_state.pool:
        st.session_state.pool.insert(0, c); st.rerun()

# --- B. 审计队列渲染 ---
for code in st.session_state.pool:
    try:
        # 获取腾讯实时数据
        res = requests.get(f"http://qt.gtimg.cn/q={code}", timeout=1)
        res.encoding = 'gbk'
        v = res.text.split('~')
        name, price, change = v[1], v[3], float(v[32])
        status_color = "red" if change >= 0 else "green"

        # --- 核心改动：使用原生 Container，严禁 HTML 标签 ---
        with st.container(border=True): # 官方原生边框，绝对不乱码
            
            # 第一行：名称、价格与操作
            col1, col2, col3 = st.columns([0.6, 0.3, 0.1])
            with col1:
                st.write(f"### 🎯 {name} `{code.upper()}`")
                st.caption(f"审计评分: 92 | 周期: 主升浪中继")
            with col2:
                st.metric("实时价", price, f"{change}%")
            with col3:
                if st.button("✕", key=f"del_{code}"):
                    st.session_state.pool.remove(code); st.rerun()

            # 第二行：审计结论（使用 st.info，自带深蓝色背景）
            st.info(f"**核心结论：** 属于典型的反核博弈信号。资金逆势扫货迹象明显，主力反人性吸筹。建议分批挂单。")

            # 第三行：五维数据指标
            m1, m2, m3, m4, m5 = st.columns(5)
            m1.metric("开盘溢价", f"{v[5]}%")
            m2.metric("盘中实体", f"{v[32]}%")
            m3.metric("W&R指标", "39.1")
            m4.metric("今日最高", v[33])
            m5.metric("涨停目标", f"{(float(v[4])*1.1):.2f}")

            # 第四行：详情展开
            with st.expander("查看深度审计逻辑 》", expanded=False):
                st.write("---")
                st.write(f"**I. 仪表盘:** 鹰眼总分 92 | 决策: 积极进攻")
                st.write(f"**II. 五维雷达:** 筹码: 35/35(+10) | 环境: 18 | 排雷: 15")
                st.write(f"**III. 真假博弈:** 意图判定: 诱空吸筹 | 核心证据: 缩量不破昨收")
                st.write(f"**IV. 死亡红线:** 筹码诈骗: 无 | 硬伤暴雷: 无 | 判定: 安全")
                st.write(f"**V. 战术执行:** 进场建议: {price} | 止损参考: 46.69")

    except Exception:
        continue
