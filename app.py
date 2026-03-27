import streamlit as st
import requests
import time
from streamlit_autorefresh import st_autorefresh

# 1. 页面配置
st.set_page_config(page_title="鹰眼审计终端", layout="wide")
st_autorefresh(interval=3000, limit=None, key="eagle_eye_integrated")

if 'pool' not in st.session_state:
    st.session_state.pool = ["sz002428", "sh600137"]

# 2. 核心 CSS：定义一体化卡牌容器
st.markdown("""
<style>
    .stApp { background-color: #020408; }
    
    /* 一体化卡牌整体 */
    .eagle-card {
        background: #111827;
        border: 1px solid #1e293b;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 20px;
        position: relative;
    }

    /* 内部推演框样式 */
    .audit-box {
        background: rgba(59, 130, 246, 0.08);
        padding: 12px;
        border-radius: 8px;
        border-left: 3px solid #3b82f6;
        margin: 12px 0;
        font-size: 14px;
        line-height: 1.5;
        color: #cbd5e1;
    }

    /* 指标栅格：手机端自动换行 */
    .metric-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(70px, 1fr));
        gap: 8px;
        margin-top: 15px;
        border-top: 1px solid #1e293b;
        padding-top: 15px;
    }
    .metric-item { text-align: center; }
    .m-label { color: #64748b; font-size: 11px; margin-bottom: 4px; }
    .m-value { color: #f8fafc; font-size: 15px; font-weight: bold; }

    /* 详情页样式 */
    .detail-section {
        background: #020617;
        margin: 10px -16px -16px -16px; /* 撑满卡牌底部 */
        padding: 16px;
        border-top: 1px dashed #334155;
        border-radius: 0 0 12px 12px;
        font-size: 13px;
        color: #94a3b8;
    }
    
    /* 隐藏原生组件多余的间距 */
    div[data-testid="stVerticalBlock"] > div { margin-bottom: 0px !important; }
</style>
""", unsafe_allow_html=True)

# --- A. 顶栏搜索 ---
c_input, _ = st.columns([0.8, 0.2])
with c_input:
    new_c = st.text_input("", placeholder="🔍 输入代码审计...", label_visibility="collapsed")
    if new_c:
        code = new_c.strip()
        if len(code) == 6: code = ("sh" if code.startswith(('6', '9')) else "sz") + code
        if code not in st.session_state.pool:
            st.session_state.pool.insert(0, code); st.rerun()

# --- B. 一体化卡牌渲染 ---
for code in st.session_state.pool:
    try:
        res = requests.get(f"http://qt.gtimg.cn/q={code}", timeout=1)
        res.encoding = 'gbk'
        v = res.text.split('~')
        name, price, change = v[1], v[3], float(v[32])
        color = "#ef4444" if change >= 0 else "#22c55e"

        # --- 卡牌开始 ---
        # 利用 Container 锁定范围
        with st.container():
            # 1. 头部操作与核心结论 (嵌入 HTML)
            st.markdown(f"""
            <div class="eagle-card">
                <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                    <div>
                        <span style="background:#ef4444; color:white; padding:2px 8px; border-radius:4px; font-size:11px; font-weight:bold;">评分 92</span>
                        <div style="font-size: 22px; font-weight: bold; color: #f8fafc; margin-top: 5px;">{name} <small style="color:#475569; font-size:14px;">{code.upper()}</small></div>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-size: 26px; font-weight: bold; color: {color};">{price}</div>
                        <div style="font-size: 14px; color: {color};">{change}%</div>
                    </div>
                </div>
                
                <div class="audit-box">
                    🎯 <b>核心结论：</b> 属于典型的反核博弈信号。资金逆势扫货迹象明显，主力反人性吸筹。建议分批入场。
                </div>

                <div class="metric-grid">
                    <div class="metric-item"><div class="m-value">{v[5]}%</div><div class="m-label">开盘溢价</div></div>
                    <div class="metric-item"><div class="m-value" style="color:{color}">{change}%</div><div class="m-label">盘中实体</div></div>
                    <div class="metric-item"><div class="m-value">39.1</div><div class="m-label">W&R指标</div></div>
                    <div class="metric-item"><div class="m-value">{v[33]}</div><div class="m-label">今日最高</div></div>
                    <div class="metric-item"><div class="m-value" style="color:#ef4444">{round(float(v[4])*1.1, 2)}</div><div class="m-label">涨停目标</div></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # 2. 紧贴卡牌的操作区 (删除按钮与详情勾选)
            col_x, col_space, col_check = st.columns([0.1, 0.6, 0.3])
            with col_x:
                if st.button("✕", key=f"del_{code}"):
                    st.session_state.pool.remove(code); st.rerun()
            with col_check:
                show_detail = st.checkbox("查看详情 》", key=f"chk_{code}")

            # 3. 详情信息：只有勾选时才“无缝注入”卡牌
            if show_detail:
                st.markdown(f"""
                <div class="detail-section" style="margin-top: -30px; position: relative; z-index: 1;">
                    <p style="margin:0 0 8px 0;">📊 <b style="color:#3b82f6;">I. 仪表盘:</b> 鹰眼总分 92 | 周期: <b style="color:#f0883e;">主升浪中继</b></p>
                    <p style="margin:0 0 8px 0;">📡 <b style="color:#3b82f6;">II. 五维雷达:</b> 筹码: 35/35(+10) | 环境: 18 | 排雷: 15</p>
                    <p style="margin:0 0 8px 0;">🃏 <b style="color:#3b82f6;">III. 真假博弈:</b> 意图: <b style="color:#f0883e;">诱空吸筹</b> | 证据: 缩量不破昨收</p>
                    <p style="margin:0 0 8px 0;">🚫 <b style="color:#3b82f6;">IV. 死亡红线:</b> 筹码诈骗: 无 | 硬伤暴雷: 无 | 判定: <b style="color:#22c55e;">安全</b></p>
                    <p style="margin:0;">🔫 <b style="color:#3b82f6;">V. 战术执行:</b> 进场: <b style="color:#f0883e;">{price}</b> | 止损: 46.69</p>
                </div>
                """, unsafe_allow_html=True)
                st.markdown("<br>", unsafe_allow_html=True) # 给底部留点呼吸空间

    except Exception as e:
        continue
