import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px

# --- BEÁLLÍTÁSOK ---
JELSZO = st.secrets["app_jelszo"]
HOLDINGS = st.secrets["darabszamok"]

st.set_page_config(page_title="PORTFÓLIÓ KEZELŐ", layout="wide")

st.markdown("""
    <style>
    th, td { text-align: center !important; border-bottom: 1px solid #444 !important; padding: 10px !important; }
    th { border-top: 1px solid #444 !important; background-color: #1e1e1e; }
    table { width: 100%; border-collapse: collapse; }
    </style>
    """, unsafe_allow_html=True)

# --- BIZTONSÁGI KAPU ---
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
    st.warning("Ez egy privát portfólió. Kérlek, add meg a jelszavad a belépéshez.")
    st.stop()

# --- ADATLEKÉRDEZÉS ÉS LOGIKA ---
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
def get_market_data():
    # Élő árfolyamok és devizák lekérése egyben
    tickers = list(HOLDINGS.keys()) + ["EURUSD=X", "USDHUF=X"]
    data = yf.download(tickers, period="5d", progress=False)['Close']
    return data

st.title("SAJÁT PORTFÓLIÓ ÁLLAPOT")

with st.spinner("Élő adatok letöltése a piacról..."):
    market_data = get_market_data()
    
    eur_usd = market_data["EURUSD=X"].iloc[-1]
    usd_huf = market_data["USDHUF=X"].iloc[-1]

    portfolio_data = []
    total_value_usd = 0

    for ticker, db in HOLDINGS.items():
        if db <= 0: continue # Csak azt mutatja, amiből van legalább 1 darabod
        
        try:
            current_price = market_data[ticker].iloc[-1]
            prev_price = market_data[ticker].iloc[-2]
            day_chg_pct = ((current_price - prev_price) / prev_price) * 100
            
            is_eur = ticker.endswith(".DE")
            price_in_usd = current_price * eur_usd if is_eur else current_price
            
            value_usd = price_in_usd * db
            value_huf = value_usd * usd_huf
            total_value_usd += value_usd
            
            portfolio_data.append({
                "Név": NAME_MAP.get(ticker, ticker),
                "Ticker": ticker,
                "Darab": db,
                "Árfolyam (Saját Deviza)": f"€{current_price:,.2f}" if is_eur else f"${current_price:,.2f}",
                "Érték (USD)": value_usd,
                "Érték (HUF)": value_huf,
                "Napi Változás (%)": day_chg_pct
            })
        except:
            pass # Ha valamiért nem jön adat, átugorja hibajelzés nélkül

# --- RENDEZÉS ÉS MEGJELENÍTÉS ---
df = pd.DataFrame(portfolio_data)

if not df.empty:
    st.subheader(f"Teljes Vagyon: ${total_value_usd:,.0f} | {(total_value_usd * usd_huf):,.0f} Ft")
    
    # Gombok a rendezéshez
    col1, col2 = st.columns(2)
    with col1:
        sort_by = st.selectbox("Rendezés alapja:", ["Érték (USD)", "Napi Változás (%)", "Név"])
    with col2:
        sort_order = st.radio("Irány:", ["Csökkenő", "Növekvő"], horizontal=True)
        
    asc = True if sort_order == "Növekvő" else False
    df = df.sort_values(by=sort_by, ascending=asc)

    # Formázás a táblázathoz
    display_df = df.copy()
    display_df["Érték (USD)"] = display_df["Érték (USD)"].apply(lambda x: f"${x:,.2f}")
    display_df["Érték (HUF)"] = display_df["Érték (HUF)"].apply(lambda x: f"{x:,.0f} Ft")
    
    def color_pct(val):
        color = '#27ae60' if val > 0 else '#e74c3c' if val < 0 else 'white'
        return f'color: {color}; font-weight: bold;'
        
    st.dataframe(
        display_df.style.map(color_pct, subset=["Napi Változás (%)"]).format("{:+.2f}%", subset=["Napi Változás (%)"]),
        use_container_width=True, hide_index=True
    )

    # --- TORTADIAGRAM ---
    st.markdown("---")
    st.subheader("Portfólió Megoszlása")
    fig = px.pie(df, values='Érték (USD)', names='Név', color_discrete_sequence=px.colors.qualitative.Pastel)
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

else:
    st.info("A portfóliód jelenleg üres, vagy egyik eszközből sincs megadva darabszám.")