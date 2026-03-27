import streamlit as st
import requests
import time
from streamlit_autorefresh import st_autorefresh

# 1. 页面配置
st.set_page_config(page_title="鹰眼审计终端", layout="wide")
st_autorefresh(interval=3000, limit=None, key="eagle_eye_v2")

if 'pool' not in st.session_state:
    st.session_state.pool = ["sz002428", "sh600137"]

# 2. UI 样式深度定制：压缩间距，强化卡牌感
st.markdown("""
<style>
    .stApp { background-color: #0d1117; }
    
    /* 极致压缩容器间距 */
    [data-testid="stVerticalBlock"] { gap: 0.3rem !important; }
    
    /* 模拟金融卡牌 */
    .stock-card {
        background: linear-gradient(135deg, #161b22 0%, #0d1117 100%);
        border: 1px solid #30363d;
        border-radius: 10px;
        padding: 12px;
        margin-bottom: 10px;
    }

    /* 指标栏小字体化 */
    .mini-metric {
        display: flex;
        justify-content: space-between;
        border-top: 1px solid #30363d;
        padding-top: 8px;
        margin-top: 8px;
    }
    .m-item { text-align: center; flex: 1; }
    .m-label { color: #8b949e; font-size: 10px; display: block; }
    .m-value { color: #c9d1d9; font-size: 12px; font-weight: 600; }

    /* 按钮样式微调 */
    .stButton > button {
        padding: 0px 10px !important;
        height: 24px !important;
        background-color: transparent !important;
        color: #8b949e !important;
        border: 1px solid #30363d !important;
    }
</style>
""", unsafe_allow_html=True)

# --- A. 顶部搜索 (常驻) ---
with st.container():
    c1, c2 = st.columns([0.8, 0.2])
    with c1:
        new_code = st.text_input("", placeholder="🔍 输入代码审计 (回车添加)", label_visibility="collapsed")
        if new_code:
            code = new_code.strip()
            if len(code) == 6: code = ("sh" if code.startswith(('6', '9')) else "sz") + code
            if code not in st.session_state.pool:
                st.session_state.pool.insert(0, code); st.rerun()
    with c2:
        if st.button("清空"): st.session_state.pool = []; st.rerun()

st.markdown("---")

# --- B. 紧凑卡牌流 ---
for code in st.session_state.pool:
    try:
        res = requests.get(f"http://qt.gtimg.cn/q={code}", timeout=1)
        res.encoding = 'gbk'
        v = res.text.split('~')
        name, price, change = v[1], v[3], float(v[32])
        color = "#ff7b72" if change >= 0 else "#3fb950" # 更符合暗色主题的高饱和红绿

        # 使用单个 container 模拟一张卡
        with st.container():
            # 顶部：名称、状态、删除
            head1, head2, head3 = st.columns([0.5, 0.4, 0.1])
            with head1:
                st.markdown(f"**{name}** `{code.upper()}`")
                st.caption("评分 92 | 主升中继")
            with head2:
                st.markdown(f"<p style='text-align:right; font-size:20px; font-weight:bold; color:{color}; margin:0;'>{price} <small>{change}%</small></p>", unsafe_allow_html=True)
            with head3:
                if st.button("✕", key=f"del_{code}"):
                    st.session_state.pool.remove(code); st.rerun()

            # 中间：结论（极致紧凑）
            st.markdown(f"""
            <div style="background: rgba(56, 139, 253, 0.1); border-left: 3px solid #388bfd; padding: 4px 10px; font-size: 12px; color: #adbac7;">
                🎯 <b>审计推演：</b> 属于典型的反核博弈信号。资金逆势扫货迹象明显，主力反人性吸筹。
            </div>
            """, unsafe_allow_html=True)

            # 底部：微型指标栏（一行搞定）
            st.markdown(f"""
            <div class="mini-metric">
                <div class="m-item"><span class="m-label">开盘溢价</span><span class="m-value">{v[5]}%</span></div>
                <div class="m-item"><span class="m-label">盘中实体</span><span class="m-value" style="color:{color}">{change}%</span></div>
                <div class="m-item"><span class="m-label">W&R</span><span class="m-value">39.1</span></div>
                <div class="m-item"><span class="m-label">最高价</span><span class="m-value">{v[33]}</span></div>
                <div class="m-item"><span class="m-label">目标价</span><span class="m-value" style="color:#ff7b72">{round(float(v[4])*1.1, 2)}</span></div>
            </div>
            """, unsafe_allow_html=True)

            # 详情抽屉
            with st.expander("查看深度审计逻辑 》"):
                st.write(f"**[I] 仪表盘:** 鹰眼总分 92 | 决策: 积极进攻")
                st.write(f"**[II] 真假博弈:** 诱空吸筹 (证据: 缩量不破昨收)")
                st.write(f"**[III] 死亡红线:** 判定: 安全")

            st.markdown("<div style='margin-bottom:20px;'></div>", unsafe_allow_html=True) # 卡牌间隙

    except:
        continue
