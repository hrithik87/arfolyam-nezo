import streamlit as st
import yfinance as yf
import requests
import pandas as pd
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

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
    if not isinstance(val, (int, float)) or pd.isna(val): return ""
    color = '#27ae60' if val > 0 else '#e74c3c' if val < 0 else 'white'
    return f'color: {color}; font-weight: bold;'

def format_pct(val):
    if pd.isna(val) or val is None: return "-"
    return f"{val:+.2f}%"

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

# Kripto lista: (Megjelenített Név, Symbol, CoinMarketCap Slug, Tartalék CoinGecko ID)
CRYPTO_LIST = [
    ("Bitcoin", "BTC", "bitcoin", "bitcoin"),
    ("Ethereum", "ETH", "ethereum", "ethereum"),
    ("Solana", "SOL", "solana", "solana"),
    ("Hyperliquid", "HYPE", "hyperliquid", "hyperliquid"),
    ("Chainlink", "LINK", "chainlink", "chainlink"),
    ("Sui", "SUI", "sui", "sui"),
    ("Bittensor", "TAO", "bittensor", "bittensor"),
    ("Pump.fun", "PUMP", "pump-fun", "pump-fun"),
    ("Jupiter", "JUP", "jupiter-ag", "jupiter-exchange-solana"),
    ("Jupiter LP", "JLP", "jupiter-perpetuals-liquidity-provider-token", "jupiter-perpetuals-liquidity-provider-token"),
    ("Pudgy Penguins", "PENGU", "pudgy-penguins", "pudgy-penguins"),
    ("Meteora", "MET", "meteora", "meteora"),
    ("Ondo", "ONDO", "ondo-finance", "ondo-finance"),
    ("Quant", "QNT", "quant", "quant-network"),
    ("Arweave", "AR", "arweave", "arweave"),
    ("Raydium", "RAY", "raydium", "raydium"),
    ("XRP", "XRP", "xrp", "ripple"),
    ("Stacks", "STX", "stacks", "blockstack"),
    ("Akash Network", "AKT", "akash-network", "akash-network"),
    ("Bonk", "BONK", "bonk1", "bonk"),
    ("Pendle", "PENDLE", "pendle", "pendle"),
    ("Rollbit Coin", "RLB", "rollbit-coin", "rollbit-coin"),
    ("DeepBook", "DEEP", "deepbook-protocol", "deep"),
    ("Uniswap", "UNI", "uniswap", "uniswap"),
    ("Walrus", "WAL", "walrus-protocol", "walrus-2"),
    ("Ethena", "ENA", "ethena", "ethena"),
    ("Zcash", "ZEC", "zcash", "zcash"),
    ("Phala Network", "PHA", "phala-network", "pha"),
    ("Render", "RENDER", "render", "render-token"),
    ("Zerebro", "ZEREBRO", "zerebro", "zerebro"),
    ("Orca", "ORCA", "orca", "orca"),
    ("Algorand", "ALGO", "algorand", "algorand"),
    ("LOFI", "LOFI", "lofi-the-yeti", "lofi-2"),
    ("ORE", "ORE", "ore", "ore"),
    ("Blub", "BLUB", "blub", "blub"),
    ("Aave", "AAVE", "aave", "aave")
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
        if closes.index.tz is not None:
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
                    if s.index.tz is not None:
                        s.index = s.index.tz_localize(None)
            except: pass
            
        if s.empty:
            continue

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
            res["YTD"] = ((current - base_val) / base_val) * 100 if base_val else None
        else:
            res["YTD"] = None
            
        results[t] = res

    return results

# --- 2. COINMARKETCAP (CMC) KÖZPONTI KRIPTO LEKÉRDEZŐ MOTOR ---
def fetch_single_cmc_crypto(item):
    name, sym, cmc_slug, cg_id = item
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'application/json'
    }
    current_year = datetime.now().year
    jan1_ts = int(datetime(current_year, 1, 1).timestamp())
    now_ts = int(datetime.now().timestamp())

    price = chg_24h = chg_7d = chg_30d = ytd_val = None

    # 1. Élő ár és 24h, 7d, 30d változás közvetlenül a CoinMarketCap-ről
    try:
        detail_url = f"https://api.coinmarketcap.com/data-api/v3/cryptocurrency/detail?slug={cmc_slug}"
        r = requests.get(detail_url, headers=headers, timeout=8)
        if r.status_code == 200:
            stats = r.json().get('data', {}).get('statistics', {})
            if stats:
                price = stats.get('price')
                chg_24h = stats.get('priceChangePercentage24h')
                chg_7d = stats.get('priceChangePercentage7d')
                chg_30d = stats.get('priceChangePercentage30d')
                # Ha a CMC közvetlenül küldi a YTD-t, azonnal használjuk
                if stats.get('priceChangePercentageYtd') is not None:
                    ytd_val = stats.get('priceChangePercentageYtd')
    except:
        pass

    # 2. Ha a CMC-n más lenne a kis token slug-ja, másodlagos keresés szimbólum alapján
    if price is None:
        try:
            # Tartalék: CryptoCompare / DexScreener gyors lekérés, ha egy slug változott volna
            ds_url = f"https://api.dexscreener.com/latest/dex/search?q={sym}"
            r_ds = requests.get(ds_url, headers=headers, timeout=6)
            if r_ds.status_code == 200:
                pairs = r_ds.json().get('pairs', [])
                for p in pairs:
                    if p.get('baseToken', {}).get('symbol', '').upper() == sym.upper():
                        price = float(p.get('priceUsd', 0))
                        chg_24h = p.get('priceChange', {}).get('h24')
                        break
        except:
            pass

    # 3. YTD (Év eleje óta) pontos kiszámítása a CMC historikus grafikonjából
    if price and ytd_val is None:
        try:
            chart_url = f"https://api.coinmarketcap.com/data-api/v3/cryptocurrency/detail/chart?slug={cmc_slug}&range={jan1_ts}~{now_ts}"
            r_c = requests.get(chart_url, headers=headers, timeout=8)
            if r_c.status_code == 200:
                points = r_c.json().get('data', {}).get('points', {})
                if points:
                    first_ts = sorted(points.keys())[0]
                    base_price = points[first_ts].get('v', [None])[0]
                    if base_price and base_price > 0:
                        ytd_val = ((price - float(base_price)) / float(base_price)) * 100
        except:
            pass

    return f"{name} - {sym}", {
        "Price": price,
        "24h": chg_24h,
        "7d": chg_7d,
        "30d": chg_30d,
        "YTD": ytd_val
    }

@st.cache_data(ttl=1200)
def get_all_crypto_cmc():
    output = {}
    # 12 párhuzamos szálon egyszerre kérdezzük le a CoinMarketCap-et (1-2 másodperc az egész)
    with ThreadPoolExecutor(max_workers=12) as executor:
        results = list(executor.map(fetch_single_cmc_crypto, CRYPTO_LIST))
        
    for label, data in results:
        if data["Price"] is not None:
            output[label] = data
            
    return output

# --- MEGJELENÍTÉS ---
st.title("FONTOSABB ÁRFOLYAMOK")

with st.spinner("Árfolyamok szinkronizálása (CoinMarketCap & Yahoo)..."):
    yahoo_data_map = fetch_all_yahoo_data()
    c_raw = get_all_crypto_cmc()

# 1. Crypto
st.header("Crypto")

if not c_raw:
    st.warning("A kripto adatok jelenleg nem érhetőek el. Kérlek, frissíts rá egy perc múlva!")
else:
    df_c = pd.DataFrame(c_raw).T
    df_c = df_c[["Price", "24h", "7d", "30d", "YTD"]]
    display_df = df_c.copy().astype(object)
    for row in display_df.index:
        display_df.at[row, "Price"] = format_final(df_c.loc[row, "Price"], "Crypto", row)
    st.table(display_df.style.map(color_delta, subset=["24h", "7d", "30d", "YTD"]).format(format_pct, subset=["24h", "7d", "30d", "YTD"]))

# 2. Yahoo Kategóriák
for cat_name, items in CATEGORIES.items():
    st.header(cat_name)
    results = {}
    for name, ticker in items.items():
        data = yahoo_data_map.get(ticker)
        if data: 
            display_label = f"{name}" if "HUF" in ticker or "EUR" in ticker else f"{name} - {ticker}"
            results[display_label] = data
    
    if cat_name == "Devizák":
        u_h, u_n = yahoo_data_map.get("USDHUF=X"), yahoo_data_map.get("USDNOK=X")
        if u_h and u_n:
            results["Norvég Korona (számított) - NOK/HUF"] = {"Price": u_h['Price'] / u_n['Price'], "24h": None, "7d": None, "30d": None, "60d": None, "90d": None, "YTD": None}

    if results:
        df = pd.DataFrame(results).T
        df = df[["Price", "24h", "7d", "30d", "60d", "90d", "YTD"]]
        display_df = df.copy().astype(object)
        for row in display_df.index:
            display_df.at[row, "Price"] = format_final(df.loc[row, "Price"], cat_name, row)
        st.table(display_df.style.map(color_delta, subset=["24h", "7d", "30d", "60d", "90d", "YTD"]).format(format_pct, subset=["24h", "7d", "30d", "60d", "90d", "YTD"]))

# 3. Nemesfémek és olaj
st.header("Nemesfémek és olaj")
m_res = {f"{n} - {t}": yahoo_data_map.get(t) for n, t in METALS.items() if yahoo_data_map.get(t)}
if m_res:
    df_m = pd.DataFrame(m_res).T
    df_m = df_m[["Price", "24h", "7d", "30d", "60d", "90d", "YTD"]]
    display_m = df_m.copy().astype(object)
    for row in display_m.index:
        display_m.at[row, "Price"] = format_final(df_m.loc[row, "Price"], "Nemesfémek", row)
    st.table(display_m.style.map(color_delta, subset=["24h", "7d", "30d", "60d", "90d", "YTD"]).format(format_pct, subset=["24h", "7d", "30d", "60d", "90d", "YTD"]))
