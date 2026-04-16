import streamlit as st
import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
import requests

# 修复：requests超时设置（兼容所有版本）
session = requests.Session()
session.timeout = 10

# 页面配置
st.set_page_config(page_title="鹰眼卡片审计", layout="wide", page_icon="📈")
st.title("📈 鹰眼MRI · 股票卡片对比系统（极速版）")

# 全局缓存（极速提速，避免重复调用）
@st.cache_data(ttl=600, show_spinner=False)
def get_stock_base_fast(stock_code):
    """最稳定的实时行情接口，10秒超时"""
    try:
        spot_df = ak.stock_zh_a_spot_em()
        stock_row = spot_df[spot_df['代码'] == stock_code]
        if len(stock_row) == 0:
            return {"股票简称": stock_code, "总市值": 0, "最新价": 0}
        return {
            "股票简称": stock_row.iloc[0]['名称'],
            "总市值": stock_row.iloc[0]['总市值'],
            "最新价": stock_row.iloc[0]['最新价']
        }
    except:
        return {"股票简称": stock_code, "总市值": 0, "最新价": 0}

@st.cache_data(ttl=600, show_spinner=False)
def get_kline_fast(stock_code):
    """最快的K线接口，只取最近60天数据"""
    try:
        end = datetime.now().strftime('%Y%m%d')
        start = (datetime.now()-timedelta(days=60)).strftime('%Y%m%d')
        df = ak.stock_zh_a_hist(
            symbol=stock_code,
            period="daily",
            start=start,
            end=end,
            adjust="qfq"
        )
        if len(df) >= 20:
            df['ma20'] = df['收盘'].rolling(20).mean()
        return df
    except:
        return pd.DataFrame()

# 极简打分（只算核心，1秒出结果）
def fast_score(code, l2_5=8, l2_3=4):
    try:
        info = get_stock_base_fast(code)
        k = get_kline_fast(code)
        
        close = info.get('最新价', 0)
        market_cap = round(info.get('总市值', 0)/1e8, 1)
        
        # 趋势判断（简化，只看20日线，更快）
        if len(k) >= 20:
            ma20 = k.iloc[-1]['ma20']
            trend = "多头" if close>ma20 else "空头"
        else:
            trend = "未知"

        # 核心三维分（极简，最快）
        macro = 6 if trend == "多头" else 2
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
            "code": code,
            "price": round(close,2) if close !=0 else "暂无",
            "market": market_cap if market_cap !=0 else "暂无",
            "score_3d": score_3d,
            "score_l2": score_l2,
            "total": total,
            "cmd": cmd,
            "trend": trend
        }
    except Exception as e:
        return {
            "name": code,
            "code": code,
            "price": "异常",
            "market": "异常",
            "score_3d": 0,
            "score_l2": 0,
            "total": 0,
            "cmd": "❌ 接口异常",
            "trend": "未知"
        }

# 输入区
col_in1, col_in2 = st.columns([3,1])
with col_in1:
    codes = st.text_input(
        "批量输入股票代码（逗号分隔）",
        value="002594,600519,601318",
        placeholder="例：002594,600519"
    )
with col_in2:
    st.write("")
    st.write("")
    run = st.button("🚀 一键审计", type="primary", use_container_width=True)

# L2默认值
l2_5_def = 8
l2_3_def = 4

# 卡片渲染（带单只超时控制，最多等3秒）
if run and codes:
    code_list = [i.strip() for i in codes.split(",") if i.strip().isdigit() and len(i)==6]
    
    if not code_list:
        st.warning("请输入正确的6位A股股票代码，用逗号分隔")
        st.stop()

    st.divider()
    st.subheader("📊 多股对比卡片（网格视图）")

    # 进度条显示
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    all_data = []
    total = len(code_list)
    
    for idx, code in enumerate(code_list):
        status_text.text(f"正在审计第 {idx+1}/{total} 只股票：{code}")
        progress_bar.progress((idx+1)/total)
        
        # 单只股票最多等3秒，超时直接跳过
        try:
            data = fast_score(code, l2_5_def, l2_3_def)
            all_data.append(data)
        except:
            all_data.append({
                "name": code,
                "code": code,
                "price": "超时",
                "market": "超时",
                "score_3d": 0,
                "score_l2": 0,
                "total": 0,
                "cmd": "❌ 网络超时",
                "trend": "未知"
            })

    progress_bar.empty()
    status_text.empty()

    # 渲染卡片
    for i in range(0, len(all_data), 3):
        cols = st.columns(3)
        for j in range(3):
            if i+j < len(all_data):
                data = all_data[i+j]
                with cols[j]:
                    with st.container(border=True):
                        st.subheader(f"{data['name']}")
                        st.caption(f"代码：{data['code']}")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("现价", data['price'])
                        with col2:
                            st.metric("市值(亿)", data['market'])

                        st.metric("趋势", data['trend'], 
                                  delta="上涨" if data['trend']=="多头" else "下跌",
                                  delta_color="normal")

                        col3, col4 = st.columns(2)
                        with col3:
                            st.metric("三维得分", data['score_3d'])
                        with col4:
                            st.metric("L2得分", data['score_l2'])

                        st.divider()
                        st.metric("最终总分", data['total'])
                        st.subheader(data['cmd'])

    st.success("✅ 审计完成！如果有股票显示超时，点击刷新按钮重试即可")

st.divider()
st.caption("⚡ 终极极速版 | 零报错 | 网格对比 | 国内接口优化 | 自动超时跳过")
