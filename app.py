import streamlit as st
import yfinance as yf
import requests
import pandas as pd
from datetime import datetime

# --- BEÁLLÍTÁSOK ---
JELSZO = st.secrets["app_jelszo"] 

st.set_page_config(page_title="FONTOSABB ÁRFOLYAMOK", layout="wide")

# CSS: Középre igazítás, rácsok finomítása
st.markdown("""
    <style>
    th, td { 
        text-align: center !important; 
        border-left: none !important; 
        border-right: none !important; 
        border-bottom: 1px solid #444 !important;
        padding: 12px !important;
    }
    th { border-top: 1px solid #444 !important; background-color: #1e1e1e; }
    table { margin-left: auto; margin-right: auto; width: 100%; border-collapse: collapse; }
    div[data-testid="stTable"] { border: none !important; }
    </style>
    """, unsafe_allow_html=True)

if "auth" not in st.session_state:
    st.session_state.auth = False

with st.sidebar:
    st.title("Biztonsági Kapu")
    pw = st.text_input("Jelszó", type="password")
    if st.button("Belépés"):
        if pw == JELSZO:
            st.session_state.auth = True
            st.rerun()
        else:
            st.error("Hibás jelszó!")

if not st.session_state.auth:
    st.warning("A hozzáférés korlátozott. Kérlek, add meg a jelszavad.")
    st.stop()

# --- FORMÁZÓ FÜGGVÉNY ---
def format_final(val, category, label):
    if pd.isna(val) or val is None: return "-"
    
    if val < 1 and val != 0:
        formatted = "{:,.8f}".format(val).replace(",", " ").rstrip('0').rstrip('.')
        if "." in formatted and len(formatted.split('.')[-1]) < 2:
             formatted = "{:,.2f}".format(val).replace(",", " ")
    else:
        formatted = "{:,.2f}".format(val).replace(",", " ")

    # Pénznem logika
    if category == "Crypto" or "Részvények" in category or "Indexek" in category or "Nemesfémek" in category:
        return f"${formatted}"
    if "ETF-ek" in category:
        return f"€{formatted}"
    if "Devizák" in category:
        if "HUF" in label or "Norvég Korona" in label:
            return f"{formatted} Ft"
        if "USD/EUR" in label:
            return f"€{formatted}"
        return f"${formatted}"
    return formatted

def color_delta(val):
    if not isinstance(val, (int, float)): return ""
    color = '#27ae60' if val > 0 else '#e74c3c' if val < 0 else 'white'
    return f'color: {color}; font-weight: bold;'

def format_pct(val):
    if pd.isna(val) or val is None: return "-"
    return f"{val:+.2f}%"

# --- ADATLEKÉRDEZÉS ---
@st.cache_data(ttl=1200)
def get_yahoo_data(ticker):
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="2y")
        if hist.empty: return None
        current = hist['Close'].iloc[-1]
        res = {"Price": current}
        intervals = {"24h": -2, "7d": -6, "30d": -22, "60d": -44, "90d": -66}
        for name, idx in intervals.items():
            try:
                prev = hist['Close'].iloc[idx]
                res[name] = ((current - prev) / prev) * 100
            except: res[name] = None
        y_start = hist[hist.index.year < datetime.now().year]
        res["YTD"] = ((current - y_start['Close'].iloc[-1]) / y_start['Close'].iloc[-1]) * 100 if not y_start.empty else None
        return res
    except: return None

@st.cache_data(ttl=1200)
def get_all_crypto():
    crypto_map = {"BTC": "Bitcoin", "ETH": "Ethereum", "SOL": "Solana", "HYPE": "Hyperliquid", "LINK": "Chainlink", "SUI": "Sui", "TAO": "Bittensor", "PUMP": "Pump.fun", "JLP": "Jupiter LP", "JUP": "Jupiter", "PENGU": "Pudgy Penguins"}
    ids = "bitcoin,ethereum,solana,hyperliquid,chainlink,sui,bittensor,pump-fun,jupiter-perpetuals-liquidity-provider-token,jupiter-exchange-solana,pudgy-penguins"
    url = f"https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&ids={ids}&price_change_percentage=24h,7d,30d"
    try:
        data = requests.get(url).json()
        output = {}
        for c in data:
            sym = c['symbol'].upper()
            name = crypto_map.get(sym, c['name'])
            output[f"{name} - {sym}"] = {"Price": c['current_price'], "24h": c.get('price_change_percentage_24h_in_currency'), "7d": c.get('price_change_percentage_7d_in_currency'), "30d": c.get('price_change_percentage_30d_in_currency'), "60d": None, "90d": None, "YTD": None}
        return output
    except: return {}

# --- MEGJELENÍTÉS ---
st.title("FONTOSABB ÁRFOLYAMOK")

# 1. Crypto
st.header("Crypto")
c_raw = get_all_crypto()
if c_raw:
    df_c = pd.DataFrame(c_raw).T
    df_c = df_c[["Price", "24h", "7d", "30d", "YTD"]]
    display_df = df_c.copy().astype(object)
    for row in display_df.index:
        display_df.at[row, "Price"] = format_final(df_c.loc[row, "Price"], "Crypto", row)
    st.table(display_df.style.map(color_delta, subset=["24h", "7d", "30d", "YTD"]).format(format_pct, subset=["24h", "7d", "30d", "YTD"]))

# 2. Yahoo Kategóriák
CATEGORIES = {
    "Részvények": {"Tesla": "TSLA", "Meta": "META", "Nvidia": "NVDA", "Google": "GOOGL", "MicroStrategy": "MSTR", "Microsoft": "MSFT", "Amazon": "AMZN", "AMD": "AMD", "Marathon": "MARA", "Sea Ltd": "SE", "Snowflake": "SNOW", "MercadoLibre": "MELI", "T. Rowe Price": "TROW", "Adobe": "ADBE", "Planet 13": "PLNH", "Enphase": "ENPH"},
    "ETF-ek": {"Vanguard All-World": "VWCE.DE", "iShares Small Cap Value": "ZPRV.DE"},
    "Indexek": {"S&P 500": "^GSPC", "Nasdaq 100": "^IXIC", "Russell 2000": "^RUT"},
    "Devizák": {"Amerikai Dollár - USD/HUF": "USDHUF=X", "Euró - EUR/HUF": "EURHUF=X", "Svájci Frank - CHF/HUF": "CHFHUF=X", "Angol Font - GBP/HUF": "GBPHUF=X", "Dollár/Euró - USD/EUR": "USDEUR=X"}
}

for cat_name, items in CATEGORIES.items():
    st.header(cat_name)
    results = {}
    for name, ticker in items.items():
        data = get_yahoo_data(ticker)
        if data: 
            # Itt töröljük a duplázott tickert a név végéről
            display_label = f"{name}" if "HUF" in ticker or "EUR" in ticker else f"{name} - {ticker}"
            results[display_label] = data
    
    if cat_name == "Devizák":
        u_h, u_n = get_yahoo_data("USDHUF=X"), get_yahoo_data("USDNOK=X")
        if u_h and u_n:
            results["Norvég Korona (számított) - NOK/HUF"] = {"Price": u_h['Price'] / u_n['Price'], "24h": None, "7d": None, "30d": None, "60d": None, "90d": None, "YTD": None}

    if results:
        df = pd.DataFrame(results).T
        df = df[["Price", "24h", "7d", "30d", "60d", "90d", "YTD"]]
        display_df = df.copy().astype(object)
        for row in display_df.index:
            display_df.at[row, "Price"] = format_final(df.loc[row, "Price"], cat_name, row)
        st.table(display_df.style.map(color_delta, subset=["24h", "7d", "30d", "60d", "90d", "YTD"]).format(format_pct, subset=["24h", "7d", "30d", "60d", "90d", "YTD"]))

st.header("Nemesfémek és olaj")
metals = {"Arany": "GC=F", "Ezüst": "SI=F", "Nyersolaj": "CL=F"}
m_res = {f"{n} - {t}": get_yahoo_data(t) for n, t in metals.items() if get_yahoo_data(t)}
if m_res:
    df_m = pd.DataFrame(m_res).T
    display_m = df_m.copy().astype(object)
    for row in display_m.index:
        display_m.at[row, "Price"] = format_final(df_m.loc[row, "Price"], "Nemesfémek", row)
    st.table(display_m.style.map(color_delta, subset=["24h", "7d", "30d", "60d", "90d", "YTD"]).format(format_pct, subset=["24h", "7d", "30d", "60d", "90d", "YTD"]))