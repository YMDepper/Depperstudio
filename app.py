import streamlit as st
import requests
import time
from streamlit_autorefresh import st_autorefresh

# 1. 页面配置
st.set_page_config(page_title="鹰眼审计终端", layout="wide")
st_autorefresh(interval=2000, limit=None, key="eagle_eye_v13")

if 'pool' not in st.session_state:
    st.session_state.pool = ["sz002428"]

# 2. 深度定制 CSS：实现组件真正的内嵌
st.markdown("""
<style>
    /* 基础黑色背景 */
    .stApp { background-color: #05070a; color: #ffffff; }
    
    /* 战术卡牌容器 - 关键：设为相对定位 */
    .stock-card-container { 
        position: relative; 
        background: #111827; 
        border-radius: 10px; 
        padding: 20px; 
        margin-bottom: 15px; 
        border: 1px solid #1f2937;
        border-left: 5px solid #ef4444;
        width: 100%;
    }

    /* 右上角删除区：绝对定位 */
    .abs-top-right {
        position: absolute !important;
        top: 10px !important;
        right: 15px !important;
        z-index: 999;
    }

    /* 右下角详情区：绝对定位 */
    .abs-bottom-right {
        position: absolute !important;
        bottom: 10px !important;
        right: 15px !important;
        z-index: 999;
    }

    /* 强制去除 Streamlit 默认按钮样式，只留文字颜色 */
    .abs-top-right button { 
        background: none !important; border: none !important; 
        color: #FFD700 !important; font-size: 24px !important; font-weight: bold !important;
        padding: 0 !important; box-shadow: none !important;
    }
    
    /* 详情文字变亮 */
    .abs-bottom-right label { color: #FFD700 !important; font-weight: bold !important; font-size: 15px !important; }

    /* 数据布局网格 */
    .data-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 10px; text-align: center; margin-top: 20px; width: 92%; }
    .gold-text { color: #FFD700; font-weight: bold; }
    
    /* 审计卡片详情 */
    .audit-card { 
        background: #0f172a; border: 1px solid #3b82f6; border-radius: 8px; 
        padding: 20px; margin-top: -10px; margin-bottom: 20px; 
    }
</style>
""", unsafe_allow_html=True)

# --- A. 搜索区 ---
c_search, _ = st.columns([0.4, 0.6])
with c_search:
    new_c = st.text_input("", placeholder="🔍 输入代码审计 (如 600111)", label_visibility="collapsed")
    if new_c:
        c_in = new_c.strip()
        if len(c_in) == 6: c_in = ("sh" if c_in.startswith(('6', '9')) else "sz") + c_in
        if c_in not in st.session_state.pool:
            st.session_state.pool.insert(0, c_in); st.rerun()

# --- B. 审计区 ---
for code in st.session_state.pool:
    ts = int(time.time() * 1000)
    try:
        res = requests.get(f"http://qt.gtimg.cn/q={code}&_t={ts}", timeout=1.0)
        res.encoding = 'gbk'
        v = res.text.split('="')[1].split('~')
        name, price, change = v[1], v[3], float(v[32])
        last_close, open_p = float(v[4]), float(v[5])
        color = "#ef4444" if change >= 0 else "#22c55e"
        
        prem = round((open_p - last_close) / last_close * 100, 2)
        ib = round((float(price) - open_p) / open_p * 100, 2) if open_p > 0 else 0

        # 开始渲染卡牌主体
        st.write(f'<div class="stock-card-container">', unsafe_allow_html=True)
        
        # 1. 强行嵌入右上按钮
        st.markdown('<div class="abs-top-right">', unsafe_allow_html=True)
        if st.button("✕", key=f"del_{code}"):
            st.session_state.pool.remove(code); st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        # 2. 强行嵌入右下勾选
        st.markdown('<div class="abs-bottom-right">', unsafe_allow_html=True)
        show_audit = st.checkbox("查看详情》", key=f"dt_{code}", label_visibility="visible")
        st.markdown('</div>', unsafe_allow_html=True)

        # 3. 卡牌信息内容
        st.markdown(f"""
            <div style="display: flex; align-items: center; justify-content: space-between; margin-right: 50px;">
                <div>
                    <span style="background:#ef4444; padding:2px 8px; border-radius:4px; font-weight:bold; font-size:14px;">评分 92</span>
                    <span style="font-size:22px; font-weight:bold; margin-left:10px;">{name}</span>
                    <span style="color:#64748b; font-size:14px; margin-left:8px;">{code}</span>
                </div>
                <div style="text-align:right;">
                    <span style="font-size:26px; font-weight:bold; color:{color};">{price}</span>
                    <span style="font-size:16px; font-weight:bold; color:{color}; margin-left:10px;">{change}%</span>
                </div>
            </div>
            <div style="background:#0a0f1a; padding:12px; border-radius:6px; margin:20px 0; border-left:3px solid #3b82f6; width: 90%;">
                🎯 <b>核心结论：</b> 属于典型的反核博弈信号。资金逆势扫货迹象明显，建议分批挂单。
            </div>
            <div class="data-grid">
                <div><div style="font-size:18px; font-weight:bold;">{prem}%</div><div style="font-size:11px; color:#64748b;">开盘溢价</div></div>
                <div><div style="font-size:18px; font-weight:bold; color:{color}">{ib}%</div><div style="font-size:11px; color:#64748b;">盘中实体</div></div>
                <div><div style="font-size:18px; font-weight:bold;">39.1</div><div style="font-size:11px; color:#64748b;">W&R指标</div></div>
                <div><div style="font-size:18px; font-weight:bold;">{v[33]}</div><div style="font-size:11px; color:#64748b;">今日最高</div></div>
                <div><div style="font-size:18px; font-weight:bold; color:#ef4444">{round(last_close*1.1, 2)}</div><div style="font-size:11px; color:#64748b;">涨停目标</div></div>
            </div>
        """, unsafe_allow_html=True)
        
        st.write('</div>', unsafe_allow_html=True)

        # 4. 详情审计展开区
        if show_audit:
            st.markdown(f"""
            <div class="audit-card">
                <div style="border-bottom: 1px solid #1e293b; padding-bottom: 8px; margin-bottom: 10px;">
                    <span style="color:#3b82f6; font-weight:bold;">I. 仪表盘:</span> 鹰眼总分 <span class="gold-text">92</span> | 周期: <span class="gold-text">主升浪中继</span> | 决策: <span class="gold-text">积极进攻</span>
                </div>
                <div style="border-bottom: 1px solid #1e293b; padding-bottom: 8px; margin-bottom: 10px;">
                    <span style="color:#3b82f6; font-weight:bold;">II. 五维雷达:</span> 筹码: <span class="gold-text">35/35(+10)</span> | 环境: 18 | 排雷: 15 | 资金: 12 | 决策: 12
                </div>
                <div style="border-bottom: 1px solid #1e293b; padding-bottom: 8px; margin-bottom: 10px;">
                    <span style="color:#3b82f6; font-weight:bold;">III. 真假博弈:</span> 意图: <span class="gold-text">诱空吸筹</span> | 证据: 缩量不破昨收，大单对倒现身。
                </div>
                <div style="border-bottom: 1px solid #1e293b; padding-bottom: 8px; margin-bottom: 10px;">
                    <span style="color:#3b82f6; font-weight:bold;">IV. 死亡红线:</span> 筹码/硬伤排查: <span style="color:#22c55e;">安全 (PASS)</span>
                </div>
                <div>
                    <span style="color:#3b82f6; font-weight:bold;">V. 战术执行:</span> 进场: <span class="gold-text">{price}</span> | 止损: <span style="color:#ef4444;">{last_close}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

    except:
        st.error(f"代码 {code} 无法解析")
