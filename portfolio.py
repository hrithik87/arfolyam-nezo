import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px

# --- BEÁLLÍTÁSOK ---
JELSZO = st.secrets["portfolio_jelszo"]
HOLDINGS = st.secrets["darabszamok"]

st.set_page_config(page_title="PORTFÓLIÓ KEZELŐ", layout="wide")

# Nincs szükség egyedi táblázat CSS-re, mert áttérünk a modern st.dataframe-re
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
@st.cache_data(ttl=600)
def fetch_global_data():
    # Globális devizák és indexek lekérése egy csomagban
    tickers = ["EURHUF=X", "USDHUF=X", "EURUSD=X", "^GSPC", "^IXIC", "^RUT"]
    data = {}
    for t in tickers:
        try:
            hist = yf.Ticker(t).history(period="5d")
            if len(hist) >= 2:
                curr = float(hist['Close'].iloc[-1])
                prev = float(hist['Close'].iloc[-2])
                chg = ((curr - prev) / prev) * 100
                data[t] = {"price": curr, "chg": chg}
        except:
            data[t] = {"price": 0, "chg": 0}
    return data

@st.cache_data(ttl=600)
def fetch_asset_data(ticker):
    try:
        t = yf.Ticker(ticker)
        hist = t.history(period="1mo")
        if hist.empty: return None
        
        if isinstance(hist.columns, pd.MultiIndex):
            prices = hist['Close'][ticker].dropna()
        else:
            prices = hist['Close'].dropna()
            
        if len(prices) < 2: return None
        
        # Valós Yahoo Finance név és 52 hetes mélypont lekérése
        info = t.info
        name = info.get('shortName', info.get('longName', ticker))
        mcap = info.get('marketCap', info.get('totalAssets', 0))
        low52 = info.get('fiftyTwoWeekLow', 0)
            
        return {
            "price": float(prices.iloc[-1]),
            "prev": float(prices.iloc[-2]),
            "name": name,
            "mcap": mcap if mcap else 0,
            "low52": low52 if low52 else 0
        }
    except: return None

# --- FŐOLDAL ---
st.title("SAJÁT PORTFÓLIÓ")

with st.spinner("Piac szinkronizálása..."):
    glob = fetch_global_data()
    
    eur_huf = glob.get("EURHUF=X", {}).get("price", 395.0)
    usd_huf = glob.get("USDHUF=X", {}).get("price", 365.0)
    eur_usd = glob.get("EURUSD=X", {}).get("price", 1.08)

    sp_chg = glob.get("^GSPC", {}).get("chg", 0)
    ndq_chg = glob.get("^IXIC", {}).get("chg", 0)
    rut_chg = glob.get("^RUT", {}).get("chg", 0)

    def col_val(v):
        return "#27ae60" if v > 0 else "#e74c3c" if v < 0 else "#aaa"

    # Felső szürke box az indexekkel és devizákkal
    st.markdown(f"""
    <div style="background-color: #1e1e1e; padding: 15px 25px; border-radius: 10px; border: 1px solid #444; margin-bottom: 20px; display: flex; flex-wrap: wrap; gap: 30px; align-items: center; justify-content: space-around;">
        <div style="text-align: center;">
            <div style="color: #aaa; font-size: 14px; margin-bottom: 5px;">EUR/HUF</div>
            <div style="font-size: 18px; font-weight: bold;">{eur_huf:,.2f} Ft</div>
        </div>
        <div style="text-align: center;">
            <div style="color: #aaa; font-size: 14px; margin-bottom: 5px;">USD/HUF</div>
            <div style="font-size: 18px; font-weight: bold;">{usd_huf:,.2f} Ft</div>
        </div>
        <div style="border-left: 1px solid #444; height: 40px;"></div>
        <div style="text-align: center;">
            <div style="color: #aaa; font-size: 14px; margin-bottom: 5px;">S&P 500</div>
            <div style="font-size: 18px; font-weight: bold; color: {col_val(sp_chg)};">{sp_chg:+.2f}%</div>
        </div>
        <div style="text-align: center;">
            <div style="color: #aaa; font-size: 14px; margin-bottom: 5px;">Nasdaq</div>
            <div style="font-size: 18px; font-weight: bold; color: {col_val(ndq_chg)};">{ndq_chg:+.2f}%</div>
        </div>
        <div style="text-align: center;">
            <div style="color: #aaa; font-size: 14px; margin-bottom: 5px;">Russell 2000</div>
            <div style="font-size: 18px; font-weight: bold; color: {col_val(rut_chg)};">{rut_chg:+.2f}%</div>
        </div>
    </div>
    """.replace(",", " "), unsafe_allow_html=True)

    rows = []
    total_usd = 0

    for ticker, db in HOLDINGS.items():
        if db <= 0: continue
        data = fetch_asset_data(ticker)
        if data:
            curr = data["price"]
            chg = ((curr - data["prev"]) / data["prev"]) * 100
            is_eur = ticker.endswith(".DE")
            p_usd = curr * eur_usd if is_eur else curr
            val_usd = p_usd * db
            total_usd += val_usd
            
            rows.append({
                "Név": data["name"],
                "Ticker": ticker,
                "Darab": db,
                "Árfolyam": curr,
                "is_eur": is_eur,
                "52w low": data["low52"],
                "Market cap": data["mcap"],
                "USD érték": val_usd,
                "HUF érték": val_usd * usd_huf,
                "Napi vált. %": chg
            })

# --- MEGJELENÍTÉS ÉS FORMÁZÁS ---
if rows:
    df = pd.DataFrame(rows)
    df["Portfólió hányad"] = (df["USD érték"] / total_usd) * 100 if total_usd > 0 else 0
    
    # Fő Érték doboz (nyilacska nélkül, egyedi dizájnnal)
    st.markdown(f"""
    <div style="background-color: #1e1e1e; padding: 25px; border-radius: 10px; border: 1px solid #444; margin-bottom: 30px;">
        <div style="color: #aaa; font-size: 16px; margin-bottom: 5px;">Érték</div>
        <div style="font-size: 42px; font-weight: bold;">${total_usd:,.0f}</div>
        <div style="color: #ccc; font-size: 20px; margin-top: 5px;">{(total_usd * usd_huf):,.0f} Ft</div>
    </div>
    """.replace(",", " "), unsafe_allow_html=True)

    # Megjelenítendő adatkeret összerakása
    disp = pd.DataFrame()
    disp["Név"] = df["Név"]
    disp["Ticker"] = df["Ticker"]
    disp["Darab"] = df["Darab"].apply(lambda x: f"{x:,.4f}".replace(",", " ").rstrip('0').rstrip('.'))
    disp["Árfolyam"] = df.apply(lambda r: f"{'€' if r['is_eur'] else '$'}{r['Árfolyam']:,.2f}".replace(",", " "), axis=1)
    disp["52w low"] = df.apply(lambda r: f"{'€' if r['is_eur'] else '$'}{r['52w low']:,.2f}".replace(",", " ") if r['52w low'] > 0 else "-", axis=1)
    disp["Market cap"] = df["Market cap"].apply(lambda x: f"${x/1e12:,.2f}T".replace(",", " ") if x >= 1e12 else (f"${x/1e9:,.2f}B".replace(",", " ") if x >= 1e8 else "-"))
    
    # Ezek az oszlopok tiszta számok maradnak a háttérben, hogy a fejléc-kattintásos rendezés tökéletesen működjön matematikailag
    disp["USD érték"] = df["USD érték"]
    disp["HUF érték"] = df["HUF érték"]
    disp["Portfólió hányad"] = df["Portfólió hányad"]
    disp["Napi vált. %"] = df["Napi vált. %"]

    # Szóközös formázás az élő (rendezhető) szám oszlopokra
    formatters = {
        "USD érték": lambda x: f"${x:,.2f}".replace(",", " "),
        "HUF érték": lambda x: f"{x:,.0f} Ft".replace(",", " "),
        "Portfólió hányad": lambda x: f"{x:,.2f}%".replace(",", " "),
        "Napi vált. %": lambda x: f"{x:+.2f}%".replace(",", " ")
    }

    def style_diff(v):
        color = '#27ae60' if v > 0 else '#e74c3c' if v < 0 else 'white'
        return f'color: {color}; font-weight: bold;'

    # A st.dataframe alapból egységes, sűrűbb sormagasságot ad, és a fejlécre kattintva rendezhető
    styled_df = disp.style.format(formatters).map(style_diff, subset=["Napi vált. %"])
    st.dataframe(styled_df, use_container_width=True, hide_index=True)

    # --- TORTADIAGRAM ---
    st.markdown("---")
    st.subheader("Portfólió diagram")
    
    fig = px.pie(df, values='USD érték', names='Ticker', color_discrete_sequence=px.colors.qualitative.Pastel)
    # Címkék a körön kívülre, vonalkákkal
    fig.update_traces(textinfo='label+percent', textposition='outside', marker=dict(line=dict(color='#000000', width=1)))
    fig.update_layout(showlegend=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(t=40, b=40, l=40, r=40))
    st.plotly_chart(fig, use_container_width=True)

else:
    st.info("Nincs megjeleníthető adat. Ellenőrizd a darabszámokat a Secrets-ben!")
