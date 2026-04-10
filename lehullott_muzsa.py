import streamlit as st
import time
import random

# 1. Oldalbeállítások (Bara V.A. Dark Mode)
st.set_page_config(page_title="A Lehullott Múzsa", page_icon="🥀", layout="centered")

# 2. Hermetikus Jelszóvédelem
def check_password():
    if "password_correct" not in st.session_state:
         st.session_state["password_correct"] = False

    if st.session_state["password_correct"]:
        return True

    st.markdown("<h1 style='text-align: center; color: #800000;'>A Lehullott Múzsa 🥀</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Csak a Mester-Kriptográfus léphet be.</p>", unsafe_allow_html=True)
    
    jelszo = st.text_input("Jelszó:", type="password")
    
    if jelszo:
        # A Streamlit Secrets-ből fogja kiolvasni a jelszót
        if jelszo == st.secrets["app_password"]:
            st.session_state["password_correct"] = True
            st.rerun()
        else:
            st.error("Hibás jelszó. Az inkognitó megmarad.")
    return False

# 3. Fő alkalmazás logika (Csak ha jó a jelszó)
if check_password():
    
    # CSS Injektálás a sötét esztétikáért
    st.markdown("""
        <style>
        .stApp {
            background-color: #0E0E0E;
            color: #F5F5F5;
            font-family: 'Georgia', serif;
        }
        div.stButton > button:first-child {
            background-color: #4A0404;
            color: #F5F5F5;
            border: 1px solid #800000;
            border-radius: 5px;
            width: 100%;
        }
        div.stButton > button:first-child:hover {
            background-color: #800000;
            border-color: #F5F5F5;
        }
        h1, h2, h3 {
            color: #8B0000 !important;
        }
        </style>
    """, unsafe_allow_html=True)

    st.title("🥀 A Lehullott Múzsa")
    st.subheader("Bara V.A. Privát Generátora")
    st.divider()

    # Állapotmentés a gombokhoz
    if 'generalt_poszt' not in st.session_state:
        st.session_state.generalt_poszt = ""
        st.session_state.generalt_prompt = ""

    # FÁZISOK
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 1. Vizuális Hangulat")
        mood = st.radio(
            "Válaszd ki a mai alap tónust:",
            ("☕ Sötét kávé és füst", "🌧️ Esős ablak és árnyékok", "🕯️ Égő gyertya a sötétben", "🥀 Vérvörös szirom fekete háttéren")
        )

    with col2:
        st.markdown("### 2. Írói Gyóntatószék")
        gyon = st.radio(
            "Mi a mai írói nyomorod?",
            ("Isten-komplexusom van, ma mindenkit megölök.", 
             "A főhősöm okosabb nálam, és ez borzasztóan idegesít.", 
             "Kutatómunkát végzek (amitől a rendőrség is megfigyelne).", 
             "A maszk mögött ma csak üres tekintet és kávé van.")
        )

    st.divider()
    st.markdown("### 3. Külvilág-Misszió (Trend-vadászat)")
    trend = st.text_input("Írj be ide egy ma látott trendet, bulvár hírt, vagy TikTok hook-ot:", placeholder="Pl.: Szakított az álompár / Viharos szél fúj...")

    st.divider()
    
    # GENERÁLÁS GOMB
    if st.button("🔥 Sötét Varázslat (Poszt Generálása)"):
        if trend == "":
            st.warning("Kérlek, írj be egy trendet vagy hírt a külvilágból!")
        else:
            with st.spinner("A múzsa a sötétben dolgozik..."):
                time.sleep(2) # Drámai hatás szünete
                
                # Itt történik a "Híd" építése (Egyszerűsített template logika)
                poszt = f"Kint a világ épp azon pörög, hogy: '{trend}'. Én meg a négy fal között ücsörgök, és az egyetlen gondolatom: {gyon.lower()} \n\nNéha a valóság és az írói lét közötti kontraszt annyira abszurd, hogy csak nevetni tudok. Vagy kávét inni. \n\nNálatok mi a mai legnagyobb dráma? 🥀👇\n\n#barava #íróiélet #mutimitírsz #sötéttitkok"
                
                prompt = f"Dark academia aesthetic, {mood.split(' ', 1)[1]}, cinematic lighting, highly detailed, photorealistic. In the background a subtle hint of '{trend}' translated to an atmospheric element, deep burgundy and black tones."
                
                st.session_state.generalt_poszt = poszt
                st.session_state.generalt_prompt = prompt

    # EREDMÉNY KIÍRÁSA
    if st.session_state.generalt_poszt != "":
        st.success("Kész. A szavak a tiédek.")
        st.markdown("#### 📝 Kész Poszt Szövege:")
        st.code(st.session_state.generalt_poszt, language="text")
        
        st.markdown("#### 🎨 Nano Banana 2 Kép Prompt:")
        st.code(st.session_state.generalt_prompt, language="text")
