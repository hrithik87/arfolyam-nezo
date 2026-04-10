import streamlit as st
import time

# --- OLDALBEÁLLÍTÁSOK ---
st.set_page_config(
    page_title="A Lehullott Múzsa | Bara V.A. Privát Rituálé",
    page_icon="🥀",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- BARA V.A. EXTRA VISUALS (ANIMÁLT HÁTTÉR ÉS CSS) ---
st.markdown("""
    <style>
    /* Sötét Bordeaux / Fekete Vignette Háttér */
    .stApp {
        background: radial-gradient(circle at center, #2e0505 0%, #0a0101 100%);
        color: #F5F5F5;
        font-family: 'Georgia', serif;
        overflow: hidden;
    }

    /* ANIMÁLT HULLÓ SZIRMOK */
    .petal-container {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        pointer-events: none;
        z-index: 0;
    }
    .petal {
        position: absolute;
        background-color: #7b0000;
        opacity: 0.6;
        border-radius: 50% 0 50% 50%;
        animation: fall 10s linear infinite;
    }
    @keyframes fall {
        0% { transform: translateY(-10%) rotate(0deg); }
        100% { transform: translateY(110%) rotate(360deg); }
    }
    
    /* Gombok / Kártyák stílusa */
    div.stButton > button {
        background-color: #1A1A1A; color: #F5F5F5; border: 1px solid #4A0404;
        border-radius: 12px; width: 100%; height: 100px; font-weight: bold;
        transition: 0.3s; font-size: 18px; margin-bottom: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    div.stButton > button:hover {
        background-color: #4A0404; border-color: #8B0000; color: white;
        transform: scale(1.05); box-shadow: 0 8px 12px rgba(139,0,0,0.5);
    }

    /* Szövegek stílusa */
    h1, h2 { color: #8B0000 !important; text-align: center; }
    h3 { color: #B22222 !important; font-style: italic; text-align: center; margin-bottom: 1.5em; }
    .status-text { text-align: center; color: #888; font-style: italic; margin-bottom: 20px; font-size: 14px; }
    .intro-text { text-align: center; font-size: 18px; line-height: 1.6; max-width: 600px; margin: 0 auto 2em auto; color: #dcdcdc; }

    /* Folyamatjelző */
    .stProgress > div > div > div > div { background-color: #8B0000; }
    </style>
    
    <div class="petal-container">
        <div class="petal" style="width: 10px; height: 10px; left: 10%; animation-delay: 1s;"></div>
        <div class="petal" style="width: 15px; height: 15px; left: 30%; animation-delay: 3s;"></div>
        <div class="petal" style="width: 8px; height: 8px; left: 50%; animation-delay: 5s;"></div>
        <div class="petal" style="width: 12px; height: 12px; left: 70%; animation-delay: 2s;"></div>
        <div class="petal" style="width: 14px; height: 14px; left: 90%; animation-delay: 4s;"></div>
        <div class="petal" style="width: 11px; height: 11px; left: 20%; animation-delay: 6s;"></div>
        <div class="petal" style="width: 13px; height: 13px; left: 60%; animation-delay: 8s;"></div>
    </div>
""", unsafe_allow_html=True)

# --- 1. JELSZÓVÉDELEM ÉS BELÉPŐ KÉPERNYŐ ---
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False
    if st.session_state["password_correct"]:
        return True
    
    # Belépő Bevezető Szöveg (Bara V.A. Vibe)
    st.markdown("<h1>🥀 A Lehullott Múzsa</h1>", unsafe_allow_html=True)
    st.markdown("<h3>Ismerd meg az elméd sötét oldalát.</h3>", unsafe_allow_html=True)
    st.markdown("""
        <div class="intro-text">
            Üdvözöllek a szentélyben. A külvilág zaja itt elnémul.<br>
            A szavak talán elhagytak, de a látomásod még él.<br>
            Ez a rituálé arra való, hogy felébredjen benned a Lehullott Múzsa.<br>
            Kövesd a lépéseket, hozz döntéseket, és adj hangot a benned lakozó káosznak.
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<p class='status-text'>A folytatáshoz bizonyítsd inkognitódat!</p>", unsafe_allow_html=True)
    jelszo = st.text_input("Mester-Kriptográfus Jelszó:", type="password", key="pwd_input")
    if jelszo:
        if jelszo == st.secrets["app_password"]:
            st.session_state["password_correct"] = True
            st.rerun()
        else:
            st.error("Hibás jelszó. Az inkognitó megmarad.")
    return False

if check_password():
    # Session State inicializálása
    if 'step' not in st.session_state:
        st.session_state.step = 1
    if 'answers' not in st.session_state:
        st.session_state.answers = {}

    # --- AUDIO MODUL (Háttérzaj a rituáléhoz) ---
    st.sidebar.markdown("### 🎧 Atmoszféra")
    st.sidebar.audio("https://www.soundhelix.com/examples/mp3/SoundHelix-Song-10.mp3")
    st.sidebar.info("Indítsd el a hangot a teljes rituális élményhez!")

    # FOLYAMATJELZŐ
    progress_val = st.session_state.step / 16
    st.progress(progress_val)
    st.markdown(f"<p class='status-text'>A rituálé állása: {st.session_state.step} / 16</p>", unsafe_allow_html=True)

    # --- A 16 LÉPCSŐS RITUÁLÉ (4 opcióval) ---
    
    # A 16 lépcső konkrét adatai (4 opcióval)
    # Az emojis karaktereket standard Unicode formára írtuk át
    steps = {
        1: ("Vizuális Alap (A kép lelke)", ["🌑 Mélyfekete Nihil", "🍷 Borvörös Melankólia", "🌫️ Hamuszürke Köd", "🕯️ Aranybarna Gyertyafény"]),
        2: ("Uralkodó Textúra", ["📜 Ódon, szakadt papír", "🪞 Tükörcserép", "🥀 Száradt szirom", "⛓️ Hideg láncok"]),
        3: ("Belső Hang (Zenei vibe)", ["🎹 Magányos zongora", "🎻 Sikoltó hegedű", "⛈️ Tá Távoli dörgés", "🤫 Nyomasztó csend"]),
        4: ("Írói Gyónás (A mai bűnöd)", ["🪦 Ma mindenkit megölök", "🎭 Elvesztem a maszk mögött", "🧩 Csak kódokat látok", "☕ Túl sok kávé, nulla szó"]),
        5: ("Karakter-sors", ["🔥 Lassú égés", "🔪 Hirtelen árulás", "🧠 Mentális összeomlás", "🖤 Megváltó halál"]),
        6: ("A Szimbólum", ["🗝️ Véres kulcs", "🐦 Döglött holló", "🖼️ Üres képkeret", "💍 Elvesztett gyűrű"]),
        7: ("Célpont (Kihez szólunk?)", ["🤝 A hűséges olvasók", "👀 A néma figyelők", "👺 A belső démonok", "🌍 A közönyös világ"]),
        8: ("Aktuális érzelem", ["🧊 Megfagyott nihil", "🌋 Fojtott düh", "🌊 Sötét sötét vágyakozás", "🍂 Fáradt beletörődés"]),
        9: ("Az Akadály", ["🚧 Plot hole (Szakadék)", "💤 Motivációhiány", "📱 A külvilág zaja", "🖋️ Öngyűlölet"]),
        10: ("Domináns Szín", ["🔴
