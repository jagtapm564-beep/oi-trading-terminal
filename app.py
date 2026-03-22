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

expiry = st.text_input("Enter Expiry Date (YYYY-MM-DD)", "2026-03-26")

if st.button("Load Option Data"):

    try:
        url = f"https://api.upstox.com/v2/option/chain?instrument_key={instrument}&expiry_date={expiry}"
        r = requests.get(url, headers=headers)
        json_data = r.json()

        option_data = json_data['data']

        strikes = []
        call_oi = []
        put_oi = []
        call_oi_change = []
        put_oi_change = []

        for item in option_data:
            strikes.append(item['strike_price'])
            call_oi.append(item['call_options']['open_interest'])
            put_oi.append(item['put_options']['open_interest'])
            call_oi_change.append(item['call_options']['change_in_oi'])
            put_oi_change.append(item['put_options']['change_in_oi'])

        df = pd.DataFrame({
            "Strike": strikes,
            "Call OI": call_oi,
            "Put OI": put_oi,
            "Call OI Change": call_oi_change,
            "Put OI Change": put_oi_change
        })

        st.subheader("Option Chain OI")
        st.dataframe(df)

        total_call_oi = sum(call_oi)
        total_put_oi = sum(put_oi)
        pcr = total_put_oi / total_call_oi

        st.metric("PCR", round(pcr,2))

        resistance = strikes[call_oi.index(max(call_oi))]
        support = strikes[put_oi.index(max(put_oi))]

        st.metric("OI Resistance", resistance)
        st.metric("OI Support", support)

    except Exception as e:
        st.write("Error:", e)

# Auto Refresh
auto_refresh = st.checkbox("Auto Refresh (30 sec)")

if auto_refresh:
    time.sleep(30)
    st.rerun()
