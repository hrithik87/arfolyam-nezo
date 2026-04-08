import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px

# --- BEÁLLÍTÁSOK ---
JELSZO = st.secrets["portfolio_jelszo"]
HOLDINGS = st.secrets["darabszamok"]

st.set_page_config(page_title="PORTFÓLIÓ KEZELŐ", layout="wide")

# CSS: Táblázat stílus
st.markdown("""
    <style>
    th, td { text-align: center !important; border-bottom: 1px solid #444 !important; padding: 10px !important; }
    th { border-top: 1px solid #444 !important; background-color: #1e1e1e; }
    table { width: 100%; border-collapse: collapse; }
    </style>
    """, unsafe_allow_html=True)

if "auth" not in st.session_state:
    st.session_state.auth = False

with st.sidebar:
    st.title("Privát Zóna")
    pw = st.text_input("Jelszó", type="password")
    if st.button("Belépés"):
        if pw == JELSZO:
            st.session_state.auth = True
            st.rerun()
        else:
            st.error("Hibás jelszó!")

if not st.session_state.auth:
    st.warning("Privát portfólió. Add meg a jelszavad.")
    st.stop()

# --- ADATLEKÉRDEZÉS ---
NAME_MAP = {
    "TSLA": "Tesla", "META": "Meta", "NVDA": "Nvidia", "GOOGL": "Google A",
    "MSTR": "MicroStrategy", "MSFT": "Microsoft", "AMZN": "Amazon",
    "AMD": "AMD", "MARA": "Marathon", "SE": "Sea Ltd", "SNOW": "Snowflake",
    "MELI": "MercadoLibre", "TROW": "T. Rowe Price", "ADBE": "Adobe",
    "PLNH": "Planet 13", "ENPH": "Enphase", "WBD": "Warner Bros. Discovery",
    "ONL": "Orion", "VWCE.DE": "Vanguard All-World", "ZPRV.DE": "iShares Small Cap Value",
    "IUSN.DE": "iShares MSCI World Small Cap", "CBTC.DE": "21Shares Core Bitcoin ETP"
}

@st.cache_data(ttl=600)
def get_price(ticker):
    try:
        t = yf.Ticker(ticker)
        df = t.history(period="5d")
        if df.empty: return None
        return {"price": df['Close'].iloc[-1], "prev": df['Close'].iloc[-2]}
    except: return None

st.title("SAJÁT PORTFÓLIÓ ÁLLAPOT")

with st.spinner("Friss árfolyamok lekérése..."):
    # Devizák fixen
    d_usd_huf = get_price("USDHUF=X")
    d_eur_usd = get_price("EURUSD=X")
    
    usd_huf = d_usd_huf["price"] if d_usd_huf else 360.0
    eur_usd = d_eur_usd["price"] if d_eur_usd else 1.08

    results = []
    total_usd = 0

    for ticker, db in HOLDINGS.items():
        if db <= 0: continue
        
        data = get_price(ticker)
        if data:
            curr = data["price"]
            chg = ((curr - data["prev"]) / data["prev"]) * 100
            
            is_eur = ticker.endswith(".DE")
            p_usd = curr * eur_usd if is_eur else curr
            
            v_usd = p_usd * db
            v_huf = v_usd * usd_huf
            total_usd += v_usd
            
            results.append({
                "Név": NAME_MAP.get(ticker, ticker),
                "Ticker": ticker,
                "Darab": db,
                "Ár": curr,
                "is_eur": is_eur,
                "Value_USD": v_usd,
                "Value_HUF": v_huf,
                "Napi_Vált": chg
            })

# --- MEGJELENÍTÉS ---
if results:
    full_df = pd.DataFrame(results)
    
    st.subheader(f"Teljes Vagyon: ${total_usd:,.0f} | {(total_usd * usd_huf):,.0f} Ft")
    
    # Rendezés gombok
    c1, c2 = st.columns(2)
    with c1:
        s_by = st.selectbox("Rendezés:", ["Value_USD", "Napi_Vált", "Név"])
    with c2:
        s_dir = st.radio("Irány:", ["Csökkenő", "Növekvő"], horizontal=True)
    
    full_df = full_df.sort_values(by=s_by, ascending=(s_dir == "Növekvő"))

    # Táblázat formázás
    show_df = pd.DataFrame()
    show_df["Név"] = full_df["Név"]
    show_df["Ticker"] = full_df["Ticker"]
    show_df["Darab"] = full_df["Darab"]
    show_df["Ár (Saját Deviza)"] = full_df.apply(lambda r: f"€{r['Ár']:,.2f}" if r['is_eur'] else f"${r['Ár']:,.2f}", axis=1)
    show_df["Érték (USD)"] = full_df["Value_USD"].apply(lambda x: f"${x:,.2f}")
    show_df["Érték (HUF)"] = full_df["Value_HUF"].apply(lambda x: f"{x:,.0f} Ft")
    show_df["Napi Változás (%)"] = full_df["Napi_Vált"]

    def color_val(v):
        return f'color: {"#27ae60" if v > 0 else "#e74c3c"}; font-weight: bold;'

    st.table(show_df.style.map(color_val, subset=["Napi Változás (%)"]).format("{:+.2f}%", subset=["Napi Változás (%)"]))

    # TORTADIAGRAM
    st.markdown("---")
    st.subheader("Portfólió Megoszlása")
    fig = px.pie(full_df, values='Value_USD', names='Név', color_discrete_sequence=px.colors.qualitative.Pastel)
    fig.update_traces(textinfo='percent+label')
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Nincs adat. Ellenőrizd a darabszámokat a Secrets-ben!")