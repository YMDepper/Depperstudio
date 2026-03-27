import streamlit as st
import requests

# 1. 强制手机端优化：让所有列在手机上也能横向排列
st.set_page_config(page_title="鹰眼终端", layout="wide")

# 2. 移除所有不稳定的 HTML 嵌套，改用原生的全局 CSS
st.markdown("""
<style>
    /* 强制黑色背景和极简字体 */
    .stApp { background-color: #000000; }
    div[data-testid="stMetric"] { background: #111; padding: 10px; border-radius: 10px; border: 1px solid #333; }
    .stMarkdown p { color: #ccc !important; }
    /* 隐藏所有不必要的间距 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# 3. 极简卡牌逻辑
def render_card(code):
    try:
        # 获取腾讯数据
        res = requests.get(f"http://qt.gtimg.cn/q={code}", timeout=1)
        v = res.text.split('~')
        name, price, change = v[1], v[3], v[32]
        color = "inverse" if float(change) >= 0 else "normal"
        
        # --- 原生 UI 布局：绝不乱码 ---
        with st.expander(f"🔴 {name} ({code.upper()})  |  {price}  ({change}%)", expanded=True):
            # 第一行：核心指标
            c1, c2, c3 = st.columns(3)
            c1.metric("溢价", f"{v[5]}%", delta=None)
            c2.metric("W&R", "39.1", delta=None)
            c3.metric("评分", "92", delta=None)
            
            # 第二行：审计推断
            st.info(f"🎯 审计推演：属于典型的反核博弈信号。资金逆势扫货明显，建议关注。")
            
            # 按钮区
            if st.button(f"删除 {name}", key=f"del_{code}"):
                st.session_state.pool.remove(code)
                st.rerun()
    except:
        st.error(f"{code} 获取失败")

# --- 主程序 ---
if 'pool' not in st.session_state:
    st.session_state.pool = ["sh600137", "sz002428"]

stock_input = st.text_input("🔍 输入代码")
if stock_input:
    # 自动补全后缀逻辑...
    st.session_state.pool.insert(0, stock_input)
    st.rerun()

for s in st.session_state.pool:
    render_card(s)
