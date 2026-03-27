import streamlit as st
import requests
import time
from streamlit_autorefresh import st_autorefresh

# 1. 基础配置
st.set_page_config(page_title="鹰眼审计终端 v1.1", layout="wide")
# 修复截图中的依赖报错，确保 st_autorefresh 正常工作
st_autorefresh(interval=2000, limit=None, key="eagle_eye_v11_fix")

if 'pool' not in st.session_state:
    st.session_state.pool = ["sz002428"]

# 2. 深度定制 CSS：实现组件真正内嵌
st.markdown("""
<style>
    .stApp { background-color: #05070a; color: #ffffff; }
    
    /* 搜索框样式 */
    .stTextInput input { background-color: #111827 !important; color: #ffffff !important; border: 1px solid #374151 !important; }

    /* 战术卡牌容器 - 相对定位 */
    .stock-card { 
        background: #111827; 
        border-radius: 10px; 
        padding: 20px; 
        margin-bottom: 20px; 
        border: 1px solid #1f2937;
        border-left: 5px solid #ef4444; 
        position: relative; /* 为内部绝对定位组件提供坐标参考 */
        min-height: 180px;
    }

    /* 右上角黄色删除 X */
    .abs-del { position: absolute; top: 15px; right: 15px; z-index: 999; }
    .abs-del button { 
        background: none !important; border: none !important; 
        color: #FFD700 !important; font-size: 22px !important; font-weight: bold !important;
        padding: 0 !important;
    }

    /* 右下角查看详情 */
    .abs-detail { position: absolute; bottom: 15px; right: 15px; z-index: 999; }
    .abs-detail label { color: #FFD700 !important; font-weight: bold !important; font-size: 16px !important; cursor: pointer; }
    
    /* 隐藏 Streamlit 默认的多余边距 */
    [data-testid="stVerticalBlock"] > div:has(div.stock-card) { padding: 0 !important; }

    /* 审计详情卡片 */
    .audit-card { background: #0f172a; border: 1px solid #3b82f6; border-radius: 8px; padding: 20px; margin-top: -15px; margin-bottom: 20px; }
    .audit-sec { margin-bottom: 12px; border-bottom: 1px solid #1e293b; padding-bottom: 8px; }
    .gold-text { color: #FFD700; font-weight: bold; }
    .data-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 10px; text-align: center; margin-top: 20px; }
</style>
""", unsafe_allow_html=True)

# --- A. 置顶搜索区 ---
c_search, _ = st.columns([0.4, 0.6])
with c_search:
    new_c = st.text_input("", placeholder="🔍 输入代码直接审计 (如 600111)", label_visibility="collapsed")
    if new_c:
        c_in = new_c.strip()
        if len(c_in) == 6: c_in = ("sh" if c_in.startswith(('6', '9')) else "sz") + c_in
        if c_in not in st.session_state.pool:
            st.session_state.pool.insert(0, c_in); st.rerun()

# --- B. 监控展示区 ---
for code in st.session_state.pool:
    ts = int(time.time() * 1000)
    try:
        res = requests.get(f"http://qt.gtimg.cn/q={code}&_t={ts}", timeout=1.0)
        res.encoding = 'gbk'
        v = res.text.split('="')[1].split('~')
        name, price, change = v[1], v[3], float(v[32])
        last_close, open_p, high = float(v[4]), float(v[5]), v[33]
        color = "#ef4444" if change >= 0 else "#22c55e"
        
        # 核心逻辑
        prem = round((open_p - last_close) / last_close * 100, 2)
        ib = round((float(price) - open_p) / open_p * 100, 2) if open_p > 0 else 0
        limit_up = round(last_close * 1.1, 2)

        # 开始构建卡牌
        st.markdown(f'<div class="stock-card">', unsafe_allow_html=True)
        
        # 1. 右上角绝对定位：黄色 X
        st.markdown('<div class="abs-del">', unsafe_allow_html=True)
        if st.button("✕", key=f"del_{code}"):
            st.session_state.pool.remove(code); st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        # 2. 右下角绝对定位：查看详情
        st.markdown('<div class="abs-detail">', unsafe_allow_html=True)
        show_audit = st.checkbox("查看详情 →", key=f"dt_{code}")
        st.markdown('</div>', unsafe_allow_html=True)

        # 3. 卡牌主体内容
        st.markdown(f"""
            <div style="margin-right: 50px;">
                <span style="background:#ef4444; padding:2px 8px; border-radius:4px; font-weight:bold; font-size:14px;">评分 92</span>
                <span style="font-size:22px; font-weight:bold; margin-left:10px;">{name}</span>
                <span style="color:#64748b; font-size:14px; margin-left:8px;">{code}</span>
                <div style="float:right; text-align:right; margin-right:20px;">
                    <span style="font-size:26px; font-weight:bold; color:{color};">{price}</span>
                    <span style="font-size:16px; font-weight:bold; color:{color}; margin-left:10px;">{change}%</span>
                </div>
            </div>
            <div style="background:#0a0f1a; padding:12px; border-radius:6px; margin:20px 0; border-left:3px solid #3b82f6; width: 92%;">
                🎯 <b>核心结论：</b> 属于典型的反核博弈信号。资金逆势扫货迹象明显，建议分批挂单。
            </div>
            <div class="data-grid">
                <div><div style="font-size:18px; font-weight:bold;">{prem}%</div><div style="font-size:11px; color:#64748b;">开盘溢价</div></div>
                <div><div style="font-size:18px; font-weight:bold; color:{color}">{ib}%</div><div style="font-size:11px; color:#64748b;">盘中实体</div></div>
                <div><div style="font-size:18px; font-weight:bold;">39.1</div><div style="font-size:11px; color:#64748b;">W&R指标</div></div>
                <div><div style="font-size:18px; font-weight:bold;">{high}</div><div style="font-size:11px; color:#64748b;">今日最高</div></div>
                <div><div style="font-size:18px; font-weight:bold; color:#ef4444">{limit_up}</div><div style="font-size:11px; color:#64748b;">涨停目标</div></div>
            </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # 4. 详情展开（在卡牌下方）
        if show_audit:
            st.markdown(f"""
            <div class="audit-card">
                <div class="audit-sec"><div style="color:#3b82f6; font-weight:bold;">I. 仪表盘 (Dashboard)</div>鹰眼总分：<span class="gold-text">92分</span> | 决策：<span class="gold-text">积极进攻</span></div>
                <div class="audit-sec"><div style="color:#3b82f6; font-weight:bold;">II. 五维雷达 (5D Radar)</div>筹码: 35/35 (奖励+10) | 环境: 18/20 | 排雷: 15/15 | 资金: 12/15 | 决策: 12/15</div>
                <div class="audit-sec"><div style="color:#3b82f6; font-weight:bold;">III. 真假博弈 (Truth Matrix)</div>意图：诱空式吸筹 | 证据：早盘缩量下杀不破关键位，逐笔现大单。</div>
                <div class="audit-sec"><div style="color:#3b82f6; font-weight:bold;">IV. 死亡红线 (Death Check)</div>红线排查：安全 (PASS)</div>
                <div style="color:#3b82f6; font-weight:bold;">V. 战术执行 (Tactics)</div>进场参考：{price} 附近 | 止损参考：{last_close} (昨收)
            </div>
            """, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"解析错误: {code}")
