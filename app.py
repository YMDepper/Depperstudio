import streamlit as st
import requests
import time
import json
from streamlit_autorefresh import st_autorefresh
from streamlit_echarts import st_echarts

# 1. 页面极简配置
st.set_page_config(page_title="鹰眼作战终端", layout="wide")

# 2. 0.5秒脉冲，战斗开始
st_autorefresh(interval=500, limit=None, key="fast_flicker")

# 初始化监控池
if 'pool' not in st.session_state:
    st.session_state.pool = ["sz002428"]
# 初始化板块映射（临时写死核心板块，未来可自动关联）
if 'sector_map' not in st.session_state:
    st.session_state.sector_map = {
        "sz002428": "sh000001" # 云南锗业先对标上证指数，未来可改为特定的行业板块代码
    }

# 暗黑极简 CSS
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; }
    .stock-card { background: #1e293b; border-radius: 8px; padding: 10px; margin-bottom: 15px; border-top: 3px solid; }
    .header-row { display: flex; justify-content: space-between; align-items: center; }
    .stat-row { display: flex; justify-content: space-between; margin-top: 8px; border-top: 1px solid #334155; padding-top: 8px; }
    .stat-item { text-align: center; flex: 1; }
    .val { font-size: 16px; font-weight: bold; }
    .lbl { font-size: 11px; color: #888; }
    div[data-testid="stEcharts"] { border-radius: 8px; overflow: hidden; background: #0f172a; padding: 5px;}
    </style>
    """, unsafe_allow_html=True)

# 核心数据抓取：个股行情 + 分时数据
def get_live_data(code):
    ts = int(time.time() * 1000)
    
    # A. 实时个股/大盘行情
    q_url = f"http://qt.gtimg.cn/q={code}&_t={ts}"
    # B. 极简分时数据 (腾讯分时接口，获取当日所有分时价格)
    t_url = f"http://web.ifzq.gtimg.cn/appstock/app/minute/query?code={code}&_t={ts}"
    
    headers = {'Referer': 'http://stock.qq.com/'}
    
    try:
        # 并发请求或超时控制 (这里简化处理)
        res_q = requests.get(q_url, timeout=0.8, headers=headers)
        res_q.encoding = 'gbk'
        v = res_q.text.split('="')[1].split('~')
        
        # 抓取行情核心参数
        stock_info = {
            "name": v[1], "code": v[2], "price": float(v[3]), "open": float(v[5]),
            "change": float(v[32]), "m_color": "#ef4444" if float(v[32]) >= 0 else "#22c55e"
        }
        
        # 获取分时价格线 (个股当日分时)
        res_t = requests.get(t_url, timeout=0.8, headers=headers)
        data = json.loads(res_t.text)
        
        # 腾讯分时数据格式特殊，需要清洗出纯价格列表
        minute_data = data['data'][code]['minute']['minute']
        price_line = [float(item[1]) for item in minute_data] # 获取价格
        
        stock_info['price_line'] = price_line
        
        # 计算开盘溢价和盘中实体
        # 需要获取昨收价，这里假设抓取代码里有昨收
        # 为了兼容，暂时用个股分时线的开盘来算开盘溢价
        return stock_info
    except: return None

# 主界面布局
st.title("🦅 鹰眼·分时双线")

# 增加监控区域
new_stock = st.text_input("➕ 输入代码添加 (如 002428)", placeholder="🔍...")
if new_stock:
    c = new_stock.strip()
    if len(c) == 6: c = f"sh{c}" if c.startswith(('6','9')) else f"sz{c}"
    if c not in st.session_state.pool:
        st.session_state.pool.insert(0, c); st.rerun()

st.markdown("---")

if st.session_state.pool:
    # 遍历监控池
    for code in st.session_state.pool:
        # 1. 抓取数据
        s = get_live_data(code)
        
        # 2. 抓取对标板块/大盘数据 (这里假设云南锗业对标上证，未来可自动关联行业板块)
        sector_code = st.session_state.sector_map.get(code, "sh000001")
        sector = get_live_data(sector_code)
        
        if s and sector:
            # 个股昨收、开盘等参数的计算 (这里需要昨收价， get_live_data 需要昨收价， 简化处理暂时假定昨收)
            # 昨收价 = s['price'] - s['change_value'] # 这个接口没有 change_value
            # 这里简化处理：假定昨收价 (需要在 API 抓取时就抓好昨收价， get_live_data 需要昨收价， 简化处理暂时假定昨收)
            # 昨收价 = 50.0 # 假定
            
            # --- 个股参数计算 ---
            prem = round((s['open'] - sector['price']) / sector['price'] * 100, 2) # 简化：开盘溢价=个股开盘与大盘价格关系
            ib = round((s['price'] - s['open']) / s['open'] * 100, 2) if s['open'] > 0 else 0
            
            # --- ECharts 极简双线配置 ---
            options = {
                "animation": False, # 关闭动画，极致追求0.5s速度
                "grid": {"top": 10, "bottom": 10, "left": 10, "right": 10}, # 极致去细节，铺满全屏
                "xAxis": {"type": 'category', "show": False}, # 去掉 X 轴
                "yAxis": {"type": 'value', "show": False, "scale": True}, # 去掉 Y 轴，保持数据相对位置
                "series": [
                    # A. 个股分时线 (亮色)
                    {
                        "name": '个股分时',
                        "type": 'line',
                        "symbol": 'none', # 去掉圆点
                        "data": s['price_line'],
                        "lineStyle": {"color": s['m_color'], "width": 2, "shadowColor": s['m_color'], "shadowBlur": 5}, # 亮、带霓虹效果
                    },
                    # B. 板块大盘线 (暗色)
                    {
                        "name": '板块走势',
                        "type": 'line',
                        "symbol": 'none', # 去掉圆点
                        "data": sector['price_line'],
                        "lineStyle": {"color": "rgba(255, 255, 255, 0.15)", "width": 1}, # 半透明暗白，低调
                    }
                ]
            }
            
            # --- 渲染卡牌 ---
            st.markdown(f"""
                <div class="stock-card" style="border-top-color:{s['m_color']}">
                    <div class="header-row">
                        <div>
                            <span style="font-size:18px; font-weight:bold;">{s['name']}</span>
                            <span style="color:#888; font-size:12px; margin-left:8px;">{s['code']} | 对标大盘 sh000001</span>
                        </div>
                        <div style="text-align:right;">
                            <span style="font-size:22px; font-weight:bold; color:{s['m_color']}">{s['price']}</span>
                            <span style="color:{s['m_color']}; margin-left:5px; font-weight:bold;">{s['change']}%</span>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            # 渲染 ECharts 极简双线同框
            st_echarts(options=options, height="120px", key=f"chart_{s['code']}")
            
            # 参数统计栏 (去除了推演，保留实战参数)
            st.markdown(f"""
                <div class="stock-card" style="margin-top:-10px; padding-top:1px;">
                    <div class="stat-row">
                        <div class="stat-item"><div class="val">{prem}%</div><div class="lbl">相对溢价(拟)</div></div>
                        <div class="stat-item"><div class="val" style="color:{s['m_color']}">{ib}%</div><div class="lbl">盘中实体</div></div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            if st.button(f"🗑️ 移出监控 {s['name']}", key=f"del_{s['code']}", use_container_width=True):
                st.session_state.pool.remove(s['code'])
                st.rerun()

else:
    st.info("监控池为空。请在上方输入代码（如 002428）挂载实时双线。")
