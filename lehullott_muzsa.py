import streamlit as st
import time

# 1. Oldalbeállítások (Bara V.A. Dark Mode)
st.set_page_config(page_title="A Lehullott Múzsa", page_icon="🥀", layout="centered")

# --- EGYEDI BARA V.A. STÍLUS (CSS) ---
st.markdown("""
    <style>
    .stApp { background-color: #0E0E0E; color: #F5F5F5; font-family: 'Georgia', serif; }
    /* Gombok stílusa */
    div.stButton > button {
        background-color: #1A1A1A; color: #F5F5F5; border: 1px solid #4A0404;
        border-radius: 8px; width: 100%; height: 80px; font-weight: bold;
        transition: 0.3s; font-size: 16px;
    }
    div.stButton > button:hover {
        background-color: #4A0404; border-color: #8B0000; color: white;
        transform: scale(1.02);
    }
    /* Folyamatjelző */
    .stProgress > div > div > div > div { background-color: #8B0000; }
    h1, h2, h3 { color: #8B0000 !important; text-align: center; }
    .stSelectbox label, .stTextInput label { color: #8B0000 !important; font-weight: bold; }
    .status-text { text-align: center; color: #666; font-style: italic; margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

# 2. Hermetikus Jelszóvédelem
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False
    if st.session_state["password_correct"]:
        return True
    
    st.markdown("<h1>🥀 A Lehullott Múzsa</h1>", unsafe_allow_html=True)
    st.markdown("<p class='status-text'>Belépés csak íróknak és démonoknak.</p>", unsafe_allow_html=True)
    jelszo = st.text_input("Jelszó:", type="password")
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

    # --- AUDIO MODUL ---
    st.sidebar.markdown("### 🎧 Atmoszféra")
    # Sejtelmes háttérzaj (eső + zongora jellegű audio link)
    st.sidebar.audio("https://www.soundhelix.com/examples/mp3/SoundHelix-Song-10.mp3")
    st.sidebar.info("Indítsd el a hangot a rituáléhoz!")

    # FOLYAMATJELZŐ
    progress_val = st.session_state.step / 16
    st.progress(progress_val)
    st.markdown(f"<p class='status-text'>A rituálé állása: {st.session_state.step} / 16</p>", unsafe_allow_html=True)

    # --- A 16 LÉPCSŐS RITUÁLÉ (4 opcióval) ---
    
    steps = {
        1: ("Vizuális Alap (A kép lelke)", ["🌑 Mélyfekete Nihil", "🍷 Borvörös Melankólia", "🌫️ Hamuszürke Köd", "🕯️ Aranybarna Gyertyafény"]),
        2: ("Uralkodó Textúra", ["📜 Ódon, szakadt papír", "🪞 Tükörcserép", "🥀 Száradt szirom", "⛓️ Hideg láncok"]),
        3: ("Belső Hang (Zenei vibe)", ["🎹 Magányos zongora", "🎻 Sikoltó hegedű", "⛈️ Távoli dörgés", "🤫 Nyomasztó csend"]),
        4: ("Írói Gyónás (A mai bűnöd)", ["🪦 Ma mindenkit megölök", "🎭 Elvesztem a maszk mögött", "🧩 Csak kódokat látok", "☕ Túl sok kávé, nulla szó"]),
        5: ("Karakter-sors", ["🔥 Lassú égés", "🔪 Hirtelen árulás", "🧠 Mentális összeomlás", "🖤 Megváltó halál"]),
        6: ("A Szimbólum", ["🗝️ Véres kulcs", "🐦 Döglött holló", "🖼️ Üres képkeret", "💍 Elvesztett gyűrű"]),
        7: ("Célpont (Kihez szólunk?)", ["🤝 A hűséges olvasók", "👀 A néma figyelők", "👺 A belső démonok", "🌍 A közönyös világ"]),
        8: ("Aktuális érzelem", ["🧊 Megfagyott nihil", "🌋 Fojtott düh", "🌊 Sötét vágyakozás", "🍂 Fáradt beletörődés"]),
        9: ("Az Akadály", ["🚧 Plot hole (Szakadék)", "💤 Motivációhiány", "📱 A külvilág zaja", "🖋️ Öngyűlölet"]),
        10: ("Domináns Szín", ["🔴 Alvadt vér", "⚫ Éjfekete", "⚪ Csontfehér", "🟣 Sötétlila"]),
        11: ("Írói Klisé (Amit ma utálunk)", ["💘 Szerelmi háromszög", "🦄 Happy end", "⚡ Kiválasztott hős", "⏳ Cliffhanger"]),
        12: ("Titoktartási Szint", ["🕵️ Teljes inkognitó", "🎭 Elejtett utalások", "📂 Kiszivárgott részlet", "📢 Nyers őszinteség"]),
        13: ("Poszt Hangvétele", ["🖋️ Költői & Elvont", "🐍 Maróan szarkasztikus", "🔪 Rövid & Ideges", "🧠 Hideg & Logikus"]),
        14: ("Vizuális Stílus", ["🎥 Cinematic (Filmes)", "🎞️ Grainy (Szemcsés/Régi)", "🔳 Minimalista", "🎨 Szürreális"]),
        15: ("CTA (A végső lökés)", ["❓ Provokatív kérdés", "🥀 Csendes kérés", "⚠️ Figyelmeztetés", "🚪 Távozás angolosan"]),
        # A 16. lépés speciális (Input mező)
    }

    if st.session_state.step <= 15:
        title, options = steps[st.session_state.step]
        st.subheader(f"{st.session_state.step}. {title}")
        
        # 4 gombos elrendezés
        cols = st.columns(2)
        for i, opt in enumerate(options):
            with cols[i % 2]:
                if st.button(opt):
                    st.session_state.answers[f"step_{st.session_state.step}"] = opt
                    st.session_state.step += 1
                    st.rerun()

    elif st.session_state.step == 16:
        st.subheader("16. Külvilág-Misszió (Trend-vadászat)")
        st.info("Görgess 5-öt az Instán/TikTokon, vagy nézd meg a híreket. Mi a legfurább/legnépszerűbb dolog?")
        trend_input = st.text_input("Írd be a külső ingert:", placeholder="Pl. Szakított az álompár / Mindenki sminkvideót néz...")
        
        col_prev, col_gen = st.columns(2)
        with col_prev:
            if st.button("← Vissza"):
                st.session_state.step -= 1
                st.rerun()
        with col_gen:
            if st.button("🔥 GENERÁLÁS"):
                if trend_input:
                    st.session_state.answers['trend'] = trend_input
                    st.session_state.step += 1
                    st.rerun()
                else:
                    st.warning("A rituáléhoz szükség van a külvilág zajára is!")

    # --- VÉGEREDMÉNY GENERÁLÁSA ---
    if st.session_state.step > 16:
        st.subheader("🥀 A rituálé beteljesedett")
        
        with st.spinner("A Lehullott Múzsa összefűzi a sötétséget..."):
            time.sleep(3)
            
            # Adatok kinyerése
            vibe = st.session_state.answers.get('step_1', '')
            gyon = st.session_state.answers.get('step_4', '')
            trend = st.session_state.answers.get('trend', '')
            stilus = st.session_state.answers.get('step_13', '')
            
            # Komplexebb Híd logika (Példa)
            poszt_text = f"Míg kint a világ olyan felszínes dolgokon pörög, mint a '{trend}', addig én itt bent a saját démonaimmal küzdök. {gyon} \n\nA {vibe.lower()} hangulata rátelepedett a billentyűzetemre. Talán a valóság csak egy rossz díszlet az én történetemhez. \n\nTi is érzitek a szakadékot a hírek és a saját belső világotok között? 🥀👇"
            
            prompt_text = f"Dark academia, cinematic style, {st.session_state.answers.get('step_14', '')}. Subject: {st.session_state.answers.get('step_6', '')} in a {st.session_state.answers.get('step_10', '')} environment. Texture: {st.session_state.answers.get('step_2', '')}. Mood: {st.session_state.answers.get('step_8', '')}. High contrast, moody lighting, 8k resolution, photorealistic."

        st.markdown("### 📝 A Poszt szövege")
        st.text_area("Másold ki:", value=poszt_text, height=200)
        
        st.markdown("### 🎨 Nano Banana 2 Kép Prompt")
        st.code(prompt_text, language="text")
        
        if st.button("🔄 Új rituálé kezdése"):
            st.session_state.step = 1
            st.session_state.answers = {}
            st.rerun()

    # Navigációs gomb vissza (ha nem a végén vagyunk)
    if 1 < st.session_state.step <= 15:
        if st.button("← Előző lépés módosítása"):
            st.session_state.step -= 1
            st.rerun()
