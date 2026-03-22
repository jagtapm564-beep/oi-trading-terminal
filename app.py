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

symbols = {
    "RELIANCE": "NSE_EQ|RELIANCE",
    "HDFCBANK": "NSE_EQ|HDFCBANK",
    "ICICIBANK": "NSE_EQ|ICICIBANK",
    "SBIN": "NSE_EQ|SBIN",
    "INFY": "NSE_EQ|INFY",
    "TCS": "NSE_EQ|TCS",
    "ITC": "NSE_EQ|ITC",
    "LT": "NSE_EQ|LT",
    "AXISBANK": "NSE_EQ|AXISBANK",
    "KOTAKBANK": "NSE_EQ|KOTAKBANK"
}

symbol_name = st.selectbox("Select Stock", list(symbols.keys()))
instrument = symbols[symbol_name]

expiry = st.text_input("Enter Expiry Date (YYYY-MM-DD)", "2026-03-26")

# Step 1: Get option contracts
def get_option_contracts():
    url = f"https://api.upstox.com/v2/option/contracts"
    params = {
        "instrument_key": instrument,
        "expiry_date": expiry
    }
    response = requests.get(url, headers=headers, params=params)
    return response.json()

# Step 2: Get market quotes
def get_market_quotes(keys):
    url = "https://api.upstox.com/v2/market-quote/quotes"
    params = {
        "instrument_key": ",".join(keys)
    }
    response = requests.get(url, headers=headers, params=params)
    return response.json()

if st.button("Load Stock Option Data"):

    contracts_json = get_option_contracts()
    contracts = contracts_json.get("data", [])

    if not contracts:
        st.error("No option contracts found")
        st.stop()

    instrument_keys = []
    strike_map = {}

    for c in contracts:
        key = c.get("instrument_key")
        strike = c.get("strike_price")
        option_type = c.get("option_type")

        instrument_keys.append(key)
        strike_map[key] = (strike, option_type)

    quotes_json = get_market_quotes(instrument_keys)
    quotes = quotes_json.get("data", {})

    rows = {}

    for key, q in quotes.items():
        strike, option_type = strike_map[key]
        oi = q.get("oi", 0)
        prev_oi = q.get("prev_oi", 0)
        ltp = q.get("last_price", 0)

        if strike not in rows:
            rows[strike] = {
                "Strike": strike,
                "Call OI": 0,
                "Put OI": 0,
                "Call OI Change": 0,
                "Put OI Change": 0,
                "Call LTP": 0,
                "Put LTP": 0
            }

        if option_type == "CE":
            rows[strike]["Call OI"] = oi
            rows[strike]["Call OI Change"] = oi - prev_oi
            rows[strike]["Call LTP"] = ltp
        else:
            rows[strike]["Put OI"] = oi
            rows[strike]["Put OI Change"] = oi - prev_oi
            rows[strike]["Put LTP"] = ltp

    df = pd.DataFrame(rows.values())
    df = df.sort_values("Strike")

    st.dataframe(df)

    # PCR
    total_call = df["Call OI"].sum()
    total_put = df["Put OI"].sum()

    if total_call > 0:
        pcr = total_put / total_call
        st.metric("PCR", round(pcr, 2))

    # Support Resistance
    resistance = df.loc[df["Call OI"].idxmax(), "Strike"]
    support = df.loc[df["Put OI"].idxmax(), "Strike"]

    st.metric("Resistance", resistance)
    st.metric("Support", support)

# Auto Refresh
auto = st.checkbox("Auto Refresh 30 sec")
if auto:
    time.sleep(30)
    st.rerun()
