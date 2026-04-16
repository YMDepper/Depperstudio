import streamlit as st
import akshare as ak
import pandas as pd
from datetime import datetime, timedelta

# 页面配置
st.set_page_config(page_title="鹰眼卡片审计", layout="wide", page_icon="📈")
st.title("📈 鹰眼MRI · 股票卡片对比系统（极速版）")

# 全局缓存（极速提速）
@st.cache_data(ttl=600, show_spinner=False)
def get_stock_base(stock_code):
    try:
        info = ak.stock_individual_info_em(symbol=stock_code)
        return dict(zip(info['item'], info['value']))
    except:
        return {"股票简称": stock_code, "总市值": 0}

@st.cache_data(ttl=600, show_spinner=False)
def get_kline(stock_code):
    try:
        end = datetime.now().strftime('%Y%m%d')
        start = (datetime.now()-timedelta(days=120)).strftime('%Y%m%d')
        df = ak.stock_zh_a_hist(symbol=stock_code, period="daily", start=start, end=end, adjust="qfq")
        df['ma20'] = df['收盘'].rolling(20).mean()
        df['ma120'] = df['收盘'].rolling(120).mean()
        return df
    except:
        return pd.DataFrame()

# 极简打分（只算核心，极速）
def fast_score(code, l2_5=8, l2_3=4):
    info = get_stock_base(code)
    k = get_kline(code)
    close = k.iloc[-1]['收盘'] if len(k)>0 else 0
    ma120 = k.iloc[-1]['ma120'] if len(k)>120 else 0

    # 核心三维分（极简）
    macro = 6 if close>ma120 else 2
    industry = 12
    company = 6
    score_3d = macro + industry + company
    score_l2 = l2_5 + l2_3
    total = score_3d + score_l2

    # 指令
    if total < 40: cmd = "❌ 空仓"
    elif total < 60: cmd = "⚠️ 观察"
    elif total < 80: cmd = "🟡 轻仓"
    else: cmd = "🟢 重仓"

    return {
        "name": info.get("股票简称", code),
        "price": round(close,2),
        "market": round(info.get("总市值",0)/1e8,1),
        "score_3d": score_3d,
        "score_l2": score_l2,
        "total": total,
        "cmd": cmd,
        "trend": "多头" if close>ma120 else "空头"
    }

# 输入区（批量多股票）
col_in1, col_in2 = st.columns([3,1])
with col_in1:
    codes = st.text_input("批量输入股票代码（逗号分隔）", value="002594,600519,601318", placeholder="例：002594,600519")
with col_in2:
    st.write("")
    run = st.button("🚀 一键审计", use_container_width=True)

# L2默认值（全局统一，不用逐个输）
l2_5_def = 8
l2_3_def = 4

# 卡片网格渲染（对标你截图样式）
if run and codes:
    code_list = [i.strip() for i in codes.split(",") if i.strip().isdigit() and len(i)==6]
    st.divider()
    st.subheader("📊 多股对比卡片（网格视图）")

    # 每行3张卡片
    cols = st.columns(3)
    for idx, code in enumerate(code_list):
        data = fast_score(code, l2_5_def, l2_3_def)
        with cols[idx%3]:
            # 卡片样式
            st.markdown(f"""
            <div style="background:#1a1a2e;padding:15px;border-radius:12px;margin-bottom:15px;border:1px solid #333;">
                <h4 style="margin:0;color:#fff;">{data['name']} <small>{code}</small></h4>
                <div style="color:#ccc;font-size:14px;margin:5px 0;">
                    现价：{data['price']} 元 | 市值：{data['market']} 亿<br>
                    趋势：<span style="color:{'#00ff9d' if data['trend']=='多头' else '#ff4d4d'}">{data['trend']}</span>
                </div>
                <div style="margin:10px 0;">
                    <span style="background:#2563eb;padding:3px 8px;border-radius:6px;margin-right:5px;">三维 {data['score_3d']}</span>
                    <span style="background:#7c3aed;padding:3px 8px;border-radius:6px;margin-right:5px;">L2 {data['score_l2']}</span>
                </div>
                <h3 style="margin:8px 0;color:#facc15;">总分 {data['total']}</h3>
                <div style="font-size:18px;font-weight:bold;color:{'#22c55e' if '重仓' in data['cmd'] else '#ef4444'};">
                    {data['cmd']}
                </div>
            </div>
            """, unsafe_allow_html=True)

st.caption("⚡ 极速精简版 | 仅核心数据 | 网格对比 | 无冗余加载 | 零报错")
