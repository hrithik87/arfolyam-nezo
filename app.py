import streamlit as st
import yfinance as yf
import requests
import pandas as pd
import numpy as np
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

# --- BEÁLLÍTÁSOK ---
JELSZO = st.secrets["app_jelszo"] 

st.set_page_config(page_title="FONTOSABB ÁRFOLYAMOK", layout="wide")

# CSS: Finomhangolás
st.markdown("""
    <style>
    div[data-testid="stDataFrame"] { width: 100%; }
    </style>
    """, unsafe_allow_html=True)

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

# --- FORMÁZÓ FÜGGVÉNYEK (A SZÁMOK HÁTTÉRBELI MEGŐRZÉSÉVEL A RENDEZÉSHEZ) ---
def format_num_str(val):
    if abs(val) < 1 and val != 0:
        formatted = "{:,.8f}".format(val).replace(",", " ").rstrip('0').rstrip('.')
        if "." in formatted and len(formatted.split('.')[-1]) < 2:
            formatted = "{:,.2f}".format(val).replace(",", " ")
        return formatted
    return "{:,.2f}".format(val).replace(",", " ")

def fmt_usd_price(val):
    if pd.isna(val) or val is None: return "-"
    return f"${format_num_str(float(val))}"

def fmt_eur_price(val):
    if pd.isna(val) or val is None: return "-"
    return f"€{format_num_str(float(val))}"

def fmt_fx_price(val):
    if pd.isna(val) or val is None: return "-"
    v = float(val)
    # A USD/EUR 1 alatti érték, a HUF párok pedig 20 felettiek
    if v < 5:
        return f"€{format_num_str(v)}"
    return f"{format_num_str(v)} Ft"

def format_pct(val):
    if pd.isna(val) or val is None: return "-"
    return f"{float(val):+.2f}%"

def color_delta(val):
    if pd.isna(val) or not isinstance(val, (int, float, np.number)):
        return "color: #888888;"
    color = '#27ae60' if val > 0 else '#e74c3c' if val < 0 else 'white'
    return f'color: {color}; font-weight: bold;'

def render_interactive_table(df, price_formatter, pct_cols):
    # Biztosítjuk, hogy minden szám-oszlop valódi float64 legyen a pontos sorbarendezéshez
    df["Price"] = pd.to_numeric(df["Price"], errors="coerce")
    for col in pct_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    format_dict = {"Price": price_formatter}
    for col in pct_cols:
        format_dict[col] = format_pct

    styled_df = (
        df.style
        .format(format_dict, na_rep="-")
        .map(color_delta, subset=pct_cols)
        .set_properties(**{'text-align': 'center'})
        .set_table_styles([
            dict(selector='th', props=[('text-align', 'center !important')]),
            dict(selector='td', props=[('text-align', 'center !important')])
        ])
    )

    col_cfg = {col: st.column_config.Column(alignment="center") for col in df.columns}
    table_height = int((len(df) + 1) * 36)

    st.dataframe(
        styled_df,
        width="stretch",
        hide_index=True,
        column_config=col_cfg,
        height=table_height
    )

# --- KATEGÓRIÁK ÉS TICKEREK ---
CATEGORIES = {
    "Részvények": {
        "Tesla": "TSLA", "Meta": "META", "Nvidia": "NVDA", "Google": "GOOGL", 
        "MicroStrategy": "MSTR", "Microsoft": "MSFT", "Amazon": "AMZN", "AMD": "AMD", 
        "Marathon": "MARA", "Sea Ltd": "SE", "Snowflake": "SNOW", "MercadoLibre": "MELI", 
        "T. Rowe Price": "TROW", "Adobe": "ADBE", "Planet 13": "PLNH", "Enphase": "ENPH",
        "Palantir Technologies": "PLTR", "Micron Technology": "MU", "Robinhood Markets": "HOOD",
        "Tempus AI, Inc.": "TEM", "Marvell Technology": "MRVL", "Astera Labs": "ALAB",
        "AST SpaceMobile": "ASTS", "Taiwan Semiconductor": "TSM", "ASML Holding": "ASML",
        "Vertiv Holdings Co.": "VRT", "Arm Holdings": "ARM", "Broadcom Inc.": "AVGO",
        "Hims & Hers Health": "HIMS", "Rocket Lab Corp": "RKLB", "Credo Technology": "CRDO",
        "ServiceNow Inc.": "NOW", "Super Micro Computer": "SMCI", "Rubrik Inc.": "RBRK",
        "IONQ Inc.": "IONQ", "Recursion Pharma": "RXRX", "Iris Energy": "IREN",
        "Oracle Corp.": "ORCL", "Salesforce Inc.": "CRM", "Qualcomm Inc.": "QCOM",
        "Duke Energy Corp.": "DUK", "Nu Holdings": "NU", "Symbotic Inc.": "SYM",
        "Cameco Corp.": "CCJ", "UiPath Inc.": "PATH", "DLocal Ltd.": "DLO",
        "C3.ai, Inc.": "AI", "Upstart Holdings": "UPST", "Lemonade, Inc.": "LMND",
        "Serve Robotics": "SERV", "Circle Internet Group Inc": "CRCL", "Pony AI Inc.": "PONY",
        "SpaceX (SPCX)": "SPCX", "Absci Corp.": "ABSI", "Eos Energy": "EOSE"
    },
    "ETF-ek": {
        "Vanguard All-World": "VWCE.DE", 
        "iShares Small Cap Value": "ZPRV.DE",
        "iShares MSCI Global Semiconductors": "SEC0.DE"
    },
    "Indexek": {
        "S&P 500": "^GSPC", "Nasdaq 100": "^IXIC", "Russell 2000": "^RUT"
    },
    "Devizák": {
        "Amerikai Dollár - USD/HUF": "USDHUF=X", "Euró - EUR/HUF": "EURHUF=X", 
        "Svájci Frank - CHF/HUF": "CHFHUF=X", "Angol Font - GBP/HUF": "GBPHUF=X", 
        "Dollár/Euró - USD/EUR": "USDEUR=X"
    }
}

METALS = {"Arany": "GC=F", "Ezüst": "SI=F", "Nyersolaj": "CL=F"}

# Kripto lista: (Megjelenített Név, Symbol, CMC Slug-ok listája, CoinGecko ID-k listája)
CRYPTO_LIST = [
    ("Bitcoin", "BTC", ["bitcoin"], ["bitcoin"]),
    ("Ethereum", "ETH", ["ethereum"], ["ethereum"]),
    ("Solana", "SOL", ["solana"], ["solana"]),
    ("Hyperliquid", "HYPE", ["hyperliquid"], ["hyperliquid"]),
    ("Chainlink", "LINK", ["chainlink"], ["chainlink"]),
    ("Sui", "SUI", ["sui"], ["sui"]),
    ("Bittensor", "TAO", ["bittensor"], ["bittensor"]),
    ("Pump.fun", "PUMP", ["pump-fun"], ["pump-fun"]),
    ("Jupiter", "JUP", ["jupiter-ag", "jupiter"], ["jupiter-exchange-solana"]),
    ("Jupiter LP", "JLP", ["jupiter-perpetuals-liquidity-provider", "jupiter-perpetuals-liquidity-provider-token"], ["jupiter-perpetuals-liquidity-provider-token"]),
    ("Pudgy Penguins", "PENGU", ["pudgy-penguins"], ["pudgy-penguins"]),
    ("Meteora", "MET", ["meteora"], ["meteora"]),
    ("Ondo", "ONDO", ["ondo-finance", "ondo"], ["ondo-finance", "ondo"]),
    ("Quant", "QNT", ["quant", "quant-network"], ["quant-network", "quant"]),
    ("Arweave", "AR", ["arweave"], ["arweave"]),
    ("Raydium", "RAY", ["raydium"], ["raydium"]),
    ("XRP", "XRP", ["xrp", "ripple"], ["ripple", "xrp"]),
    ("Stacks", "STX", ["stacks", "blockstack"], ["blockstack", "stacks"]),
    ("Akash Network", "AKT", ["akash-network"], ["akash-network"]),
    ("Bonk", "BONK", ["bonk1", "bonk"], ["bonk"]),
    ("Pendle", "PENDLE", ["pendle"], ["pendle"]),
    ("Rollbit Coin", "RLB", ["rollbit-coin"], ["rollbit-coin"]),
    ("DeepBook", "DEEP", ["deepbook-protocol", "deepbook", "deep"], ["deep", "deepbook"]),
    ("Uniswap", "UNI", ["uniswap"], ["uniswap"]),
    ("Walrus", "WAL", ["walrus-protocol", "walrus", "walrus-2"], ["walrus-2", "walrus"]),
    ("Ethena", "ENA", ["ethena"], ["ethena"]),
    ("Zcash", "ZEC", ["zcash"], ["zcash"]),
    ("Phala Network", "PHA", ["phala-network", "pha"], ["pha", "phala-network"]),
    ("Render", "RENDER", ["render", "render-token"], ["render-token", "render"]),
    ("Zerebro", "ZEREBRO", ["zerebro"], ["zerebro"]),
    ("Orca", "ORCA", ["orca"], ["orca"]),
    ("Algorand", "ALGO", ["algorand"], ["algorand"]),
    ("LOFI", "LOFI", ["lofi-the-yeti", "lofi", "lofi-2"], ["lofi-2", "lofi"]),
    ("ORE", "ORE", ["ore", "ore-solana"], ["ore"]),
    ("Blub", "BLUB", ["blub", "blub-sui"], ["blub"]),
    ("Aave", "AAVE", ["aave"], ["aave"])
]

# --- 1. YAHOO ADATLEKÉRDEZÉS (RÉSZVÉNYEK, ETF-EK, INDEXEK, DEVIZÁK, NEMESFÉMEK) ---
@st.cache_data(ttl=1200)
def fetch_all_yahoo_data():
    all_tickers = []
    for cat in CATEGORIES.values():
        all_tickers.extend(cat.values())
    all_tickers.extend(METALS.values())
    all_tickers.append("USDNOK=X")
    all_tickers = list(set(all_tickers))

    try:
        raw = yf.download(all_tickers, period="2y", progress=False)
        closes = raw['Close'] if 'Close' in raw else pd.DataFrame()
        if isinstance(closes, pd.Series):
            closes = closes.to_frame(name=all_tickers[0])
        if isinstance(closes.index, pd.DatetimeIndex) and closes.index.tz is not None:
            closes.index = closes.index.tz_localize(None)
    except:
        closes = pd.DataFrame()

    results = {}
    current_year = datetime.now().year

    for t in all_tickers:
        s = pd.Series(dtype=float)
        if t in closes.columns:
            s = closes[t].dropna()
        if len(s) < 2:
            try:
                hist = yf.Ticker(t).history(period="2y")
                if not hist.empty and 'Close' in hist.columns:
                    s = hist['Close'].dropna()
            except:
                pass
            
        if s.empty:
            continue

        if isinstance(s.index, pd.DatetimeIndex):
            if s.index.tz is not None:
                s.index = s.index.tz_localize(None)
            s.index = s.index.normalize()

        current = float(s.iloc[-1])
        res = {"Price": current}
        intervals = {"24h": -2, "7d": -6, "30d": -22, "60d": -44, "90d": -66}
        for name, idx in intervals.items():
            try:
                prev = float(s.iloc[idx])
                res[name] = ((current - prev) / prev) * 100
            except:
                res[name] = None
                
        y_start = s[s.index.year < current_year]
        if not y_start.empty:
            base_val = float(y_start.iloc[-1])
        else:
            base_val = float(s.iloc[0])
        res["YTD"] = ((current - base_val) / base_val) * 100 if base_val else None
            
        results[t] = res

    return results

# --- 2. KRIPTO ADATLEKÉRDEZÉS (4 LÉPCSŐS CMC + COINGECKO + CRYPTOCOMPARE MOTOR) ---
def fetch_single_crypto_full(args):
    item, cg_backup_map = args
    name, sym, cmc_slugs, cg_ids = item
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'application/json'
    }
    current_year = datetime.now().year
    jan1_ts = int(datetime(current_year, 1, 1).timestamp())
    now_ts = int(datetime.now().timestamp())

    price = chg_24h = chg_7d = chg_30d = chg_60d = chg_90d = ytd_val = None
    cmc_id = None

    # 1. LÉPCSŐ: CoinMarketCap Detail API (tartalmazza a közvetlen ytdPriceChangePercentage mezőt!)
    for slug in cmc_slugs:
        try:
            detail_url = f"https://api.coinmarketcap.com/data-api/v3/cryptocurrency/detail?slug={slug}"
            r = requests.get(detail_url, headers=headers, timeout=7)
            if r.status_code == 200:
                data = r.json().get('data', {})
                stats = data.get('statistics', {})
                if stats and stats.get('price') is not None:
                    cmc_id = data.get('id')
                    price = float(stats.get('price'))
                    chg_24h = stats.get('priceChangePercentage24h')
                    chg_7d = stats.get('priceChangePercentage7d')
                    chg_30d = stats.get('priceChangePercentage30d')
                    chg_60d = stats.get('priceChangePercentage60d')
                    chg_90d = stats.get('priceChangePercentage90d')
                    # A CMC-ben a pontos kulcsnév: ytdPriceChangePercentage
                    ytd_val = stats.get('ytdPriceChangePercentage')
                    if ytd_val is None:
                        ytd_val = stats.get('priceChangePercentageYtd')
                    break
        except:
            pass

    # 2. LÉPCSŐ: Ha a CMC-n más volt a slug, kiegészítés az egyetlen csomagos CoinGecko mentőövből
    for cid in cg_ids:
        if cid in cg_backup_map:
            cg_item = cg_backup_map[cid]
            if price is None and cg_item.get('current_price') is not None:
                price = float(cg_item['current_price'])
            if chg_24h is None:
                chg_24h = cg_item.get('price_change_percentage_24h_in_currency')
            if chg_7d is None:
                chg_7d = cg_item.get('price_change_percentage_7d_in_currency')
            if chg_30d is None:
                chg_30d = cg_item.get('price_change_percentage_30d_in_currency')
            break

    # 3. LÉPCSŐ: Ha a YTD még mindig hiányozna, lekérjük a CMC-től a numerikus ID alapján a Jan 1 árfolyamot
    if price and ytd_val is None and cmc_id is not None:
        try:
            chart_url = f"https://api.coinmarketcap.com/data-api/v3/cryptocurrency/detail/chart?id={cmc_id}&range={jan1_ts}~{now_ts}"
            r_c = requests.get(chart_url, headers=headers, timeout=7)
            if r_c.status_code == 200:
                points = r_c.json().get('data', {}).get('points', {})
                if points:
                    first_ts = sorted(points.keys(), key=lambda x: int(x))[0]
                    base_price = points[first_ts].get('v', [None])[0]
                    if base_price and float(base_price) > 0:
                        ytd_val = ((price - float(base_price)) / float(base_price)) * 100
        except:
            pass

    # 4. LÉPCSŐ: CryptoCompare napi historikus gyertyák (ha bármelyik adat vagy YTD még hiányozna)
    if price is None or ytd_val is None or chg_7d is None or chg_30d is None:
        try:
            days_needed = (datetime.now() - datetime(current_year, 1, 1)).days + 5
            limit_days = max(days_needed, 100)
            cc_url = f"https://min-api.cryptocompare.com/data/v2/histoday?fsym={sym}&tsym=USD&limit={limit_days}"
            r_cc = requests.get(cc_url, headers=headers, timeout=7)
            if r_cc.status_code == 200:
                candles = [c for c in r_cc.json().get('Data', {}).get('Data', []) if c.get('close', 0) > 0]
                if len(candles) >= 2:
                    if price is None:
                        price = float(candles[-1]['close'])
                    if chg_24h is None and len(candles) >= 2:
                        p = float(candles[-2]['close'])
                        chg_24h = ((price - p) / p) * 100
                    if chg_7d is None and len(candles) >= 8:
                        p = float(candles[-8]['close'])
                        chg_7d = ((price - p) / p) * 100
                    if chg_30d is None and len(candles) >= 31:
                        p = float(candles[-31]['close'])
                        chg_30d = ((price - p) / p) * 100
                    if chg_60d is None and len(candles) >= 61:
                        p = float(candles[-61]['close'])
                        chg_60d = ((price - p) / p) * 100
                    if chg_90d is None and len(candles) >= 91:
                        p = float(candles[-91]['close'])
                        chg_90d = ((price - p) / p) * 100
                    if ytd_val is None:
                        jan_candles = [c for c in candles if c.get('time', 0) >= jan1_ts - 86400]
                        base_c = jan_candles[0] if jan_candles else candles[0]
                        base_p = float(base_c['close'])
                        if base_p > 0:
                            ytd_val = ((price - base_p) / base_p) * 100
        except:
            pass

    return {
        "Név": f"{name} - {sym}",
        "Price": price,
        "24h": chg_24h,
        "7d": chg_7d,
        "30d": chg_30d,
        "60d": chg_60d,
        "90d": chg_90d,
        "YTD": ytd_val
    }

@st.cache_data(ttl=1200)
def get_all_crypto_master():
    # Egyetlen gyors csomagolt (batch) lekérés a CoinGeckóra biztonsági tartaléknak
    all_cg_ids = []
    for _, _, _, cg_ids in CRYPTO_LIST:
        all_cg_ids.extend(cg_ids)
    ids_str = ",".join(list(set(all_cg_ids)))
    
    cg_backup_map = {}
    try:
        cg_url = f"https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&ids={ids_str}&price_change_percentage=24h,7d,30d&per_page=100"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        resp = requests.get(cg_url, headers=headers, timeout=10)
        if resp.status_code == 200:
            for item in resp.json():
                cg_backup_map[item['id']] = item
    except:
        pass

    # Párhuzamosított CMC + YTD lekérdezés mind a 36 tokenre
    tasks = [(item, cg_backup_map) for item in CRYPTO_LIST]
    with ThreadPoolExecutor(max_workers=12) as executor:
        results = list(executor.map(fetch_single_crypto_full, tasks))

    valid_rows = [r for r in results if r["Price"] is not None]
    return valid_rows

# --- MEGJELENÍTÉS ---
st.title("FONTOSABB ÁRFOLYAMOK")

with st.spinner("Árfolyamok és YTD adatok szinkronizálása..."):
    yahoo_data_map = fetch_all_yahoo_data()
    crypto_rows = get_all_crypto_master()

PCT_COLS = ["24h", "7d", "30d", "60d", "90d", "YTD"]

# 1. Crypto
st.header("Crypto")
if not crypto_rows:
    st.warning("A kripto adatok jelenleg nem érhetőek el. Kérlek, frissíts rá egy perc múlva!")
else:
    df_c = pd.DataFrame(crypto_rows)
    df_c = df_c[["Név", "Price", "24h", "7d", "30d", "60d", "90d", "YTD"]]
    render_interactive_table(df_c, fmt_usd_price, PCT_COLS)

# 2. Yahoo Kategóriák
for cat_name, items in CATEGORIES.items():
    st.header(cat_name)
    rows = []
    for name, ticker in items.items():
        data = yahoo_data_map.get(ticker)
        if data:
            display_label = f"{name}" if "HUF" in ticker or "EUR" in ticker else f"{name} - {ticker}"
            row_dict = {"Név": display_label}
            row_dict.update(data)
            rows.append(row_dict)
    
    if cat_name == "Devizák":
        u_h, u_n = yahoo_data_map.get("USDHUF=X"), yahoo_data_map.get("USDNOK=X")
        if u_h and u_n:
            rows.append({
                "Név": "Norvég Korona (számított) - NOK/HUF",
                "Price": u_h['Price'] / u_n['Price'],
                "24h": None, "7d": None, "30d": None, "60d": None, "90d": None, "YTD": None
            })

    if rows:
        df_cat = pd.DataFrame(rows)
        df_cat = df_cat[["Név", "Price", "24h", "7d", "30d", "60d", "90d", "YTD"]]
        if "ETF-ek" in cat_name:
            p_fmt = fmt_eur_price
        elif "Devizák" in cat_name:
            p_fmt = fmt_fx_price
        else:
            p_fmt = fmt_usd_price
        render_interactive_table(df_cat, p_fmt, PCT_COLS)

# 3. Nemesfémek és olaj
st.header("Nemesfémek és olaj")
metal_rows = []
for n, t in METALS.items():
    data = yahoo_data_map.get(t)
    if data:
        row_dict = {"Név": f"{n} - {t}"}
        row_dict.update(data)
        metal_rows.append(row_dict)

if metal_rows:
    df_m = pd.DataFrame(metal_rows)
    df_m = df_m[["Név", "Price", "24h", "7d", "30d", "60d", "90d", "YTD"]]
    render_interactive_table(df_m, fmt_usd_price, PCT_COLS)
