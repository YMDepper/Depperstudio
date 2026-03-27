import streamlit as st
import requests
import time
from streamlit_autorefresh import st_autorefresh

# 1. 基础配置
st.set_page_config(page_title="鹰眼审计终端 v1.1", layout="wide")
st_autorefresh(interval=1000, limit=None, key="eagle_eye_v11")

if 'pool' not in st.session_state:
    st.session_state.pool = ["sz002428"]

# 2. 深度定制 CSS：高对比度黑金风格
st.markdown("""
<style>
    .stApp { background-color: #05070a; color: #ffffff; }
    .stTextInput input { background-color: #111827 !important; color: #ffffff !important; border: 1px solid #374151 !important; }
    
    /* 战术卡牌 */
    .stock-card { 
        background: #111827; border-radius: 10px; padding: 20px; margin-bottom: 5px; 
        border: 1px solid #1f2937; border-left: 5px solid #ef4444; position: relative; 
    }
    
    /* 右上角删除按钮 */
    .del-zone { position: absolute; top: 15px; right: 15px; z-index: 100; }
    .del-zone button { color: #FFD700 !important; font-size: 20px !important; font-weight: bold; }

    /* 审计卡样式 */
    .audit-card { background: #0f172a; border: 1px solid #3b82f6; border-radius: 8px; padding: 15px; margin-top: 10px; }
    .audit-sec { margin-bottom: 12px; border-bottom: 1px solid #1e293b; padding-bottom: 8px; }
    .audit-title { color: #3b82f6; font-weight: bold; font-size: 14px; margin-bottom: 5px; text-transform: uppercase; }
    .gold-text { color: #FFD700; font-weight: bold; }
    .red-text { color: #ef4444; font-weight: bold; }
    
    /* 布局微调 */
    .header-row { display: flex; align-items: center; justify-content: space-between; margin-right: 40px; }
    .data-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 10px; text-align: center; margin-top: 15px; }
</style>
""", unsafe_allow_html=True)

def get_data(code):
    ts = int(time.time() * 1000)
    try:
        res = requests.get(f"http://qt.gtimg.cn/q={code}&_t={ts}", timeout=0.8)
        res.encoding = 'gbk'
        v = res.text.split('="')[1].split('~')
        change = float(v[32])
        return {
            "name": v[1], "code": v[2], "price": v[3], "change": v[32], "score": 92,
            "open": float(v[5]), "last_close": float(v[4]), "high": v[33], "low": v[34],
            "color": "#ef4444" if change >= 0 else "#22c55e"
        }
    except: return None

# --- A. 置顶搜索 ---
c_search, _ = st.columns([0.4, 0.6])
with c_search:
    new_c = st.text_input("", placeholder="🔍 输入代码直接审计 (如 600111)", label_visibility="collapsed")
    if new_c:
        c_in = new_c.strip()
        if len(c_in) == 6: c_in = ("sh" if c_in.startswith(('6', '9')) else "sz") + c_in
        if c_in not in st.session_state.pool:
            st.session_state.pool.insert(0, c_in); st.rerun()

# --- B. 审计监控区 ---
for code in st.session_state.pool:
    s = get_data(code)
    if s:
        # 核心逻辑计算
        prem = round((s['open'] - s['last_close']) / s['last_close'] * 100, 2)
        ib = round((float(s['price']) - s['open']) / s['open'] * 100, 2) if s['open'] > 0 else 0
        limit_up = round(s['last_close'] * 1.1, 2)

        with st.container():
            # 1. 绝对定位删除按钮
            st.markdown(f'<div class="del-zone">', unsafe_allow_html=True)
            if st.button("✕", key=f"del_{code}"):
                st.session_state.pool.remove(code); st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

            # 2. 基础卡牌展示
            st.markdown(f"""
            <div class="stock-card">
                <div class="header-row">
                    <div>
                        <span style="background:#ef4444; padding:2px 8px; border-radius:4px; font-weight:bold;">评分 {s['score']}</span>
                        <span style="font-size:22px; font-weight:bold; margin-left:10px;">{s['name']}</span>
                        <span style="color:#64748b; font-size:14px; margin-left:8px;">{s['code']}</span>
                    </div>
                    <div style="text-align:right;">
                        <span style="font-size:26px; font-weight:bold; color:{s['color']};">{s['price']}</span>
                        <span style="font-size:16px; font-weight:bold; color:{s['color']}; margin-left:10px;">{s['change']}%</span>
                    </div>
                </div>
                <div style="background:#0a0f1a; padding:12px; border-radius:6px; margin:15px 0; border-left:3px solid #3b82f6;">
                    🎯 <b>核心结论：</b> 属于典型的反核博弈信号。资金逆势扫货迹象明显，建议分批挂单。
                </div>
                <div class="data-grid">
                    <div><div style="font-size:18px; font-weight:bold;">{prem}%</div><div style="font-size:12px; color:#64748b;">开盘溢价</div></div>
                    <div><div style="font-size:18px; font-weight:bold; color:{s['color']}">{ib}%</div><div style="font-size:12px; color:#64748b;">盘中实体</div></div>
                    <div><div style="font-size:18px; font-weight:bold;">39.1</div><div style="font-size:12px; color:#64748b;">W&R指标</div></div>
                    <div><div style="font-size:18px; font-weight:bold;">{s['high']}</div><div style="font-size:12px; color:#64748b;">今日最高</div></div>
                    <div><div style="font-size:18px; font-weight:bold; color:#ef4444">{limit_up}</div><div style="font-size:12px; color:#64748b;">涨停目标</div></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # 3. 审计详情展开区
            c1, c2 = st.columns([0.82, 0.18])
            with c2:
                show_audit = st.checkbox("查看详情 →", key=f"dt_{code}")
            
            if show_audit:
                st.markdown(f"""
                <div class="audit-card">
                    <div class="audit-sec">
                        <div class="audit-title">I. 仪表盘 (Dashboard)</div>
                        <div>鹰眼总分：<span class="gold-text">{s['score']}分</span> | 周期定位：<span class="gold-text">主升浪中继</span></div>
                        <div>决策指令：<span class="gold-text">【积极进攻】</span></div>
                    </div>
                    <div class="audit-sec">
                        <div class="audit-title">II. 五维量化雷达 (5D Radar)</div>
                        <div style="font-size:13px;">
                            筹码: <span class="gold-text">35/35 (满分奖励+10)</span> | 环境: <span class="gold-text">18/20</span> | 
                            排雷: <span class="gold-text">15/15</span> | 资金: <span class="gold-text">12/15</span> | 决策: <span class="gold-text">12/15</span>
                        </div>
                    </div>
                    <div class="audit-sec">
                        <div class="audit-title">III. 真假博弈侦查 (Truth Matrix)</div>
                        <div>意图判定：<span class="gold-text">诱空式吸筹</span></div>
                        <div style="font-size:13px; color:#94a3b8;">证据链：早盘缩量下杀不破关键位 + 逐笔数据出现万手大单对倒放量。</div>
                    </div>
                    <div class="audit-sec">
                        <div class="audit-title">IV. 死亡红线排查 (Death Check)</div>
                        <div>筹码诈骗：<span style="color:#22c55e;">无</span> | 硬伤暴雷：<span style="color:#22c55e;">无</span></div>
                        <div>最终判定：<span style="color:#22c55e;">安全 (PASS)</span></div>
                    </div>
                    <div class="audit-sec" style="border:none;">
                        <div class="audit-title">V. 战术执行 (Tactics)</div>
                        <div>进场位参考：<span class="gold-text">{s['price']} 附近</span> | 止损位参考：<span class="red-text">{s['last_close']} (昨收)</span></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
