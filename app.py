import streamlit as st
import pandas as pd
import requests
import time

st.set_page_config(page_title="OI Trading Terminal", layout="wide")
st.title("OI Trading Analysis Terminal")

ACCESS_TOKEN = st.secrets["ACCESS_TOKEN"]

headers = {
    "Accept": "application/json",
    "Authorization": f"Bearer {ACCESS_TOKEN}"
}

# Top 20 F&O Stocks + Index
symbols = {
    "NIFTY": "NSE_INDEX|Nifty 50",
    "BANKNIFTY": "NSE_INDEX|Nifty Bank",
    "FINNIFTY": "NSE_INDEX|Nifty Financial Services",

    "RELIANCE": "NSE_EQ|RELIANCE",
    "HDFCBANK": "NSE_EQ|HDFCBANK",
    "ICICIBANK": "NSE_EQ|ICICIBANK",
    "SBIN": "NSE_EQ|SBIN",
    "INFY": "NSE_EQ|INFY",
    "TCS": "NSE_EQ|TCS",
    "LT": "NSE_EQ|LT",
    "ITC": "NSE_EQ|ITC",
    "AXISBANK": "NSE_EQ|AXISBANK",
    "KOTAKBANK": "NSE_EQ|KOTAKBANK",
    "TATAMOTORS": "NSE_EQ|TATAMOTORS",
    "TATASTEEL": "NSE_EQ|TATASTEEL",
    "BAJFINANCE": "NSE_EQ|BAJFINANCE",
    "HCLTECH": "NSE_EQ|HCLTECH",
    "MARUTI": "NSE_EQ|MARUTI",
    "ULTRACEMCO": "NSE_EQ|ULTRACEMCO",
    "ADANIENT": "NSE_EQ|ADANIENT",
    "ADANIPORTS": "NSE_EQ|ADANIPORTS",
    "WIPRO": "NSE_EQ|WIPRO",
    "NTPC": "NSE_EQ|NTPC"
}

symbol_name = st.selectbox("Select Symbol", list(symbols.keys()))
instrument = symbols[symbol_name]

expiry = st.text_input("Enter Expiry Date (YYYY-MM-DD)", "2026-03-26")

def get_option_data(instrument, expiry):
    url = f"https://api.upstox.com/v2/option/chain?instrument_key={instrument}&expiry_date={expiry}"
    response = requests.get(url, headers=headers)
    return response.json()

if st.button("Load Option Data"):

    try:
        json_data = get_option_data(instrument, expiry)
        option_data = json_data.get('data', [])

        strikes = []
        call_oi = []
        put_oi = []
        call_ltp = []
        put_ltp = []
        call_prev_oi = []
        put_prev_oi = []

        for item in option_data:
            strikes.append(item.get('strike_price', 0))

            call_market = item.get('call_options', {}).get('market_data', {})
            put_market = item.get('put_options', {}).get('market_data', {})

            call_oi.append(call_market.get('oi', 0))
            put_oi.append(put_market.get('oi', 0))

            call_prev_oi.append(call_market.get('prev_oi', 0))
            put_prev_oi.append(put_market.get('prev_oi', 0))

            call_ltp.append(call_market.get('ltp', 0))
            put_ltp.append(put_market.get('ltp', 0))

        df = pd.DataFrame({
            "Strike": strikes,
            "Call OI": call_oi,
            "Put OI": put_oi,
            "Call Prev OI": call_prev_oi,
            "Put Prev OI": put_prev_oi,
            "Call LTP": call_ltp,
            "Put LTP": put_ltp
        })

        # OI Change
        df["Call OI Change"] = df["Call OI"] - df["Call Prev OI"]
        df["Put OI Change"] = df["Put OI"] - df["Put Prev OI"]

        st.subheader("Option Chain Data")
        st.dataframe(df)

        # PCR
        total_call_oi = sum(call_oi)
        total_put_oi = sum(put_oi)

        if total_call_oi > 0:
            pcr = total_put_oi / total_call_oi
            st.metric("PCR", round(pcr, 2))

        # Support Resistance
        resistance = strikes[call_oi.index(max(call_oi))]
        support = strikes[put_oi.index(max(put_oi))]

        st.metric("OI Resistance", resistance)
        st.metric("OI Support", support)

        # Build Up Analysis
        buildup = []

        for i in range(len(df)):
            if df["Call OI Change"][i] > 0:
                buildup.append("Short Build Up")
            elif df["Put OI Change"][i] > 0:
                buildup.append("Long Build Up")
            elif df["Call OI Change"][i] < 0:
                buildup.append("Short Covering")
            elif df["Put OI Change"][i] < 0:
                buildup.append("Long Unwinding")
            else:
                buildup.append("Neutral")

        df["Build Up"] = buildup

        st.subheader("Build Up Analysis")
        st.dataframe(df[["Strike", "Build Up"]])

        # Intraday Direction
        if pcr > 1.2:
            st.success("Market Direction: Bullish")
        elif pcr < 0.8:
            st.error("Market Direction: Bearish")
        else:
            st.warning("Market Direction: Sideways")

    except Exception as e:
        st.error(e)

# Auto Refresh
auto_refresh = st.checkbox("Auto Refresh (30 sec)")
if auto_refresh:
    time.sleep(30)
    st.rerun()
