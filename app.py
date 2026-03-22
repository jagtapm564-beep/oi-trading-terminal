import streamlit as st
import pandas as pd
import requests
import time

st.set_page_config(page_title="OI Trading Terminal", layout="wide")
st.title("OI Trading Analysis Terminal")

# Access Token from Streamlit Secrets
ACCESS_TOKEN = st.secrets["ACCESS_TOKEN"]

headers = {
    "Accept": "application/json",
    "Authorization": f"Bearer {ACCESS_TOKEN}"
}

# Symbols
symbols = {
    "NIFTY": "NSE_INDEX|Nifty 50",
    "BANKNIFTY": "NSE_INDEX|Nifty Bank"
}

# Select Symbol
symbol_name = st.selectbox("Select Symbol", list(symbols.keys()))
instrument = symbols[symbol_name]

# Expiry Date
expiry = st.text_input("Enter Expiry Date (YYYY-MM-DD)", "2026-03-26")

# Load Option Data
if st.button("Load Option Data"):
    try:
        url = f"https://api.upstox.com/v2/option/chain?instrument_key={instrument}&expiry_date={expiry}"
        response = requests.get(url, headers=headers)
        json_data = response.json()

        st.subheader("API Response")
        st.json(json_data)

        option_data = json_data.get('data', [])

        strikes = []
        call_oi = []
        put_oi = []
        call_oi_change = []
        put_oi_change = []

        for item in option_data:
            strikes.append(item.get('strike_price', 0))

            call_oi.append(item.get('call_options', {}).get('oi', 0))
            put_oi.append(item.get('put_options', {}).get('oi', 0))

            call_oi_change.append(item.get('call_options', {}).get('oi_change', 0))
            put_oi_change.append(item.get('put_options', {}).get('oi_change', 0))

        df = pd.DataFrame({
            "Strike": strikes,
            "Call OI": call_oi,
            "Put OI": put_oi,
            "Call OI Change": call_oi_change,
            "Put OI Change": put_oi_change
        })

        st.subheader("Option Chain OI Data")
        st.dataframe(df)

        # PCR
        total_call_oi = sum(call_oi)
        total_put_oi = sum(put_oi)

        if total_call_oi > 0:
            pcr = total_put_oi / total_call_oi
            st.metric("PCR", round(pcr, 2))

        # Support & Resistance
        if len(call_oi) > 0:
            resistance = strikes[call_oi.index(max(call_oi))]
            support = strikes[put_oi.index(max(put_oi))]

            st.metric("OI Resistance", resistance)
            st.metric("OI Support", support)

    except Exception as e:
        st.error(e)

# Auto Refresh
auto_refresh = st.checkbox("Auto Refresh (30 sec)")

if auto_refresh:
    time.sleep(30)
    st.rerun()
