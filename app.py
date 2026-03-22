import streamlit as st
import requests
import pandas as pd
import time

st.set_page_config(page_title="OI Trading Terminal", layout="wide")

ACCESS_TOKEN = ACCESS_TOKEN = st.secrets.get("ACCESS_TOKEN", "")

headers = {
    "Accept": "application/json",
    "Authorization": f"Bearer {ACCESS_TOKEN}"
}

fno_stocks = {
    "NIFTY": "NSE_INDEX|Nifty 50",
    "BANKNIFTY": "NSE_INDEX|Nifty Bank",
    "RELIANCE": "NSE_EQ|RELIANCE",
    "HDFCBANK": "NSE_EQ|HDFCBANK",
    "ICICIBANK": "NSE_EQ|ICICIBANK",
    "SBIN": "NSE_EQ|SBIN",
    "TCS": "NSE_EQ|TCS",
    "INFY": "NSE_EQ|INFY",
    "AXISBANK": "NSE_EQ|AXISBANK",
    "TATAPOWER": "NSE_EQ|TATAPOWER"
}

def get_live_price(instrument):
    url = "https://api.upstox.com/v2/market-quote/ltp"
    params = {"instrument_key": instrument}
    response = requests.get(url, headers=headers, params=params)
    data = response.json()
    price = list(data['data'].values())[0]['last_price']
    return price

def analyze_oi(instrument):
    url = "https://api.upstox.com/v2/option/chain"
    params = {"instrument_key": instrument}
    response = requests.get(url, headers=headers, params=params)
    data = response.json()

    option_data = []

    for item in data['data']:
        strike = item['strike_price']
        call_oi = item['call_options']['market_data']['oi']
        call_oi_change = item['call_options']['market_data']['oi_change']
        put_oi = item['put_options']['market_data']['oi']
        put_oi_change = item['put_options']['market_data']['oi_change']

        option_data.append([
            strike,
            call_oi,
            call_oi_change,
            put_oi,
            put_oi_change
        ])

    df = pd.DataFrame(option_data, columns=[
        "Strike",
        "Call OI",
        "Call OI Change",
        "Put OI",
        "Put OI Change"
    ])

    resistance = df.loc[df["Call OI"].idxmax()]["Strike"]
    support = df.loc[df["Put OI"].idxmax()]["Strike"]

    total_call_oi = df["Call OI"].sum()
    total_put_oi = df["Put OI"].sum()
    pcr = total_put_oi / total_call_oi

    price = get_live_price(instrument)

    df["Diff"] = abs(df["Strike"] - price)
    atm_row = df.loc[df["Diff"].idxmin()]

    atm_call_oi_change = atm_row["Call OI Change"]
    atm_put_oi_change = atm_row["Put OI Change"]

    if atm_put_oi_change > atm_call_oi_change:
        signal = "Bullish"
    else:
        signal = "Bearish"

    if abs(price - support) < abs(price - resistance) and signal == "Bullish":
        trade = "Buy CE"
    elif abs(price - resistance) < abs(price - support) and signal == "Bearish":
        trade = "Buy PE"
    else:
        trade = "Wait"

    return price, support, resistance, round(pcr, 2), atm_call_oi_change, atm_put_oi_change, trade


st.title("OI Trading Analysis Terminal")

auto_refresh = st.sidebar.checkbox("Auto Refresh (30 sec)")

scanner_data = []

if st.button("Run OI Scanner") or auto_refresh:
    for stock, instrument in fno_stocks.items():
        try:
            price, support, resistance, pcr, atm_call, atm_put, trade = analyze_oi(instrument)
            scanner_data.append([
                stock, price, support, resistance, pcr, atm_call, atm_put, trade
            ])
        except:
            scanner_data.append([stock, "-", "-", "-", "-", "-", "-", "Error"])

    scanner_df = pd.DataFrame(
        scanner_data,
        columns=[
            "Stock",
            "Price",
            "Support",
            "Resistance",
            "PCR",
            "ATM Call OI Change",
            "ATM Put OI Change",
            "Best Trade"
        ]
    )

    st.dataframe(scanner_df, use_container_width=True)

if auto_refresh:
    time.sleep(30)
    st.experimental_rerun()
