import streamlit as st
import pandas as pd
import requests
import time

st.set_page_config(page_title="OI Trading Terminal", layout="wide")

st.title("OI Trading Analysis Terminal")

ACCESS_TOKEN = st.secrets.get("ACCESS_TOKEN", "")

headers = {
    "Accept": "application/json",
    "Authorization": f"Bearer {ACCESS_TOKEN}"
}

stocks = [
"NIFTY","BANKNIFTY","RELIANCE","HDFCBANK","ICICIBANK","SBIN","INFY","TCS","AXISBANK",
"KOTAKBANK","LT","ITC","HCLTECH","WIPRO","MARUTI","BAJFINANCE","BAJAJFINSV","ADANIENT",
"ADANIPORTS","ASIANPAINT","TITAN","ULTRACEMCO","ONGC","COALINDIA","POWERGRID","NTPC",
"JSWSTEEL","TATASTEEL","HINDALCO","GRASIM","SUNPHARMA","DRREDDY","CIPLA","DIVISLAB",
"BRITANNIA","NESTLEIND","HEROMOTOCO","EICHERMOT","M&M","TATAMOTORS","INDUSINDBK",
"SBILIFE","HDFCLIFE","BAJAJ-AUTO","UPL","TECHM","LTIM","PEL","DLF","HAL","BEL"
]

data = []

if st.button("Run OI Scanner"):
    for stock in stocks:
        try:
            url = f"https://api.upstox.com/v2/market-quote/quotes?symbol={stock}"
            r = requests.get(url, headers=headers)
            price = r.json()['data'][stock]['last_price']

            support = price - 10
            resistance = price + 10
            pcr = 1.0

            call_oi_change = 0
            put_oi_change = 0

            price_change = 0
oi_change = put_oi_change - call_oi_change

if price_change > 0 and oi_change > 0:
    signal = "Long Build Up"
elif price_change < 0 and oi_change > 0:
    signal = "Short Build Up"
elif price_change > 0 and oi_change < 0:
    signal = "Short Covering"
elif price_change < 0 and oi_change < 0:
    signal = "Long Unwinding"
else:
    signal = "Range"
            data.append([stock, price, support, resistance, pcr, call_oi_change, put_oi_change, signal])

        except:
            data.append([stock, "-", "-", "-", "-", "-", "-", "-"])

    df = pd.DataFrame(data, columns=[
        "Stock","Price","Support","Resistance","PCR","Call OI Change","Put OI Change","Signal"
    ])

    st.dataframe(df)
total_call_oi = 0
total_put_oi = 0

for row in data:
    try:
        total_call_oi += float(row[5])
        total_put_oi += float(row[6])
    except:
        pass

sentiment = "Neutral"

if total_put_oi > total_call_oi:
    sentiment = "Bullish"
elif total_call_oi > total_put_oi:
    sentiment = "Bearish"

st.subheader("Market Sentiment")
st.metric("Overall Market", sentiment)
bullish = df[df["Signal"]=="Long Build Up"]
bearish = df[df["Signal"]=="Short Build Up"]

st.subheader("Top Bullish OI Build Up")
st.dataframe(bullish)

st.subheader("Top Bearish OI Build Up")
st.dataframe(bearish)

breakout = []

for i,row in df.iterrows():
    try:
        price = float(row["Price"])
        res = float(row["Resistance"])
        sup = float(row["Support"])

        if price > res * 0.99:
            breakout.append([row["Stock"], "Resistance Breakout"])

        if price < sup * 1.01:
            breakout.append([row["Stock"], "Support Breakdown"])

    except:
        pass

breakout_df = pd.DataFrame(breakout, columns=["Stock","Breakout"])

st.subheader("Breakout Scanner")
st.dataframe(breakout_df)
auto_refresh = st.checkbox("Auto Refresh (30 sec)")

if auto_refresh:
    time.sleep(30)
    st.rerun()
