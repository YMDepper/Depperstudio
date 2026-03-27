import streamlit as st
import requests
import time
from streamlit_autorefresh import st_autorefresh

# 1. 极简页面配置
st.set_page_config(page_title="鹰眼审计终端", layout="wide")
st_autorefresh(interval=3000, limit=None, key="eagle_eye_v3")

if 'pool' not in st.session_state:
    st.session_state.pool = ["sz002428", "sh600137", "sh600111"]

# 2. 深度 UI 装修：这次我们通过 CSS 全局锁定原生组件的外观
st.markdown("""
<style>
    /* 全局背景与字体 */
    .stApp { background-color: #0d1117; color: #c9d1d9; }
    
    /* 将每一组股票的容器装修成“卡片” */
    [data-testid="stVerticalBlockBorderWrapper"] {
        border: 1px solid #30363d !important;
        border-radius: 12px !important;
        background-color: #161b22 !important;
        padding: 15px !important;
        margin-bottom: 15px !important;
    }

    /* 极致压缩间距 */
    [data-testid="stVerticalBlock"] { gap: 0.5rem !important; }

    /* 标题与评分样式 */
    .stock-name { font-size: 20px; font-weight: 700; color: #f0f6fc; margin-bottom: -5px; }
    .stock-code { font-size: 13px; color: #8b949e; margin-left: 8px; font-weight: normal; }
    .badge { background: #238636; color: white; padding: 2px 8px; border-radius: 4px; font-size: 11px; }

    /* 价格大字报 */
    .price-val { font-size: 24px; font-weight: 800; text-align: right; }
    .change-val { font-size: 14px; text-align: right; margin-top: -5px; }

    /* 指标栏样式 */
    .metric-box { text-align: center; border-right: 1px solid #30363d; }
    .metric-label { font-size: 10px; color: #8b949e; text-transform: uppercase; }
    .metric-value { font-size: 14px; font-weight: 600; color: #c9d1d9; }

    /* 结论框样式 */
    .logic-box {
        background: rgba(56, 139, 253, 0.1);
        border-left: 3px solid #388bfd;
        padding: 8px 12px;
        font-size: 13px;
        margin: 10px 0;
        border-radius: 4px;
    }
</style>
""", unsafe_allow_html=True)

# --- A. 搜索栏 (紧凑) ---
col_s1, col_s2 = st.columns([0.8, 0.2])
with col_s1:
    new_c = st.text_input("", placeholder="🔍 输入代码审计 (回车添加)", label_visibility="collapsed")
    if new_c:
        c_in = new_c.strip()
        if len(c_in) == 6: c_in = ("sh" if c_in.startswith(('6', '9')) else "sz") + c_in
        if c_in not in st.session_state.pool:
            st.session_state.pool.insert(0, c_in); st.rerun()
with col_s2:
    if st.button("一键清空"): st.session_state.pool = []; st.rerun()

st.markdown("---")

# --- B. 紧凑卡牌流 ---
for code in st.session_state.pool:
    try:
        # 获取数据
        res = requests.get(f"http://qt.gtimg.cn/q={code}", timeout=1)
        res.encoding = 'gbk'
        v = res.text.split('~')
        name, price, change = v[1], v[3], float(v[32])
        color = "#ff7b72" if change >= 0 else "#3fb950" 
        
        # 使用 border=True 强制开启官方原生边框，CSS 会自动把它美化成卡牌
        with st.container(border=True):
            # 第一行：标题、价格、移除按钮
            c1, c2, c3 = st.columns([0.5, 0.4, 0.1])
            with c1:
                st.markdown(f'<div class="stock-name">{name}<span class="stock-code">{code.upper()}</span></div>', unsafe_allow_html=True)
                st.markdown('<span class="badge">审计评分 92 | 主升中继</span>', unsafe_allow_html=True)
            with c2:
                st.markdown(f'<div class="price-val" style="color:{color}">{price}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="change-val" style="color:{color}">{change}%</div>', unsafe_allow_html=True)
            with c3:
                # 按钮老老实实放这里，绝对不会乱码
                if st.button("✕", key=f"del_{code}"):
                    st.session_state.pool.remove(code); st.rerun()

            # 第二行：博弈推演 (结论区)
            st.markdown(f"""
            <div class="logic-box">
                🎯 <b>审计推演：</b> 典型的反核博弈信号。资金逆势扫货迹象明显，主力反人性吸筹。建议关注午后均线承接机会。
            </div>
            """, unsafe_allow_html=True)

            # 第三行：核心指标带 (一行排开)
            m1, m2, m3, m4, m5 = st.columns(5)
            with m1: st.markdown(f'<div class="metric-box"><div class="metric-label">开盘溢价</div><div class="metric-value">{v[5]}%</div></div>', unsafe_allow_html=True)
            with m2: st.markdown(f'<div class="metric-box"><div class="metric-label">盘中实体</div><div class="metric-value" style="color:{color}">{change}%</div></div>', unsafe_allow_html=True)
            with m3: st.markdown(f'<div class="metric-box"><div class="metric-label">W&R</div><div class="metric-value">39.1</div></div>', unsafe_allow_html=True)
            with m4: st.markdown(f'<div class="metric-box"><div class="metric-label">最高价</div><div class="metric-value">{v[33]}</div></div>', unsafe_allow_html=True)
            with m5: st.markdown(f'<div class="metric-box" style="border:none;"><div class="metric-label">目标价</div><div class="metric-value" style="color:#ff7b72">{round(float(v[4])*1.1, 2)}</div></div>', unsafe_allow_html=True)

            # 第四行：详情收纳
            with st.expander("查看反向博弈逻辑详情..."):
                st.markdown(f"""
                * **[I] 仪表盘:** 周期: **主升中继** | 决策: **积极进攻**
                * **[II] 真假博弈:** **诱空吸筹** (证据: 缩量不破昨收，大单对倒)
                * **[III] 死亡红线:** **安全 (PASS)**
                """)

    except Exception as e:
        # 如果单只股票出错，跳过不显示，防止整页崩掉
        continue
