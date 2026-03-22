import streamlit as st
import pandas as pd
import requests
import time

st.set_page_config(page_title="OI Trading Terminal", layout="wide")
st.title("Options OI Trading Terminal")

ACCESS_TOKEN = st.secrets["ACCESS_TOKEN"]

headers = {
    "Accept": "application/json",
    "Authorization": f"Bearer {ACCESS_TOKEN}"
}

index_symbols = {
    "NIFTY": "NSE_INDEX|Nifty 50",
    "BANKNIFTY": "NSE_INDEX|Nifty Bank",
    "FINNIFTY": "NSE_INDEX|Nifty Financial Services"
stock_symbols = {
    "RELIANCE": "NSE_EQ|INE002A01018",
    "HDFCBANK": "NSE_EQ|INE040A01034",
    "ICICIBANK": "NSE_EQ|INE090A01021",
    "SBIN": "NSE_EQ|INE062A01020",
    "INFY": "NSE_EQ|INE009A01021",
    "TCS": "NSE_EQ|INE467B01029",
    "ITC": "NSE_EQ|INE154A01025",
    "LT": "NSE_EQ|INE018A01030",
    "AXISBANK": "NSE_EQ|INE238A01034",
    "KOTAKBANK": "NSE_EQ|INE237A01028"
}

instrument_type = st.selectbox("Select Type", ["Index", "Stock"])

if instrument_type == "Index":
    symbol_name = st.selectbox("Select Index", list(index_symbols.keys()))
    instrument = index_symbols[symbol_name]
else:
    symbol_name = st.selectbox("Select Stock", list(stock_symbols.keys()))
    instrument = stock_symbols[symbol_name]

expiry = st.text_input("Enter Expiry (YYYY-MM-DD)", "2026-03-26")

def get_index_option_chain():
    url = "https://api.upstox.com/v2/option/chain"
    params = {
        "instrument_key": instrument,
        "expiry_date": expiry
    }
    response = requests.get(url, headers=headers, params=params)
    return response.json()

def get_option_contracts():
    url = "https://api.upstox.com/v2/option/contracts"
    params = {
        "instrument_key": instrument,
        "expiry_date": expiry
    }
    response = requests.get(url, headers=headers, params=params)
    return response.json()

def get_market_quotes(keys):
    url = "https://api.upstox.com/v2/market-quote/quotes"
    params = {
        "instrument_key": ",".join(keys)
    }
    response = requests.get(url, headers=headers, params=params)
    return response.json()

if st.button("Load Option Data"):

    if instrument_type == "Index":
        json_data = get_index_option_chain()
        option_data = json_data.get("data", [])

        rows = []
        for item in option_data:
            strike = item.get("strike_price", 0)
            call_md = item.get("call_options", {}).get("market_data", {})
            put_md = item.get("put_options", {}).get("market_data", {})

            rows.append({
                "Strike": strike,
                "Call OI": call_md.get("oi", 0),
                "Put OI": put_md.get("oi", 0),
                "Call OI Change": call_md.get("oi", 0) - call_md.get("prev_oi", 0),
                "Put OI Change": put_md.get("oi", 0) - put_md.get("prev_oi", 0),
                "Call LTP": call_md.get("ltp", 0),
                "Put LTP": put_md.get("ltp", 0),
            })

        df = pd.DataFrame(rows)

    else:
        contracts_json = get_option_contracts()
        contracts = contracts_json.get("data", [])

        if not contracts:
            st.error("No option contracts found")
            st.write(contracts_json)
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

        if not quotes:
            st.error("No market quotes found")
            st.write(quotes_json)
            st.stop()

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

    if df.empty:
        st.error("No option data available")
        st.stop()

    df = df.sort_values("Strike")
    st.dataframe(df)

    total_call = df["Call OI"].sum()
    total_put = df["Put OI"].sum()

    if total_call > 0:
        pcr = total_put / total_call
        st.metric("PCR", round(pcr, 2))

    resistance = df.loc[df["Call OI"].idxmax(), "Strike"]
    support = df.loc[df["Put OI"].idxmax(), "Strike"]

    st.metric("Resistance", resistance)
    st.metric("Support", support)

auto = st.checkbox("Auto Refresh 30 sec")
if auto:
    time.sleep(30)
    st.rerun()
