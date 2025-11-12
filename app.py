# app.py （投稿用：無 LINE、無按鈕、簡潔版）
import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# === AI 資產配置建議 ===
def get_ai_allocation(age, monthly_save, risk):
    base = {
        "0050.TW": 0.4, "0056.TW": 0.3, "VT": 0.2, "BND": 0.1
    }
    if risk == "保守":
        base["BND"] += 0.2; base["VT"] -= 0.1; base["0050.TW"] -= 0.1
    elif risk == "積極":
        base["VT"] += 0.2; base["BND"] -= 0.1

    st.info(f"**AI 小秘書建議（{age}歲，風險：{risk}）**\n根據現代投資組合理論，建議每月投入 {monthly_save:,.0f} 元：")
    for t, w in base.items():
        name = {"0050.TW":"台灣50", "0056.TW":"高股息", "VT":"全球股票", "BND":"美國債券"}[t]
        st.write(f"- **{name}** (`{t}`): {w*100:.0f}%")
    return base

# === 模擬 20 年複利 ===
def simulate_portfolio(allocation, monthly_save, years=20):
    end_date = datetime.now()
    start_date = f"{end_date.year - years}-01-01"
    total_monthly_return = 0.0
    valid_count = 0

    for ticker, weight in allocation.items():
        try:
            data = yf.download(ticker, start=start_date, end=end_date, progress=False)
            if data.empty:
                continue
            close_col = 'Adj Close' if 'Adj Close' in data.columns else 'Close'
            monthly_return = data[close_col].resample('M').last().pct_change().mean()
            if pd.notna(monthly_return):
                total_monthly_return += monthly_return * weight
                valid_count += 1
        except:
            continue

    if valid_count == 0:
        total_monthly_return = 0.005  # 預設 0.5%/月

    months = years * 12
    future_value = 0.0
    values = []
    for m in range(months):
        future_value = future_value * (1 + total_monthly_return) + monthly_save
        if m % 12 == 0:
            values.append(future_value)

    return values

# === 介面 ===
st.title("AI 投資小秘書")
st.markdown("---")

col1, col2 = st.columns(2)
with col1:
    age = st.slider("年齡", 20, 60, 30)
    monthly_save = st.number_input("每月投入", 1000, 50000, 5000, 1000)
with col2:
    risk = st.selectbox("風險", ["保守", "中性", "積極"])

if st.button("生成投資建議"):
    allocation = get_ai_allocation(age, monthly_save, risk)
    values = simulate_portfolio(allocation, monthly_save)

    years = list(range(0, 21))
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=years, y=values, mode='lines+markers', name='你的組合'))

    # 台股對比
    try:
        twse_data = yf.download("^TWII", period="20y", progress=False)
        if not twse_data.empty:
            close_col = 'Adj Close' if 'Adj Close' in twse_data.columns else 'Close'
            twse_ret = twse_data[close_col].resample('M').last().pct_change().mean()
            if pd.notna(twse_ret):
                tv = 0.0
                tvs = []
                for m in range(240):
                    tv = tv * (1 + twse_ret) + monthly_save
                    if m % 12 == 0:
                        tvs.append(tv)
                fig.add_trace(go.Scatter(x=years, y=tvs, mode='lines+markers', name='台股加權指數'))
    except:
        pass

    fig.update_layout(title="20 年複利模擬", xaxis_title="年", yaxis_title="總資產 (元)")
    st.plotly_chart(fig, use_container_width=True)
    st.success(f"20 年後預估資產：**{values[-1]:,.0f} 元**")

    # === 模擬簡訊（自動顯示，不用按）===
    st.info("**模擬 LINE 簡訊功能**：\n"
            "每日 18:00 將自動推播：\n"
            "『AI投資小秘書 今日提醒！\n"
            f"時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            "點擊查看最新模擬～』")

# === 免責 ===
st.markdown("---")
st.caption("免責聲明：本工具僅供教育用途，非投資建議。")
