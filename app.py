import streamlit as st
import pandas as pd
import requests
import time

st.set_page_config(page_title="Futures OI Scanner", layout="wide")
st.title("Stock Futures OI Scanner")

ACCESS_TOKEN = st.secrets["ACCESS_TOKEN"]

headers = {
    "Accept": "application/json",
    "Authorization": f"Bearer {ACCESS_TOKEN}"
}

# Top F&O Stocks
stocks = [
    "RELIANCE","HDFCBANK","ICICIBANK","SBIN","INFY",
    "TCS","ITC","LT","AXISBANK","KOTAKBANK"
]

def get_market_quotes(keys):
    url = "https://api.upstox.com/v2/market-quote/quotes"
    params = {"instrument_key": ",".join(keys)}
    response = requests.get(url, headers=headers, params=params)
    return response.json()

# Example futures instrument keys (update monthly)
futures_keys = {
    "RELIANCE": "NSE_FO|RELIANCE26MARFUT",
    "HDFCBANK": "NSE_FO|HDFCBANK26MARFUT",
    "ICICIBANK": "NSE_FO|ICICIBANK26MARFUT",
    "SBIN": "NSE_FO|SBIN26MARFUT",
    "INFY": "NSE_FO|INFY26MARFUT",
    "TCS": "NSE_FO|TCS26MARFUT",
    "ITC": "NSE_FO|ITC26MARFUT",
    "LT": "NSE_FO|LT26MARFUT",
    "AXISBANK": "NSE_FO|AXISBANK26MARFUT",
    "KOTAKBANK": "NSE_FO|KOTAKBANK26MARFUT"
}

if st.button("Load Futures Data"):

    instrument_keys = list(futures_keys.values())
    quotes_json = get_market_quotes(instrument_keys)
    quotes = quotes_json.get("data", {})

    rows = []

    for stock, key in futures_keys.items():
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
            "Stock": stock,
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
