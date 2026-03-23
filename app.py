import streamlit as st
import pandas as pd
import requests
import time

st.set_page_config(page_title="F&O OI Scanner", layout="wide")
st.title("Stock Futures OI Scanner")

ACCESS_TOKEN = st.secrets["ACCESS_TOKEN"]

headers = {
    "Accept": "application/json",
    "Authorization": f"Bearer {ACCESS_TOKEN}"
}

# Stock Futures Instrument Keys (Near Month Futures)
futures_symbols = {
    "RELIANCE": "NSE_FO|RELIANCE24MARFUT",
    "HDFCBANK": "NSE_FO|HDFCBANK24MARFUT",
    "ICICIBANK": "NSE_FO|ICICIBANK24MARFUT",
    "SBIN": "NSE_FO|SBIN24MARFUT",
    "INFY": "NSE_FO|INFY24MARFUT",
    "TCS": "NSE_FO|TCS24MARFUT",
    "ITC": "NSE_FO|ITC24MARFUT",
    "LT": "NSE_FO|LT24MARFUT",
    "AXISBANK": "NSE_FO|AXISBANK24MARFUT",
    "KOTAKBANK": "NSE_FO|KOTAKBANK24MARFUT"
}

def get_market_quotes(keys):
    url = "https://api.upstox.com/v2/market-quote/quotes"
    params = {
        "instrument_key": ",".join(keys)
    }
    response = requests.get(url, headers=headers, params=params)
    return response.json()

if st.button("Load Futures OI Data"):

    instrument_keys = list(futures_symbols.values())
    quotes_json = get_market_quotes(instrument_keys)
    quotes = quotes_json.get("data", {})

    rows = []

    for name, key in futures_symbols.items():
        q = quotes.get(key, {})
        
        ltp = q.get("last_price", 0)
        prev_close = q.get("ohlc", {}).get("close", 0)
        oi = q.get("oi", 0)
        prev_oi = q.get("prev_oi", 0)

        price_change = ltp - prev_close
        oi_change = oi - prev_oi

        if price_change > 0 and oi_change > 0:
            signal = "Long Build Up"
        elif price_change < 0 and oi_change > 0:
            signal = "Short Build Up"
        elif price_change > 0 and oi_change < 0:
            signal = "Short Covering"
        elif price_change < 0 and oi_change < 0:
            signal = "Long Unwinding"
        else:
            signal = "Neutral"

        rows.append({
            "Stock": name,
            "Price": ltp,
            "Price Change": round(price_change, 2),
            "OI": oi,
            "OI Change": oi_change,
            "Signal": signal
        })

    df = pd.DataFrame(rows)
    st.dataframe(df.sort_values("OI Change", ascending=False))

auto = st.checkbox("Auto Refresh 30 sec")
if auto:
    time.sleep(30)
    st.rerun()
