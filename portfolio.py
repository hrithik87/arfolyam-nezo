import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px

# --- BEÁLLÍTÁSOK ÉS MEMÓRIA ---
JELSZO = st.secrets["portfolio_jelszo"]
HOLDINGS = st.secrets["darabszamok"]

st.set_page_config(page_title="PORTFÓLIÓ KEZELŐ", layout="wide")

st.markdown("""
    <style>
    th, td { text-align: center !important; border-bottom: 1px solid #444 !important; padding: 12px !important; }
    th { border-top: 1px solid #444 !important; background-color: #1e1e1e; font-weight: bold; }
    table { width: 100%; border-collapse: collapse; }
    div[data-testid="stMetric"] { background-color: #1e1e1e; padding: 15px; border-radius: 10px; border: 1px solid #444; }
    </style>
    """, unsafe_allow_html=True)

# --- AZONOSÍTÁS ---
if "auth" not in st.session_state:
    st.session_state.auth = False

with st.sidebar:
    st.title("Azonosítás")
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
def fetch_safe_data(ticker):
    try:
        t = yf.Ticker(ticker)
        # Árfolyam lekérése (period=1mo biztosabb az ETF-eknél)
        hist = t.history(period="1mo")
        if hist.empty: return None
        
        # Market Cap külön try-ban, hogy ne rontsa el az árat
        mcap = 0
        try:
            info = t.info
            mcap = info.get('marketCap', info.get('totalAssets', 0))
            if mcap is None: mcap = 0
        except:
            mcap = 0
            
        return {
            "price": hist['Close'].iloc[-1],
            "prev": hist['Close'].iloc[-2],
            "mcap": mcap
        }
    except:
        return None

st.title("SAJÁT PORTFÓLIÓ ÁLLAPOT")

with st.spinner("Adatok szinkronizálása a piaccal..."):
    # Fix deviza lekérés
    d_usd_huf = fetch_safe_data("USDHUF=X")
    d_eur_usd = fetch_safe_data("EURUSD=X")
    
    usd_huf = d_usd_huf["price"] if d_usd_huf else 365.0
    eur_usd = d_eur_usd["price"] if d_eur_usd else 1.08

    rows = []
    total_usd = 0

    for ticker, db in HOLDINGS.items():
        if db <= 0: continue
        
        data = fetch_safe_data(ticker)
        if data:
            curr = data["price"]
            chg = ((curr - data["prev"]) / data["prev"]) * 100
            mcap = data["mcap"]
            
            is_eur = ticker.endswith(".DE")
            p_usd = curr * eur_usd if is_eur else curr
            
            val_usd = p_usd * db
            val_huf = val_usd * usd_huf
            total_usd += val_usd
            
            rows.append({
                "Név": NAME_MAP.get(ticker, ticker),
                "Ticker": ticker,
                "Darab": db,
                "Price": curr,
                "is_eur": is_eur,
                "Market cap": mcap,
                "Value USD": val_usd,
                "Value HUF": val_huf,
                "Day change %": chg
            })

# --- MEGJELENÍTÉS ---
if rows:
    df = pd.DataFrame(rows)
    
    st.metric("Teljes vagyon (USD)", f"${total_usd:,.0f}", delta=f"{(total_usd * usd_huf):,.0f} Ft", delta_color="off")
    st.markdown("---")

    ctrl1, ctrl2 = st.columns([2, 1])
    with ctrl1:
        sort_col = st.selectbox("Rendezés alapja:", ["Value USD", "Day change %", "Név"])
    with ctrl2:
        sort_dir = st.radio("Irány:", ["Csökkenő", "Növekvő"], horizontal=True)

    df = df.sort_values(by=sort_col, ascending=(sort_dir == "Növekvő"))

    # Formázott táblázat
    disp = pd.DataFrame()
    disp["Név"] = df["Név"]
    disp["Ticker"] = df["Ticker"]
    disp["Darab"] = df["Darab"].apply(lambda x: f"{x:,.4f}".rstrip('0').rstrip('.'))
    disp["Price"] = df.apply(lambda r: f"€{r['Price']:,.2f}" if r['is_eur'] else f"${r['Price']:,.2f}", axis=1)
    disp["Value USD"] = df["Value USD"].apply(lambda x: f"${x:,.2f}")
    disp["Value HUF"] = df["Value HUF"].apply(lambda x: f"{x:,.0f} Ft")
    disp["Day change %"] = df["Day change %"]

    def style_diff(v):
        color = '#27ae60' if v > 0 else '#e74c3c' if v < 0 else 'white'
        return f'color: {color}; font-weight: bold;'

    st.table(disp.style.map(style_diff, subset=["Day change %"]).format("{:+.2f}%", subset=["Day change %"]))

    # --- TORTADIAGRAM ---
    st.markdown("---")
    st.subheader("Portfólió megoszlása")
    fig = px.pie(df, values='Value USD', names='Név', 
                 color_discrete_sequence=px.colors.qualitative.Pastel)
    fig.update_traces(textinfo='percent+label', textposition='inside')
    fig.update_layout(showlegend=True, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig, use_container_width=True)

else:
    st.info("Nincs megjeleníthető adat. Ellenőrizd a darabszámokat!")