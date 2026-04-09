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
def fetch_robust_data(ticker):
    try:
        # 10 napot töltünk le, hogy biztosan legyen benne értelmezhető adat
        df = yf.download(ticker, period="10d", progress=False)
        if df.empty: return None
        
        # Yahoo MultiIndex kezelése és NaN-ok kidobása
        if isinstance(df.columns, pd.MultiIndex):
            prices = df['Close'][ticker].dropna()
        else:
            prices = df['Close'].dropna()
            
        if len(prices) < 2: return None
        
        # Market Cap külön, hogy ne rontsa el a számítást
        mcap = 0
        try:
            mcap = yf.Ticker(ticker).info.get('marketCap', 0)
        except: pass
            
        return {
            "price": float(prices.iloc[-1]),
            "prev": float(prices.iloc[-2]),
            "mcap": mcap if mcap else 0
        }
    except:
        return None

st.title("SAJÁT PORTFÓLIÓ ÁLLAPOT")

with st.spinner("Adatok szinkronizálása a piaccal..."):
    # Deviza keresztárfolyamok
    d_huf = fetch_robust_data("USDHUF=X")
    d_eur = fetch_robust_data("EURUSD=X")
    
    usd_huf = d_huf["price"] if d_huf else 365.0
    eur_usd = d_eur["price"] if d_eur else 1.08

    rows = []
    total_usd = 0

    for ticker, db in HOLDINGS.items():
        if db <= 0: continue
        
        data = fetch_robust_data(ticker)
        if data:
            curr = data["price"]
            chg = ((curr - data["prev"]) / data["prev"]) * 100
            
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
                "Market cap": data["mcap"],
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

    # Formázott táblázat - PONTOSAN A KÉRT OSZLOPRENDBEN
    disp = pd.DataFrame()
    disp["Név"] = df["Név"]
    disp["Ticker"] = df["Ticker"]
    disp["Darab"] = df["Darab"].apply(lambda x: f"{x:,.4f}".rstrip('0').rstrip('.'))
    disp["Price"] = df.apply(lambda r: f"€{r['Price']:,.2f}" if r['is_eur'] else f"${r['Price']:,.2f}", axis=1)
    # Market Cap formázás (T = Trillió, B = Billió/Milliárd)
    disp["Market cap"] = df["Market cap"].apply(lambda x: f"${x/1e12:,.2f}T" if x >= 1e12 else (f"${x/1e9:,.2f}B" if x >= 1e8 else "-"))
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
    st.info("Nincs megjeleníthető adat.")