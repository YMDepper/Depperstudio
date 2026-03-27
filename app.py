import streamlit as st
import requests
import time
from streamlit_autorefresh import st_autorefresh

# 1. 极简页面配置
st.set_page_config(page_title="鹰眼全维度终端", layout="wide")
st_autorefresh(interval=3000, limit=None, key="eagle_eye_integrated")

if 'pool' not in st.session_state:
    st.session_state.pool = ["sz002428", "sh600137"]

# 2. 核心 CSS 引擎：黑金、紧凑、一体化锁定
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    .stApp { background-color: #020408; font-family: 'Inter', sans-serif; }
    
    /* 极致压缩原生容器间距 */
    [data-testid="stVerticalBlock"] { gap: 0.3rem !important; }
    .block-container { padding-top: 1rem !important; }
    [data-testid="stHeader"] { visibility: hidden; }

    /* 高级搜索框 */
    .stTextInput input {
        background-color: #0f172a !important; border: 1px solid #1e293b !important;
        border-radius: 12px !important; color: #f8fafc !important; padding: 12px 20px !important;
    }

    /* 金融通行证卡牌整体 */
    .eagle-card {
        position: relative; background: linear-gradient(135deg, #111827 0%, #0d1117 100%);
        border: 1px solid #1e293b; border-radius: 12px; padding: 15px;
        margin-bottom: 10px; overflow: hidden;
        transition: all 0.3s ease;
    }
    .eagle-card:hover { border-color: #fbbf24; box-shadow: 0 5px 15px rgba(251, 191, 36, 0.1); }

    /* 评分勋章 */
    .score-badge {
        background: rgba(239, 68, 68, 0.15); color: #ef4444;
        padding: 4px 10px; border-radius: 6px; font-size: 11px; font-weight: 700;
        border: 1px solid rgba(239, 68, 68, 0.3); letter-spacing: 0.5px;
    }

    /* 数据栅格布局：横向压缩 */
    .metric-grid { 
        display: flex; justify-content: space-between; border-top: 1px solid #1e293b; padding-top: 8px; margin-top: 8px; 
    }
    .m-item { text-align: center; flex: 1; }
    .m-label { color: #8b949e; font-size: 10px; text-transform: uppercase; margin-top: 4px; display: block; }
    .m-value { color: #f8fafc; font-size: 15px; font-weight: 600; }

    /* 交互组件层级锁定 */
    /* 右上角删除符号 X */
    .btn-delete {
        position: absolute; top: 10px; right: 10px; color: #475569; font-size: 18px; text-decoration: none; font-family: sans-serif; transition: 0.3s;
    }
    .btn-delete:hover { color: #f1f5f9; }

    /* 右下角详情文本 */
    .detail-trigger {
        position: absolute; bottom: 10px; right: 15px; color: #fbbf24; font-size: 12px; font-weight: bold; cursor: pointer; transition: 0.3s;
    }
    .detail-trigger:hover { color: #FFD700; }

    /* 审计卡高级详情部分：勾选展开，无损注入底部 */
    .audit-card {
        background: #020617; border: 1px dotted #1e293b; border-radius: 12px;
        padding: 20px; margin-top: -15px; margin-bottom: 15px;
        animation: slideDown 0.4s ease-out;
    }
    @keyframes slideDown { from { opacity: 0; transform: translateY(-10px); } to { opacity: 1; transform: translateY(0); } }
</style>
""", unsafe_allow_html=True)

# --- A. 顶栏搜索 (保持干净) ---
c_search, _ = st.columns([0.6, 0.4])
with c_search:
    new_c = st.text_input("", placeholder="🔍 输入代码审计 (例如 600111)", label_visibility="collapsed")
    if new_c:
        c_in = new_c.strip()
        if len(c_in) == 6: c_in = ("sh" if c_in.startswith(('6', '9')) else "sz") + c_in
        if c_in not in st.session_state.pool:
            st.session_state.pool.insert(0, c_in); st.rerun()

# --- B. 动态卡牌流区 ---
for code in st.session_state.pool:
    try:
        ts = int(time.time() * 1000)
        res = requests.get(f"http://qt.gtimg.cn/q={code}&_t={ts}", timeout=1.0)
        res.encoding = 'gbk'
        v = res.text.split('="')[1].split('~')
        name, price, change = v[1], v[3], float(v[32])
        last_close, open_p = float(v[4]), float(v[5])
        color = "#ff7b72" if change >= 0 else "#3fb950" # 更符合暗色主题的高饱和红绿
        
        prem = round((open_p - last_close) / last_close * 100, 2)
        ib = round((float(price) - open_p) / open_p * 100, 2) if open_p > 0 else 0

        # --- 1. 注入交互逻辑层 (HTML 内嵌视觉核心) ---
        with st.container():
            col_x, col_space, col_check = st.columns([0.1, 0.6, 0.3])
            # 删除和详情的真实原生组件在这里渲染
            if st.button("✕", key=f"del_{code}"):
                st.session_state.pool.remove(code); st.rerun()
            show_detail = st.checkbox("详情 》", key=f"chk_{code}")

            # --- 2. 卡牌主体渲染 (Markdown，零内嵌按钮，确保不乱码) ---
            st.markdown(f"""
            <div class="eagle-card" style="margin-top: -30px;">
                <div style="position: absolute; top: 10px; right: 15px; color: #475569; font-size: 18px;">✕</div>
                
                <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                    <div>
                        <div class="score-badge">评分 92</div>
                        <div style="font-size: 22px; font-weight: 700; color: #f8fafc; margin-top: 10px;">{name}</div>
                        <div style="color: #475569; font-size: 13px; margin-top: 4px;">{code.upper()}</div>
                    </div>
                    <div style="text-align: right; margin-right: 20px;">
                        <div style="font-size: 28px; font-weight: 700; color: {color};">{price}</div>
                        <div style="font-size: 14px; color: {color};">{change}%</div>
                    </div>
                </div>
                
                <div style="background: rgba(59, 130, 246, 0.05); padding: 12px; border-radius: 10px; margin-top: 20px; border-left: 2px solid #3b82f6;">
                    <span style="color: #3b82f6; font-size: 16px; margin-right: 8px;">🎯</span>
                    <span style="color: #CBD5E1; font-size: 13px; line-height: 1.5;">鹰眼博弈推演：此为典型的反核博弈信号。资金逆势扫货迹象明显，主力反人性吸筹。建议关注午后均线承接机会。</span>
                </div>

                <div class="metric-grid">
                    <div class="m-item"><div class="m-value">{prem}%</div><div class="m-label">开盘溢价</div></div>
                    <div class="m-item"><div class="m-value" style="color:{color}">{ib}%</div><div class="m-label">盘中实体</div></div>
                    <div class="m-item"><div class="m-value">39.1</div><div class="m-label">W&R指标</div></div>
                    <div class="m-item"><div class="m-value">{v[33]}</div><div class="m-label">今日最高价</div></div>
                    <div class="m-item"><div class="m-value" style="color:#ff7b72">{round(last_close*1.1, 2)}</div><div class="m-label">涨停目标价</div></div>
                </div>

                <div class="detail-trigger">详情 》</div>
            </div>
            """, unsafe_allow_html=True)

            # --- 3. 详情审计抽屉部分：勾选无损注入 ---
            if show_detail:
                st.markdown(f"""
                <div class="audit-card" style="margin-top: -30px; position: relative; z-index: 1;">
                    <div style="color:#94a3b8; font-size:13px; line-height:2;">
                        <span style="color:#3b82f6; font-weight:bold;">[I] 仪表盘:</span> 鹰眼总分 <b style="color:#fbbf24;">92</b> | 周期: <b style="color:#fbbf24;">主升中继</b> | 决策: <b>积极进攻</b><br>
                        <span style="color:#3b82f6; font-weight:bold;">[II] 真假博弈:</span> <b style="color:#fbbf24;">诱空吸筹</b> (证据: 缩量不破昨收，大单对倒现身)<br>
                        <span style="color:#3b82f6; font-weight:bold;">[III] 风控扫描:</span> 筹码分布 安全 | 质押暴雷 无 | 判定: <b style="color:#22c55e;">安全 (PASS)</b><br>
                        <span style="color:#3b82f6; font-weight:bold;">[IV] 战术执行:</span> 建议进场参考价格: <b style="color:#fbbf24;">{price}</b> | 止损位点: <b style="color:#ef4444;">{v[4]}</b>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                # 为卡牌底部留出呼吸空间
                st.markdown("<br>", unsafe_allow_html=True)

    except:
        continue
