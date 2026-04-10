import streamlit as st
import time

# 1. Oldalbeállítások (Bara V.A. Dark Mode)
st.set_page_config(page_title="A Lehullott Múzsa", page_icon="🥀", layout="centered")

# CSS Injektálás a vizuális élményért
st.markdown("""
    <style>
    .stApp { background-color: #0E0E0E; color: #F5F5F5; font-family: 'Georgia', serif; }
    div.stButton > button { background-color: #4A0404; color: #F5F5F5; border: 1px solid #800000; border-radius: 5px; width: 100%; height: 3em; font-weight: bold; }
    div.stButton > button:hover { background-color: #800000; border-color: #F5F5F5; }
    h1, h2, h3 { color: #8B0000 !important; text-align: center; }
    .stProgress > div > div > div > div { background-color: #8B0000; }
    .choice-card { border: 1px solid #4A0404; padding: 20px; border-radius: 10px; background: #1A1A1A; text-align: center; transition: 0.3s; cursor: pointer; }
    .choice-card:hover { border-color: #800000; background: #2A1A1A; }
    </style>
""", unsafe_allow_html=True)

# 2. Hermetikus Jelszóvédelem
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False
    if st.session_state["password_correct"]:
        return True
    
    st.markdown("<h1>🥀 A Lehullott Múzsa</h1>", unsafe_allow_html=True)
    jelszo = st.text_input("Jelszó:", type="password")
    if jelszo:
        if jelszo == st.secrets["app_password"]:
            st.session_state["password_correct"] = True
            st.rerun()
        else:
            st.error("Hibás jelszó.")
    return False

if check_password():
    # Session State inicializálása a 16 lépéshez
    if 'step' not in st.session_state:
        st.session_state.step = 1
    if 'answers' not in st.session_state:
        st.session_state.answers = {}

    # --- AUDIO FŰSZER ---
    # Egy sejtelmes, sötét ambient zongora + eső (YouTube-ról behúzva, diszkréten)
    st.sidebar.markdown("### 🎧 Atmoszféra")
    st.sidebar.audio("https://www.soundhelix.com/examples/mp3/SoundHelix-Song-10.mp3") # Placeholder, de sötét hangulatú
    st.sidebar.info("Indítsd el a zenét a rituáléhoz!")

    # FOLYAMATJELZŐ
    progress = st.session_state.step / 16
    st.progress(progress)
    st.write(f"Kategória: {st.session_state.step} / 16")

    # --- A 16 LÉPCSŐS RITUÁLÉ ---
    
    # Itt egy nagy elágazásrendszer jön a lépésekhez
    if st.session_state.step == 1:
        st.subheader("1. Vizuális Alap (Válassz egy képet!)")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🌑 Mélyfekete Nihil"): st.session_state.answers['vibe'] = "Nihil"; st.session_state.step += 1; st.rerun()
        with c2:
            if st.button("🍷 Borvörös Melankólia"): st.session_state.answers['vibe'] = "Melankólia"; st.session_state.step += 1; st.rerun()

    elif st.session_state.step == 2:
        st.subheader("2. Uralkodó Textúra")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("📜 Ódon Papír"): st.session_state.answers['textura'] = "Papír"; st.session_state.step += 1; st.rerun()
        with c2:
            if st.button("🪞 Tükörcserép"): st.session_state.answers['textura'] = "Tükör"; st.session_state.step += 1; st.rerun()

    elif st.session_state.step == 3:
        st.subheader("3. Mi szól a fejedben?")
        ans = st.selectbox("Zenei vibe:", ["Sötét zongora", "Viharzúgás", "Suttogások", "Kínos csend"])
        if st.button("Következő"): st.session_state.answers['zene'] = ans; st.session_state.step += 1; st.rerun()

    # (A többi 4-15 lépést a kódolás során folyamatosan bővítjük, most az alap vázat adom meg, hogy lásd a működést)
    
    elif st.session_state.step < 16:
        st.subheader(f"{st.session_state.step}. Írói Kérdés")
        st.write("Itt jönnek a folyamatos, mélyebb kérdések...")
        if st.button("Lépj tovább"): st.session_state.step += 1; st.rerun()

    elif st.session_state.step == 16:
        st.subheader("16. A Külvilág Zaja (Trend)")
        trend = st.text_input("Mi a legfrissebb bulvár vagy TikTok trend?")
        if st.button("🔥 GENERÁLÁS"): 
            st.session_state.answers['trend'] = trend
            st.session_state.step += 1
            st.rerun()

    # VÉGEREDMÉNY
    if st.session_state.step > 16:
        st.balloons()
        st.success("A rituálé véget ért. Íme a posztod.")
        st.write(st.session_state.answers) # Teszteléshez kiírjuk az összegyűjtött adatokat
        if st.button("Újrakezdés"):
            st.session_state.step = 1
            st.session_state.answers = {}
            st.rerun()

    # Visszalépés lehetősége
    if st.session_state.step > 1 and st.session_state.step <= 16:
        if st.button("← Vissza az előző döntéshez"):
            st.session_state.step -= 1
            st.rerun()
