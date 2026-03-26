import streamlit as st
import requests
import pandas as pd

# ---------------------------------------------------------
# 【核心配置区】在此处直接修改你永远想关注的股票代码
# ---------------------------------------------------------
MY_DEFAULT_STOCKS = "sh600519,sz000001,sz002594" # 你可以把这里改成你的持仓，如 "sh600000,sz000002"
# ---------------------------------------------------------

st.set_page_config(page_title="破军·鹰眼系统3.0", page_icon="🎯", layout="wide")

# 极简黑白灰风格 CSS
st.markdown("""
    <style>
    .reportview-container { background: #ffffff; }
    .stMetric { border: 1px solid #f0f0f0; padding: 15px; border-radius: 5px; background: #fafafa; }
    div.stButton > button { width: 100%; border-radius: 5px; height: 3em; background-color: #f0f2f6; }
    .logic-card { padding: 20px; border-radius: 10px; margin-bottom: 10px; border-left: 8px solid; box-shadow: 2px 2px 5px rgba(0,0,0,0.05); }
    .buy { border-left-color: #ff4b4b; background-color: #fff5f5; } /* A股红涨 */
    .sell { border-left-color: #28a745; background-color: #f6fff6; } /* A股绿跌 */
    .wait { border-left-color: #cccccc; background-color: #f8f9fa; }
    </style>
    """, unsafe_allow_html=True)

# 侧边栏：策略参数（逻辑2的体现）
with st.sidebar:
    st.header("🎯 战略参数设定")
    # 逻辑核心：周线与日线的博弈位
    weekly_trend = st.slider("周线战略支撑位 (%)", -20.0, 0.0, -10.0)
    daily_chip = st.slider("日线筹码密集区 (%)", -10.0, 0.0, -3.0)
    stop_loss = st.slider("风控止损强制线 (%)", -15.0, 0.0, -7.0)
    
    st.divider()
    codes_input = st.text_area("✍️ 临时修改监控池 (逗号分隔)", MY_DEFAULT_STOCKS)
    st.info("💡 提示：若想永久修改默认股票，请修改代码第11行。")

# 高速抓取函数
def get_live_data(codes):
    if not codes: return []
    try:
        url = f"http://qt.gtimg.cn/q={codes.replace(' ', '')}"
        res = requests.get(url, timeout=2)
        res.encoding = 'gbk'
        data = []
        for line in res.text.split(';'):
            if len(line) < 50: continue
            parts = line.split('~')
            data.append({
                "name": parts[1], "code": parts[2], "price": float(parts[3]),
                "change": float(parts[32]), "high": float(parts[33]), "low": float(parts[34]),
                "volume": float(parts[37]), "turnover": float(parts[38])
            })
        return data
    except: return []

# 主界面渲染
st.title("🎯 破军·鹰眼战略终端")
st.caption("基于：周线战略定性 + 日线筹码定量 + 主力反人性推演")

stocks = get_live_data(codes_input)

if stocks:
    # 第一排：核心行情
    cols = st.columns(len(stocks))
    for i, s in enumerate(stocks):
        with cols[i]:
            # A股习惯：涨显示红色(normal)，跌显示绿色(inverse)
            color = "normal" if s['change'] >= 0 else "inverse"
            st.metric(s['name'], f"¥{s['price']}", f"{s['change']}%", delta_color=color)

    st.divider()

    # 第二排：鹰眼逻辑看板
    st.subheader("🔍 实时博弈推演")
    for s in stocks:
        change = s['change']
        
        # 核心逻辑结合（逻辑2+3）
        if change <= stop_loss:
            style, status, advice = "buy", "🛑 趋势破位", "已击穿风控底线。主力可能已完成阶段性收割，建议执行坚决风控，保留筹码。"
        elif change <= weekly_trend:
            style, status, advice = "buy", "💎 周线战略区", "触及周线级别大支撑。此处为长线反博弈点，主力大概率在此洗盘接筹，建议分批加仓。"
        elif change <= daily_chip:
            style, status, advice = "buy", "📈 日线筹码位", "进入日线筹码密集区，符合‘仓位滚动法’买入逻辑。观察换手率是否缩量。"
        else:
            style, status, advice = "wait", "⚖️ 均衡波动", "目前处于博弈真空期。建议保持原有仓位不动，等待参数触碰。"
        
        # A股配色修正：跌的时候（买点）显示醒目颜色
        card_color = "buy" if change < 0 else "wait"

        st.markdown(f"""
            <div class="logic-card {card_color}">
                <div style="display:flex; justify-content:space-between;">
                    <span style="font-size:1.2em; font-weight:bold;">{s['name']} ({s['code']})</span>
                    <span style="font-weight:bold; color:{'#ff4b4b' if change >=0 else '#28a745'}">{status}</span>
                </div>
                <div style="margin-top:10px; font-size:0.95em; color:#444;">
                    <b>分析报告：</b>{advice}<br/>
                    <small>关键数据：换手 {s['turnover']}% | 今日振幅 {round(s['high']-s['low'], 2)}</small>
                </div>
            </div>
        """, unsafe_allow_html=True)
else:
    st.error("数据连接超时或代码格式错误。")

if st.button("🔄 立即同步最新行情"):
    st.rerun()
