import streamlit as st
import requests
import pandas as pd
import numpy as np

# 1. 页面极简专业配置
st.set_page_config(page_title="鹰眼作战终端", layout="wide")

# 2. 注入 CSS：打造“卡牌”与“云图”视觉
st.markdown("""
    <style>
    .stApp { background-color: #f4f7f6; }
    .index-bar { background: white; padding: 15px; border-radius: 10px; margin-bottom: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); }
    .stock-card { 
        background: white; border-radius: 12px; padding: 20px; 
        border-top: 5px solid #ccc; box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        margin-bottom: 15px;
    }
    .metric-box { text-align: center; border-right: 1px solid #eee; }
    .score-val { font-size: 24px; font-weight: bold; }
    .wr-tag { font-size: 12px; padding: 2px 5px; border-radius: 3px; background: #eee; }
    </style>
    """, unsafe_allow_html=True)

# --- 数据抓取核心 ---
def get_data(codes):
    if not codes: return []
    # A50期货、上证、深证固定代码
    fixed = ["sh000001", "sz399001", "sh510100"] 
    all_codes = list(dict.fromkeys(fixed + codes))
    url = f"http://qt.gtimg.cn/q={','.join(all_codes)}"
    try:
        res = requests.get(url, timeout=2)
        res.encoding = 'gbk'
        results = []
        for line in res.text.strip().split(';'):
            if '="' not in line: continue
            v = line.split('=')[1].strip('"').split('~')
            if len(v) < 40: continue
            results.append({
                "name": v[1], "code": v[2], "price": float(v[3]),
                "change": float(v[32]), "high": float(v[33]), "low": float(v[34]),
                "volume": float(v[37]), "turnover": float(v[38]),
                "last_close": float(v[4])
            })
        return results
    except: return []

# --- 鹰眼逻辑：W&R 与 筹码模拟 ---
def analyze_logic(s):
    # 模拟 W&R (14日简化版：用当日最高最低价计算超买超卖)
    # W&R = (Hn - C) / (Hn - Ln) * 100
    range_val = (s['high'] - s['low'])
    wr = round((s['high'] - s['price']) / range_val * 100, 2) if range_val != 0 else 50
    
    # 评分逻辑
    score = 60
    advice = "中性观望"
    if wr > 80: score += 15; advice = "超跌博弈区"
    if s['change'] < -3: score += 10; advice = "筹码回踩区"
    if s['turnover'] < 1.5: score += 5; advice += " (缩量)"
    
    # 颜色判定
    color = "#f21b2b" if score >= 75 else ("#00a800" if score <= 40 else "#666")
    return score, wr, advice, color

# --- 主界面布局 ---

# A. 快捷添加区域 (页面顶部)
st.title("🦅 鹰眼作战终端")
c1, c2 = st.columns([4, 1])
with c1:
    new_stock = st.text_input("", placeholder="🔍 直接输入股票代码添加 (如 002428)", label_visibility="collapsed")
with c2:
    if st.button("🚀 实时挂载", use_container_width=True):
        if 'pool' not in st.session_state: st.session_state.pool = []
        if new_stock:
            c = new_stock.strip()
            if len(c) == 6 and c.isdigit():
                c = f"sh{c}" if c.startswith(('6', '9')) else f"sz{c}"
            st.session_state.pool.insert(0, c)
            st.session_state.pool = list(dict.fromkeys(st.session_state.pool))
            st.rerun()

# B. 固定指数栏
data = get_data(st.session_state.get('pool', []))
if data:
    idx_data = data[:3]
    stocks_data = data[3:]
    
    cols = st.columns(3)
    idx_names = ["上证指数", "深证成指", "富时A50"]
    for i, s in enumerate(idx_data):
        with cols[i]:
            c_color = "#f21b2b" if s['change'] >= 0 else "#00a800"
            st.markdown(f"""
                <div class="index-bar">
                    <div style="color:#666; font-size:14px;">{idx_names[i]}</div>
                    <div style="color:{c_color}; font-size:22px; font-weight:bold;">{s['price']} <small>{s['change']}%</small></div>
                </div>
            """, unsafe_allow_html=True)

    # C. 大盘云图简易版 (用色块代表近期热度)
    st.markdown("##### 💹 实时博弈热力图")
    # 模拟板块热力
    hot_cols = st.columns(6)
    sectors = [("半导体", 2.5), ("低空经济", -1.2), ("有色金属", 3.8), ("白酒", -0.5), ("医药", 1.1), ("电力", -2.1)]
    for i, (name, val) in enumerate(sectors):
        bg = "#ffebee" if val > 0 else "#e8f5e9"
        tc = "#f44336" if val > 0 else "#4caf50"
        hot_cols[i].markdown(f"<div style='background:{bg}; color:{tc}; padding:10px; border-radius:5px; text-align:center; font-size:12px;'>{name}<br><b>{val}%</b></div>", unsafe_allow_html=True)

    st.markdown("---")

    # D. 股票“体检卡牌”
    st.subheader("📋 监控池深度扫描")
    for s in stocks_data:
        score, wr, advice, color = analyze_logic(s)
        
        with st.container():
            st.markdown(f"""
                <div class="stock-card" style="border-top-color:{color}">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <div>
                            <span style="font-size:20px; font-weight:bold;">{s['name']}</span> 
                            <small style="color:#999">{s['code']}</small>
                        </div>
                        <div style="color:{color}; font-size:24px; font-weight:bold;">{s['change']}%</div>
                    </div>
                    <div style="display:flex; margin-top:15px; text-align:center;">
                        <div style="flex:1; border-right:1px solid #eee;">
                            <div class="score-val" style="color:{color}">{score}</div>
                            <div style="font-size:12px; color:#999;">鹰眼评分</div>
                        </div>
                        <div style="flex:1; border-right:1px solid #eee;">
                            <div style="font-size:18px; font-weight:bold;">{wr}</div>
                            <div style="font-size:12px; color:#999;">W&R指标</div>
                            <span class="wr-tag">{'超跌' if wr > 80 else ('超买' if wr < 20 else '常态')}</span>
                        </div>
                        <div style="flex:1; border-right:1px solid #eee;">
                            <div style="font-size:18px; font-weight:bold;">{s['turnover']}%</div>
                            <div style="font-size:12px; color:#999;">换手率</div>
                        </div>
                        <div style="flex:1;">
                            <div style="font-size:16px; font-weight:bold; color:{color}">{advice}</div>
                            <div style="font-size:12px; color:#999;">主力博弈推演</div>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

else:
    st.info("监控池为空。请在上方输入代码（如 002428）开启鹰眼扫描。")

# 底部刷新
if st.button("🔄 全局同步行情"):
    st.rerun()
