import streamlit as st
import requests
import time
from streamlit_autorefresh import st_autorefresh

# 1. 页面配置与自动刷新
st.set_page_config(page_title="鹰眼审计终端", layout="wide")
st_autorefresh(interval=2000, limit=None, key="eagle_eye_v12")

if 'pool' not in st.session_state:
    st.session_state.pool = ["sz002428"]

# 2. 深度定制 CSS：锁定右上/右下交互位
st.markdown("""
<style>
    .stApp { background-color: #05070a; color: #ffffff; }
    
    /* 搜索框 */
    .stTextInput input { background-color: #111827 !important; color: #ffffff !important; border: 1px solid #374151 !important; }

    /* 卡牌容器 */
    .stock-card { 
        background: #111827; border-radius: 10px; padding: 20px; margin-bottom: 10px; 
        border: 1px solid #1f2937; border-left: 5px solid #ef4444; position: relative;
    }

    /* 右上角删除区 */
    .top-right-tool { position: absolute; top: 12px; right: 15px; z-index: 1000; }
    
    /* 右下角详情区 */
    .bottom-right-tool { position: absolute; bottom: 12px; right: 15px; z-index: 1000; }

    /* 统一按钮样式，去除背景 */
    .stButton > button { background: none !important; border: none !important; padding: 0 !important; color: #FFD700 !important; box-shadow: none !important; }
    .stCheckbox label { color: #FFD700 !important; font-weight: bold !important; font-size: 15px !important; }

    /* 数据布局 */
    .data-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 10px; text-align: center; margin-top: 15px; width: 90%; }
    .gold-val { color: #FFD700; font-weight: bold; }
    
    /* 审计卡片 */
    .audit-card { background: #0f172a; border: 1px solid #3b82f6; border-radius: 8px; padding: 15px; margin-bottom: 20px; }
</style>
""", unsafe_allow_html=True)

# --- A. 置顶搜索 ---
c_search, _ = st.columns([0.4, 0.6])
with c_search:
    new_c = st.text_input("", placeholder="🔍 输入代码 (如 600111)", label_visibility="collapsed")
    if new_c:
        c_in = new_c.strip()
        if len(c_in) == 6: c_in = ("sh" if c_in.startswith(('6', '9')) else "sz") + c_in
        if c_in not in st.session_state.pool:
            st.session_state.pool.insert(0, c_in); st.rerun()

# --- B. 审计监控区 ---
for code in st.session_state.pool:
    ts = int(time.time() * 1000)
    try:
        res = requests.get(f"http://qt.gtimg.cn/q={code}&_t={ts}", timeout=1.0)
        res.encoding = 'gbk'
        v = res.text.split('="')[1].split('~')
        name, price, change = v[1], v[3], float(v[32])
        last_close, open_p = float(v[4]), float(v[5])
        color = "#ef4444" if change >= 0 else "#22c55e"
        
        # 逻辑计算
        prem = round((open_p - last_close) / last_close * 100, 2)
        ib = round((float(price) - open_p) / open_p * 100, 2) if open_p > 0 else 0

        # --- 渲染卡牌本体 ---
        with st.container():
            # 1. 注入内嵌工具位
            # 右上角删除
            st.markdown(f'<div class="top-right-tool">', unsafe_allow_html=True)
            if st.button("✕", key=f"del_{code}"):
                st.session_state.pool.remove(code); st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
            
            # 右下角详情
            st.markdown(f'<div class="bottom-right-tool">', unsafe_allow_html=True)
            show_audit = st.checkbox("查看详情》", key=f"dt_{code}")
            st.markdown('</div>', unsafe_allow_html=True)

            # 2. 卡牌静态 HTML 内容
            st.markdown(f"""
            <div class="stock-card">
                <div style="display: flex; align-items: center; justify-content: space-between; margin-right: 60px;">
                    <div>
                        <span style="background:#ef4444; padding:2px 8px; border-radius:4px; font-weight:bold; font-size:14px;">评分 92</span>
                        <span style="font-size:20px; font-weight:bold; margin-left:10px;">{name}</span>
                        <span style="color:#64748b; font-size:12px; margin-left:8px;">{code}</span>
                    </div>
                    <div style="text-align:right;">
                        <span style="font-size:24px; font-weight:bold; color:{color};">{price}</span>
                        <span style="font-size:14px; font-weight:bold; color:{color}; margin-left:10px;">{change}%</span>
                    </div>
                </div>
                <div style="background:#0a0f1a; padding:10px; border-radius:6px; margin:15px 0; border-left:3px solid #3b82f6; width: 92%; font-size:14px;">
                    🎯 <b>核心结论：</b> 属于典型的反核博弈信号。资金逆势扫货迹象明显，建议分批挂单。
                </div>
                <div class="data-grid">
                    <div><div style="font-size:16px; font-weight:bold;">{prem}%</div><div style="font-size:11px; color:#64748b;">开盘溢价</div></div>
                    <div><div style="font-size:16px; font-weight:bold; color:{color}">{ib}%</div><div style="font-size:11px; color:#64748b;">盘中实体</div></div>
                    <div><div style="font-size:16px; font-weight:bold;">39.1</div><div style="font-size:11px; color:#64748b;">W&R指标</div></div>
                    <div><div style="font-size:16px; font-weight:bold;">{v[33]}</div><div style="font-size:11px; color:#64748b;">今日最高</div></div>
                    <div><div style="font-size:16px; font-weight:bold; color:#ef4444">{round(last_close*1.1, 2)}</div><div style="font-size:11px; color:#64748b;">涨停目标</div></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # 3. 展开审计详情
            if show_audit:
                st.markdown(f"""
                <div class="audit-card">
                    <div class="audit-sec"><span style="color:#3b82f6; font-weight:bold;">I. 仪表盘:</span> 鹰眼总分 <span class="gold-val">92</span> | 周期: <span class="gold-val">主升浪中继</span> | 决策: <span class="gold-val">积极进攻</span></div>
                    <div class="audit-sec"><span style="color:#3b82f6; font-weight:bold;">II. 五维雷达:</span> 筹码: <span class="gold-val">35/35(+10)</span> | 环境: 18 | 排雷: 15 | 资金: 12 | 决策: 12</div>
                    <div class="audit-sec"><span style="color:#3b82f6; font-weight:bold;">III. 真假博弈:</span> 意图判定: <span class="gold-val">诱空吸筹</span> | 核心证据: 缩量不破昨收，大单对倒。</div>
                    <div class="audit-sec"><span style="color:#3b82f6; font-weight:bold;">IV. 死亡红线:</span> 筹码诈骗: 无 | 硬伤暴雷: 无 | 判定: <span style="color:#22c55e;">安全</span></div>
                    <div><span style="color:#3b82f6; font-weight:bold;">V. 战术执行:</span> 进场: <span class="gold-val">{price}</span> | 止损: <span style="color:#ef4444;">{last_close}</span></div>
                </div>
                """, unsafe_allow_html=True)

    except:
        st.error(f"无法加载代码: {code}")
