import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime
import numpy as np

# --- BEÁLLÍTÁSOK ÉS MEMÓRIA ---
JELSZO = st.secrets["portfolio_jelszo"]
HOLDINGS = st.secrets["darabszamok"]

st.set_page_config(page_title="PORTFÓLIÓ KEZELŐ", layout="wide")

# CSS: Letisztult, modern táblázat stílus
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
@st.cache_data(ttl=600)
def fetch_global_data():
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

@st.cache_data(ttl=1200) # Hosszabb cache a nagy adathalmaz miatt
def fetch_asset_history(ticker):
    try:
        t = yf.Ticker(ticker)
        # 1 éves adat a történelmi charthoz és YTD-hez
        hist = t.history(period="1y")
        if hist.empty: return None
        
        if isinstance(hist.columns, pd.MultiIndex):
            prices = hist['Close'][ticker].dropna()
        else:
            prices = hist['Close'].dropna()
            
        if len(prices) < 2: return None

        info = t.info
        name = info.get('shortName', info.get('longName', ticker))
        mcap = info.get('marketCap', info.get('totalAssets', 0))
        low52 = info.get('fiftyTwoWeekLow', 0)

        # Időszaki árak kiszámítása
        curr_price = float(prices.iloc[-1])
        prev_price = float(prices.iloc[-2])
        
        # 7 nap visszatekintés, ha nincs, akkor a legkorábbi adat
        p_7d_idx = -7 if len(prices) >= 7 else 0
        price_7d = float(prices.iloc[p_7d_idx])
        
        # 30 nap visszatekintés, ha nincs, akkor a legkorábbi adat
        p_30d_idx = -30 if len(prices) >= 30 else 0
        price_30d = float(prices.iloc[p_30d_idx])
        
        # YTD ár keresése (év első kereskedési napja)
        current_year = datetime.now().year
        ytd_prices = prices[prices.index.year == current_year]
        price_ytd = float(ytd_prices.iloc[0]) if not ytd_prices.empty else float(prices.iloc[0])

        return {
            "name": name,
            "prices_series": prices, # A teljes 1 éves adatsor
            "curr": curr_price,
            "prev": prev_price,
            "p_7d": price_7d,
            "p_30d": price_30d,
            "p_ytd": price_ytd,
            "mcap": mcap if mcap else 0,
            "low52": low52 if low52 else 0
        }
    except: return None

# --- NÉV ÉS TIKKER CSERÉK, ÚJ INSTRUMENTUM ---
NAME_RENAME_MAP = {
    "VWCE.DE": "iShares MSCI World Small Cap UCITS ETF", # Hibás név a kódban, a JustETF alapján: "Vanguard FTSE All-World UCITS ETF"
    "ZPRV.DE": "iShares MSCI USA Small Cap Value Factor UCITS ETF",
    "IUSN.DE": "iShares MSCI World Small Cap UCITS ETF", # Ez a név maradhat
    "CBTC.DE": "21Shares Core Bitcoin ETP" # Új név
}

# Javítom a korábbi hibámat, a névcsere szótárt pontosítom
CORRECT_NAME_RENAME_MAP = {
    "VWCE.DE": "Vanguard FTSE All-World UCITS ETF (Dist)",
    "ZPRV.DE": "iShares MSCI USA Small Cap Value Factor UCITS ETF",
    "IUSN.DE": "iShares MSCI World Small Cap UCITS ETF",
    "CBTC.DE": "21Shares Bitcoin Core ETP" # A felhasználó kért neve
}

# --- FŐOLDAL ---
st.title("SAJÁT PORTFÓLIÓ")

with st.spinner("Piac szinkronizálása és történelmi adatok letöltése..."):
    glob = fetch_global_data()
    eur_huf = glob.get("EURHUF=X", {}).get("price", 395.0)
    usd_huf = glob.get("USDHUF=X", {}).get("price", 365.0)
    eur_usd = glob.get("EURUSD=X", {}).get("price", 1.08)
    sp_chg = glob.get("^GSPC", {}).get("chg", 0)
    ndq_chg = glob.get("^IXIC", {}).get("chg", 0)
    rut_chg = glob.get("^RUT", {}).get("chg", 0)

    def col_val(v): return "#27ae60" if v > 0 else "#e74c3c" if v < 0 else "#aaa"

    # Felső szürke box az indexekkel és devizákkal (ezresválasztó szóköz!)
    st.markdown(f"""
    <div style="background-color: #1e1e1e; padding: 15px 25px; border-radius: 10px; border: 1px solid #444; margin-bottom: 20px; display: flex; flex-wrap: wrap; gap: 30px; align-items: center; justify-content: space-around;">
        <div style="text-align: center;"><div style="color: #aaa; font-size: 14px; margin-bottom: 5px;">EUR/HUF</div><div style="font-size: 18px; font-weight: bold;">{eur_huf:,.2f} Ft</div></div>
        <div style="text-align: center;"><div style="color: #aaa; font-size: 14px; margin-bottom: 5px;">USD/HUF</div><div style="font-size: 18px; font-weight: bold;">{usd_huf:,.2f} Ft</div></div>
        <div style="border-left: 1px solid #444; height: 40px;"></div>
        <div style="text-align: center;"><div style="color: #aaa; font-size: 14px; margin-bottom: 5px;">S&P 500</div><div style="font-size: 18px; font-weight: bold; color: {col_val(sp_chg)};">{sp_chg:+.2f}%</div></div>
        <div style="text-align: center;"><div style="color: #aaa; font-size: 14px; margin-bottom: 5px;">Nasdaq</div><div style="font-size: 18px; font-weight: bold; color: {col_val(ndq_chg)};">{ndq_chg:+.2f}%</div></div>
        <div style="text-align: center;"><div style="color: #aaa; font-size: 14px; margin-bottom: 5px;">Russell 2000</div><div style="font-size: 18px; font-weight: bold; color: {col_val(rut_chg)};">{rut_chg:+.2f}%</div></div>
    </div>
    """.replace(",", " "), unsafe_allow_html=True)

    rows = []
    
    # Portfólió szintű aggregált értékekhez (most, tegnap, 7d, 30d, ytd)
    tot_usd_now = 0
    tot_usd_prev = 0
    tot_usd_7d = 0
    tot_usd_30d = 0
    tot_usd_ytd = 0
    
    # DataFrame a történelmi charthoz
    portfolio_history = pd.DataFrame()

    for ticker, db in HOLDINGS.items():
        if db <= 0: continue
        data = fetch_asset_history(ticker)
        if data:
            is_eur = ticker.endswith(".DE")
            # Európai papírok esetén az ár és az idősor dollárosítása
            multiplier = eur_usd if is_eur else 1.0
            
            curr_val = data["curr"] * multiplier * db
            prev_val = data["prev"] * multiplier * db
            v_7d = data["p_7d"] * multiplier * db
            v_30d = data["p_30d"] * multiplier * db
            v_ytd = data["p_ytd"] * multiplier * db
            
            tot_usd_now += curr_val
            tot_usd_prev += prev_val
            tot_usd_7d += v_7d
            tot_usd_30d += v_30d
            tot_usd_ytd += v_ytd
            
            # Idősoros érték a portfólió charthoz (ffill() és outer join arobosztusabb kezelésért)
            asset_history_usd = (data["prices_series"] * multiplier * db).ffill()
            if portfolio_history.empty:
                portfolio_history = asset_history_usd.to_frame(name=ticker)
            else:
                portfolio_history = portfolio_history.join(asset_history_usd.rename(ticker), how='outer')

            # Névcsere, ha a szótárban szerepel a tikker
            final_name = CORRECT_NAME_RENAME_MAP.get(ticker, data["name"])

            # 7 napos adatsor a sparkline-hoz (csak az utolsó 7, vagy kevesebb)
            sparkline_data = data["prices_series"].ffill().tail(7).tolist()

            rows.append({
                "Név": final_name,
                "Ticker": ticker,
                "Darab": db,
                "Árfolyam": data["curr"],
                "is_eur": is_eur,
                "52w low": data["low52"],
                "Market cap": data["mcap"],
                "USD érték": curr_val,
                "Napi vált. %": ((curr_val - prev_val) / prev_val) * 100 if prev_val else 0,
                "Napi vált. USD": curr_val - prev_val,
                "7d %": ((curr_val - v_7d) / v_7d) * 100 if v_7d else 0,
                "7d USD": curr_val - v_7d,
                "30d %": ((curr_val - v_30d) / v_30d) * 100 if v_30d else 0,
                "30d USD": curr_val - v_30d,
                "YTD %": ((curr_val - v_ytd) / v_ytd) * 100 if v_ytd else 0,
                "YTD USD": curr_val - v_ytd,
                "7d Chart": sparkline_data
            })

# --- MEGJELENÍTÉS ---
if rows:
    df = pd.DataFrame(rows)
    df["Portfólió hányad"] = (df["USD érték"] / tot_usd_now) * 100 if tot_usd_now > 0 else 0

    # Teljes portfólió metrikák (számítás és színezés)
    pf_chg_day_pct = ((tot_usd_now - tot_usd_prev) / tot_usd_prev) * 100 if tot_usd_prev else 0
    pf_chg_day_usd = tot_usd_now - tot_usd_prev
    pf_chg_7d_pct = ((tot_usd_now - tot_usd_7d) / tot_usd_7d) * 100 if tot_usd_7d else 0
    pf_chg_7d_usd = tot_usd_now - tot_usd_7d
    pf_chg_30d_pct = ((tot_usd_now - tot_usd_30d) / tot_usd_30d) * 100 if tot_usd_30d else 0
    pf_chg_30d_usd = tot_usd_now - tot_usd_30d
    pf_chg_ytd_pct = ((tot_usd_now - tot_usd_ytd) / tot_usd_ytd) * 100 if tot_usd_ytd else 0
    pf_chg_ytd_usd = tot_usd_now - tot_usd_ytd

    def fmt_c(v): return "green" if v > 0 else "red" if v < 0 else "gray"

    # Fő Érték doboz (ezresválasztó szóköz, nyilacska nélkül, új teljes pf metrikák)
    st.markdown(f"""
    <div style="background-color: #1e1e1e; padding: 25px; border-radius: 10px; border: 1px solid #444; margin-bottom: 30px;">
        <div style="color: #aaa; font-size: 16px; margin-bottom: 5px;">Érték</div>
        <div style="font-size: 42px; font-weight: bold;">${tot_usd_now:,.0f}</div>
        <div style="color: #ccc; font-size: 20px; margin-top: 5px; margin-bottom: 15px;">{(tot_usd_now * usd_huf):,.0f} Ft</div>
        <div style="display: flex; gap: 20px; font-size: 14px;">
            <div>Napi: <span style="color:{fmt_c(pf_chg_day_pct)};">{pf_chg_day_pct:+.2f}%</span> (<span style="color:{fmt_c(pf_chg_day_usd)};">${pf_chg_day_usd:+,.0f}</span>)</div>
            <div>7d: <span style="color:{fmt_c(pf_chg_7d_pct)};">{pf_chg_7d_pct:+.2f}%</span> (<span style="color:{fmt_c(pf_chg_7d_usd)};">${pf_chg_7d_usd:+,.0f}</span>)</div>
            <div>30d: <span style="color:{fmt_c(pf_chg_30d_pct)};">{pf_chg_30d_pct:+.2f}%</span> (<span style="color:{fmt_c(pf_chg_30d_usd)};">${pf_chg_30d_usd:+,.0f}</span>)</div>
            <div>YTD: <span style="color:{fmt_c(pf_chg_ytd_pct)};">{pf_chg_ytd_pct:+.2f}%</span> (<span style="color:{fmt_c(pf_chg_ytd_usd)};">${pf_chg_ytd_usd:+,.0f}</span>)</div>
        </div>
    </div>
    """.replace(",", " "), unsafe_allow_html=True)

    # Táblázat előkészítése (ezresválasztó szóköz!)
    disp = pd.DataFrame()
    disp["Név"] = df["Név"]
    disp["Ticker"] = df["Ticker"]
    disp["Darab"] = df["Darab"].apply(lambda x: f"{x:,.4f}".replace(",", " ").rstrip('0').rstrip('.'))
    disp["Árfolyam"] = df.apply(lambda r: f"{'€' if r['is_eur'] else '$'}{r['Árfolyam']:,.2f}".replace(",", " "), axis=1)
    disp["52w low"] = df.apply(lambda r: f"{'€' if r['is_eur'] else '$'}{r['52w low']:,.2f}".replace(",", " ") if r['52w low'] > 0 else "-", axis=1)
    disp["Market cap"] = df["Market cap"].apply(lambda x: f"${x/1e12:,.2f}T".replace(",", " ") if x >= 1e12 else (f"${x/1e9:,.2f}B".replace(",", " ") if x >= 1e8 else "-"))
    disp["USD érték"] = df["USD érték"]
    disp["Portfólió hányad"] = df["Portfólió hányad"]
    
    # Új időszaki oszlopok a táblázatba (számok maradnak a rendezéshez)
    disp["Napi vált. %"] = df["Napi vált. %"]
    disp["Napi vált. USD"] = df["Napi vált. USD"]
    disp["7d %"] = df["7d %"]
    disp["7d USD"] = df["7d USD"]
    disp["30d %"] = df["30d %"]
    disp["30d USD"] = df["30d USD"]
    disp["YTD %"] = df["YTD %"]
    disp["YTD USD"] = df["YTD USD"]
    
    # Sparkline adat beszúrása
    disp["7d Chart"] = df["7d Chart"]

    # Formázók az st.dataframe-hez (USD formázás, ezresválasztó szóköz, sparkline)
    format_dict = {
        "USD érték": st.column_config.NumberColumn("USD érték", format="$ %.2f"),
        "Portfólió hányad": st.column_config.NumberColumn("Portfólió hányad", format="%.2f %%"),
        "Napi vált. %": st.column_config.NumberColumn("Napi vált. %", format="%+.2f %%"),
        "Napi vált. USD": st.column_config.NumberColumn("Napi vált. USD", format="$ %+.2f"),
        "7d %": st.column_config.NumberColumn("7d %", format="%+.2f %%"),
        "7d USD": st.column_config.NumberColumn("7d USD", format="$ %+.2f"),
        "30d %": st.column_config.NumberColumn("30d %", format="%+.2f %%"),
        "30d USD": st.column_config.NumberColumn("30d USD", format="$ %+.2f"),
        "YTD %": st.column_config.NumberColumn("YTD %", format="%+.2f %%"),
        "YTD USD": st.column_config.NumberColumn("YTD USD", format="$ %+.2f"),
        "7d Chart": st.column_config.LineChartColumn("7d Chart", y_min=None, y_max=None)
    }

    # Színformázó függvény: piros mínusz, zöld plusz
    def style_diff(v):
        color = '#27ae60' if v > 0 else '#e74c3c' if v < 0 else 'white'
        return f'color: {color}; font-weight: bold;'

    # Kiszámoljuk a pontos magasságot, hogy ne legyen görgetősáv (36 pixel / sor + fejléc)
    table_height = int((len(disp) + 1) * 36)

    # Megjelenítés (height paraméter beállítva a teljes listához, st.dataframe modern rendezése, színformázás!)
    # Alkalmazom a színformázást az összes százalékos oszlopra a táblázatban
    styled_df = disp.style.format(format_dict).map(style_diff, subset=["Napi vált. %", "7d %", "30d %", "YTD %"])
    st.dataframe(styled_df, use_container_width=True, hide_index=True, height=table_height)

    # --- HISTORICAL CHART (éves teljes pf USD grafikon) ---
    st.markdown("---")
    st.subheader("Portfólió teljes éves eredménye, USD")
    if not portfolio_history.empty:
        # Tiszta történelmi adatsor készítése
        portfolio_history_ffill = portfolio_history.ffill()
        total_history = portfolio_history_ffill.sum(axis=1) # Sorok (eszközök) összeadása
        
        # Plotly chart készítése, napi beosztással
        fig_hist = px.line(x=total_history.index, y=total_history.values, 
                           labels={'x': 'Dátum', 'y': 'Érték (USD)'})
        fig_hist.update_traces(line_color='#27ae60')
        fig_hist.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                               xaxis_title="", yaxis_title="USD",
                               hovermode="x unified")
        # Interaktív időablak választó gombok (1m, 3m, 6m, YTD, 1y)
        fig_hist.update_xaxes(
            rangeselector=dict(
                buttons=list([
                    dict(count=1, label="1m", step="month", stepmode="backward"),
                    dict(count=3, label="3m", step="month", stepmode="backward"),
                    dict(count=6, label="6m", step="month", stepmode="backward"),
                    dict(count=1, label="YTD", step="year", stepmode="todate"),
                    dict(count=1, label="1y", step="year", stepmode="backward"),
                    dict(step="all")
                ])
            )
        )
        st.plotly_chart(fig_hist, use_container_width=True)

    # --- TORTADIAGRAM (letisztított legendás változat) ---
    st.markdown("---")
    st.subheader("Portfólió diagram")
    fig_pie = px.pie(df, values='USD érték', names='Ticker', color_discrete_sequence=px.colors.qualitative.Pastel)
    # Eltávolítom a diagramon lévő feliratokat a zsúfoltság miatt, de bekapcsolom a legendát
    fig_pie.update_traces(textinfo='none', marker=dict(line=dict(color='#000000', width=1)))
    # A legenda elhelyezése és formázása
    fig_pie.update_layout(showlegend=True, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                           legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.05))
    st.plotly_chart(fig_pie, use_container_width=True)

else:
    st.info("Nincs megjeleníthető adat.")
