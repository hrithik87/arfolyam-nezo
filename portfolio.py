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

st.markdown("""
    <style>
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

@st.cache_data(ttl=1200) 
def fetch_asset_history(ticker):
    try:
        t = yf.Ticker(ticker)
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

        curr_price = float(prices.iloc[-1])
        prev_price = float(prices.iloc[-2])
        
        p_7d_idx = -7 if len(prices) >= 7 else 0
        price_7d = float(prices.iloc[p_7d_idx])
        
        p_30d_idx = -30 if len(prices) >= 30 else 0
        price_30d = float(prices.iloc[p_30d_idx])
        
        current_year = datetime.now().year
        ytd_prices = prices[prices.index.year == current_year]
        price_ytd = float(ytd_prices.iloc[0]) if not ytd_prices.empty else float(prices.iloc[0])

        return {
            "name": name,
            "prices_series": prices,
            "curr": curr_price,
            "prev": prev_price,
            "p_7d": price_7d,
            "p_30d": price_30d,
            "p_ytd": price_ytd,
            "mcap": mcap if mcap else 0,
            "low52": low52 if low52 else 0
        }
    except: return None

# Névcsere a pontos elvárások alapján
NAME_RENAME_MAP = {
    "VWCE.DE": "FTSE All-World ETF",
    "ZPRV.DE": "MSCI USA Small Cap Value ETF",
    "IUSN.DE": "MSCI World Small Cap ETF",
    "CBTC.DE": "21shares Bitcoin Core ETP",
    "21BC.DE": "21shares Bitcoin Core ETP"
}

# --- FŐOLDAL ---
st.title("SAJÁT PORTFÓLIÓ")

with st.spinner("Piac szinkronizálása és adatok letöltése..."):
    glob = fetch_global_data()
    eur_huf = glob.get("EURHUF=X", {}).get("price", 395.0)
    usd_huf = glob.get("USDHUF=X", {}).get("price", 365.0)
    eur_usd = glob.get("EURUSD=X", {}).get("price", 1.08)
    sp_chg = glob.get("^GSPC", {}).get("chg", 0)
    ndq_chg = glob.get("^IXIC", {}).get("chg", 0)
    rut_chg = glob.get("^RUT", {}).get("chg", 0)

    def col_val(v): return "#27ae60" if v > 0 else "#e74c3c" if v < 0 else "#aaa"

    # Felső szürke box - Formázott számokkal, szóközös ezresválasztóval
    str_eur_huf = f"{eur_huf:,.2f}".replace(",", " ")
    str_usd_huf = f"{usd_huf:,.2f}".replace(",", " ")
    str_sp_chg = f"{sp_chg:+.2f}".replace(",", " ")
    str_ndq_chg = f"{ndq_chg:+.2f}".replace(",", " ")
    str_rut_chg = f"{rut_chg:+.2f}".replace(",", " ")

    st.markdown(f"""
    <div style="background-color: #1e1e1e; padding: 15px 25px; border-radius: 10px; border: 1px solid #444; margin-bottom: 20px; display: flex; flex-wrap: wrap; gap: 30px; align-items: center; justify-content: space-around;">
        <div style="text-align: center;"><div style="color: #aaa; font-size: 14px; margin-bottom: 5px;">EUR/HUF</div><div style="font-size: 18px; font-weight: bold;">{str_eur_huf} Ft</div></div>
        <div style="text-align: center;"><div style="color: #aaa; font-size: 14px; margin-bottom: 5px;">USD/HUF</div><div style="font-size: 18px; font-weight: bold;">{str_usd_huf} Ft</div></div>
        <div style="border-left: 1px solid #444; height: 40px;"></div>
        <div style="text-align: center;"><div style="color: #aaa; font-size: 14px; margin-bottom: 5px;">S&P 500</div><div style="font-size: 18px; font-weight: bold; color: {col_val(sp_chg)};">{str_sp_chg}%</div></div>
        <div style="text-align: center;"><div style="color: #aaa; font-size: 14px; margin-bottom: 5px;">Nasdaq</div><div style="font-size: 18px; font-weight: bold; color: {col_val(ndq_chg)};">{str_ndq_chg}%</div></div>
        <div style="text-align: center;"><div style="color: #aaa; font-size: 14px; margin-bottom: 5px;">Russell 2000</div><div style="font-size: 18px; font-weight: bold; color: {col_val(rut_chg)};">{str_rut_chg}%</div></div>
    </div>
    """, unsafe_allow_html=True)

    rows = []
    
    tot_usd_now = 0
    tot_usd_prev = 0
    tot_usd_7d = 0
    tot_usd_30d = 0
    tot_usd_ytd = 0
    
    portfolio_history = pd.DataFrame()

    for ticker, db in HOLDINGS.items():
        if db <= 0: continue
        
        # Tikker átirányítás a Yahoo Finance anomália miatt
        yahoo_ticker = "21BC.DE" if ticker == "CBTC.DE" else ticker
        
        data = fetch_asset_history(yahoo_ticker)
        if data:
            is_eur = yahoo_ticker.endswith(".DE")
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
            
            asset_history_usd = (data["prices_series"] * multiplier * db).ffill()
            if portfolio_history.empty:
                portfolio_history = asset_history_usd.to_frame(name=ticker)
            else:
                portfolio_history = portfolio_history.join(asset_history_usd.rename(ticker), how='outer')

            final_name = NAME_RENAME_MAP.get(ticker, data["name"])
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
                "HUF érték": curr_val * usd_huf,  # <-- HUF érték visszatéve a számításba
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

    pf_chg_day_pct = ((tot_usd_now - tot_usd_prev) / tot_usd_prev) * 100 if tot_usd_prev else 0
    pf_chg_day_usd = tot_usd_now - tot_usd_prev
    pf_chg_7d_pct = ((tot_usd_now - tot_usd_7d) / tot_usd_7d) * 100 if tot_usd_7d else 0
    pf_chg_7d_usd = tot_usd_now - tot_usd_7d
    pf_chg_30d_pct = ((tot_usd_now - tot_usd_30d) / tot_usd_30d) * 100 if tot_usd_30d else 0
    pf_chg_30d_usd = tot_usd_now - tot_usd_30d
    pf_chg_ytd_pct = ((tot_usd_now - tot_usd_ytd) / tot_usd_ytd) * 100 if tot_usd_ytd else 0
    pf_chg_ytd_usd = tot_usd_now - tot_usd_ytd

    def fmt_c(v): return "green" if v > 0 else "red" if v < 0 else "gray"

    str_tot_usd = f"{tot_usd_now:,.0f}".replace(",", " ")
    str_tot_huf = f"{(tot_usd_now * usd_huf):,.0f}".replace(",", " ")
    
    str_day_pct = f"{pf_chg_day_pct:+.2f}".replace(",", " ")
    str_day_usd = f"{pf_chg_day_usd:+,.0f}".replace(",", " ").replace("-", "") 
    sign_day_usd = "-" if pf_chg_day_usd < 0 else "+"

    str_7d_pct = f"{pf_chg_7d_pct:+.2f}".replace(",", " ")
    str_7d_usd = f"{pf_chg_7d_usd:+,.0f}".replace(",", " ").replace("-", "")
    sign_7d_usd = "-" if pf_chg_7d_usd < 0 else "+"

    str_30d_pct = f"{pf_chg_30d_pct:+.2f}".replace(",", " ")
    str_30d_usd = f"{pf_chg_30d_usd:+,.0f}".replace(",", " ").replace("-", "")
    sign_30d_usd = "-" if pf_chg_30d_usd < 0 else "+"

    str_ytd_pct = f"{pf_chg_ytd_pct:+.2f}".replace(",", " ")
    str_ytd_usd = f"{pf_chg_ytd_usd:+,.0f}".replace(",", " ").replace("-", "")
    sign_ytd_usd = "-" if pf_chg_ytd_usd < 0 else "+"

    st.markdown(f"""
    <div style="background-color: #1e1e1e; padding: 25px; border-radius: 10px; border: 1px solid #444; margin-bottom: 30px;">
        <div style="color: #aaa; font-size: 16px; margin-bottom: 5px;">Érték</div>
        <div style="font-size: 42px; font-weight: bold;">${str_tot_usd}</div>
        <div style="color: #ccc; font-size: 20px; margin-top: 5px; margin-bottom: 15px;">{str_tot_huf} Ft</div>
        <div style="display: flex; gap: 20px; font-size: 14px;">
            <div>Napi: <span style="color:{fmt_c(pf_chg_day_pct)};">{str_day_pct}%</span> (<span style="color:{fmt_c(pf_chg_day_usd)};">{sign_day_usd}${str_day_usd}</span>)</div>
            <div>7d: <span style="color:{fmt_c(pf_chg_7d_pct)};">{str_7d_pct}%</span> (<span style="color:{fmt_c(pf_chg_7d_usd)};">{sign_7d_usd}${str_7d_usd}</span>)</div>
            <div>30d: <span style="color:{fmt_c(pf_chg_30d_pct)};">{str_30d_pct}%</span> (<span style="color:{fmt_c(pf_chg_30d_usd)};">{sign_30d_usd}${str_30d_usd}</span>)</div>
            <div>YTD: <span style="color:{fmt_c(pf_chg_ytd_pct)};">{str_ytd_pct}%</span> (<span style="color:{fmt_c(pf_chg_ytd_usd)};">{sign_ytd_usd}${str_ytd_usd}</span>)</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    disp = pd.DataFrame()
    disp["Név"] = df["Név"]
    disp["Ticker"] = df["Ticker"]
    disp["Darab"] = df["Darab"].apply(lambda x: f"{x:,.4f}".replace(",", " ").rstrip('0').rstrip('.'))
    disp["Árfolyam"] = df.apply(lambda r: f"{'€' if r['is_eur'] else '$'}{r['Árfolyam']:,.2f}".replace(",", " "), axis=1)
    disp["52w low"] = df.apply(lambda r: f"{'€' if r['is_eur'] else '$'}{r['52w low']:,.2f}".replace(",", " ") if r['52w low'] > 0 else "-", axis=1)
    disp["Market cap"] = df["Market cap"].apply(lambda x: f"${x/1e12:,.2f}T".replace(",", " ") if x >= 1e12 else (f"${x/1e9:,.2f}B".replace(",", " ") if x >= 1e8 else "-"))
    
    disp["USD érték"] = df["USD érték"]
    disp["HUF érték"] = df["HUF érték"]  # <-- HUF érték oszlop beillesztve
    disp["Portfólió hányad"] = df["Portfólió hányad"]
    disp["Napi vált. %"] = df["Napi vált. %"]
    disp["Napi vált. USD"] = df["Napi vált. USD"]
    disp["7d %"] = df["7d %"]
    disp["7d USD"] = df["7d USD"]
    disp["30d %"] = df["30d %"]
    disp["30d USD"] = df["30d USD"]
    disp["YTD %"] = df["YTD %"]
    disp["YTD USD"] = df["YTD USD"]
    disp["7d Chart"] = df["7d Chart"]

    # Szóközös formázó függvények
    def fmt_usd(x): return f"${x:,.2f}".replace(",", " ").replace("$-", "-$")
    def fmt_usd_plus(x): return f"${x:+,.2f}".replace(",", " ").replace("$-", "-$").replace("$+", "+$")
    def fmt_huf(x): return f"{x:,.0f} Ft".replace(",", " ") # <-- HUF formázó
    def fmt_pct(x): return f"{x:,.2f}%".replace(",", " ")
    def fmt_pct_plus(x): return f"{x:+,.2f}%".replace(",", " ")

    format_dict = {
        "USD érték": fmt_usd,
        "HUF érték": fmt_huf, # <-- HUF formázó bekapcsolva
        "Portfólió hányad": fmt_pct,
        "Napi vált. %": fmt_pct_plus,
        "Napi vált. USD": fmt_usd_plus,
        "7d %": fmt_pct_plus,
        "7d USD": fmt_usd_plus,
        "30d %": fmt_pct_plus,
        "30d USD": fmt_usd_plus,
        "YTD %": fmt_pct_plus,
        "YTD USD": fmt_usd_plus,
    }

    def style_diff(v):
        color = '#27ae60' if v > 0 else '#e74c3c' if v < 0 else 'white'
        return f'color: {color}; font-weight: bold;'

    styled_df = disp.style.format(format_dict).map(style_diff, subset=["Napi vált. %", "Napi vált. USD", "7d %", "7d USD", "30d %", "30d USD", "YTD %", "YTD USD"])

    # Streamlit oszlop beállítások: KÖZÉPRE IGAZÍTÁS MINDENHOL
    col_cfg = {col: st.column_config.Column(alignment="center") for col in disp.columns if col != "7d Chart"}
    col_cfg["7d Chart"] = st.column_config.LineChartColumn("7d Chart", y_min=None, y_max=None)

    table_height = int((len(disp) + 1) * 36)

    st.dataframe(styled_df, use_container_width=True, hide_index=True, column_config=col_cfg, height=table_height)

    # --- HISTORICAL CHART ---
    st.markdown("---")
    st.subheader("Portfólió teljes éves eredménye, USD")
    if not portfolio_history.empty:
        portfolio_history_ffill = portfolio_history.ffill()
        total_history = portfolio_history_ffill.sum(axis=1)
        
        fig_hist = px.line(x=total_history.index, y=total_history.values, 
                           labels={'x': 'Dátum', 'y': 'Érték (USD)'})
        fig_hist.update_traces(line_color='#27ae60')
        fig_hist.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                               xaxis_title="", yaxis_title="USD",
                               hovermode="x unified")
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

    # --- TORTADIAGRAM ---
    st.markdown("---")
    st.subheader("Portfólió diagram")
    fig_pie = px.pie(df, values='USD érték', names='Ticker', color_discrete_sequence=px.colors.qualitative.Pastel)
    fig_pie.update_traces(textinfo='none', marker=dict(line=dict(color='#000000', width=1)))
    fig_pie.update_layout(showlegend=True, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                           legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.05))
    st.plotly_chart(fig_pie, use_container_width=True)

else:
    st.info("Nincs megjeleníthető adat.")
