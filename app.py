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
    "NIFTY": "NSE_INDEX|Nifty 50",
    "BANKNIFTY": "NSE_INDEX|Nifty Bank"
}

symbol_name = st.selectbox("Select Symbol", list(symbols.keys()))
instrument = symbols[symbol_name]

if st.button("Load Option Data"):

    url = f"https://api.upstox.com/v2/option/chain?instrument_key={instrument}"
    r = requests.get(url, headers=headers)

    st.subheader("API Response")
    st.write(r.json())   # This will show actual API response

# Auto Refresh
auto_refresh = st.checkbox("Auto Refresh (30 sec)")

if auto_refresh:
    time.sleep(30)
    st.rerun()
