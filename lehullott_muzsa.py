import streamlit as st
import time

# --- OLDALBEÁLLÍTÁSOK ---
st.set_page_config(
    page_title="A Lehullott Múzsa | Bara V.A. Privát Rituálé",
    page_icon="🥀",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- BARA V.A. EXTRA VIZUÁLIS ELEMEK (CSS) ---
st.markdown("""
    <style>
    .stApp {
        background: radial-gradient(circle at center, #3d0505 0%, #0a0101 100%);
        background-attachment: fixed;
        color: #F5F5F5;
        font-family: 'Georgia', serif;
    }
    .petal-container {
        position: fixed; top: 0; left: 0; width: 100%; height: 100%;
        pointer-events: none; z-index: 0;
    }
    .petal {
        position: absolute; background-color: #8B0000; opacity: 0.5;
        border-radius: 50% 0 50% 50%; animation: fall 12s linear infinite;
    }
    @keyframes fall {
        0% { transform: translateY(-10vh) rotate(0deg) translateX(0); }
        100% { transform: translateY(110vh) rotate(360deg) translateX(10px); }
    }
    div.stButton > button {
        background-color: rgba(26, 26, 26, 0.8); color: #F5F5F5; border: 1px solid #5a0505;
        border-radius: 12px; width: 100%; height: 90px; font-weight: bold;
        transition: all 0.4s ease; font-size: 18px; margin-bottom: 15px;
        backdrop-filter: blur(5px);
    }
    div.stButton > button:hover {
        background-color: #5a0505; border-color: #ff3b3b; color: white;
        transform: translateY(-5px); box-shadow: 0 10px 20px rgba(139,0,0,0.6);
    }
    h1 { color: #8B0000 !important; text-align: center; font-size: 3em; text-shadow: 2px 2px 4px #000; }
    h2 { color: #a30000 !important; text-align: center; margin-bottom: 1em; }
    .intro-box {
        background: rgba(0, 0, 0, 0.6); padding: 30px; border-radius: 20px;
        border: 1px solid #4A0404; text-align: center; margin-bottom: 30px;
        backdrop-filter: blur(10px);
    }
    .status-text { text-align: center; color: #666; font-size: 0.9em; margin-top: 10px; }
    .stProgress > div > div > div > div { background-color: #8B0000; }
    </style>
    <div class="petal-container">
        <div class="petal" style="width: 12px; height: 12px; left: 5%; animation-delay: 0s;"></div>
        <div class="petal" style="width: 18px; height: 18px; left: 25%; animation-delay: 2s;"></div>
        <div class="petal" style="width: 15px; height: 15px; left: 65%; animation-delay: 1s;"></div>
        <div class="petal" style="width: 20px; height: 20px; left: 85%; animation-delay: 3s;"></div>
        <div class="petal" style="width: 14px; height: 14px; left: 55%; animation-delay: 5s;"></div>
    </div>
""", unsafe_allow_html=True)

# --- JELSZÓVÉDELEM ---
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False
    if st.session_state["password_correct"]:
        return True
    
    st.markdown("<h1>🥀 A Lehullott Múzsa</h1>", unsafe_allow_html=True)
    st.markdown("""<div class="intro-box"><p style="font-size: 1.1em; line-height: 1.8;">
    Üdvözöllek, Írónőke. Ez a te belső szentélyed.<br>
    A rituálé célja, hogy 16 lépésben feltárjuk a mai napod mélyén rejlő történetet.</p></div>""", unsafe_allow_html=True)
    
    jelszo = st.text_input("Kódfejtő jelszó:", type="password", key="pwd_input")
    if jelszo:
        if jelszo == st.secrets["app_password"]:
            st.session_state["password_correct"] = True
            st.rerun()
        else:
            st.error("A kód hibás.")
    return False

if check_password():
    if 'step' not in st.session_state:
        st.session_state.step = 1
    if 'answers' not in st.session_state:
        st.session_state.answers = {}

    st.sidebar.markdown("### 🎧 Atmoszféra")
    st.sidebar.audio("https://www.soundhelix.com/examples/mp3/SoundHelix-Song-10.mp3")

    # JAVÍTOTT PROGRESS BAR (max 1.0)
    progress_val = min(st.session_state.step / 16, 1.0)
    st.progress(progress_val)
    
    if st.session_state.step <= 16:
        st.markdown(f"<p class='status-text'>Rituálé: {st.session_state.step} / 16</p>", unsafe_allow_html=True)

    steps = {
        1: ("Vizuális Alap", ["🌑 Mélyfekete Nihil", "🍷 Borvörös Melankólia", "🌫️ Hamuszürke Köd", "🕯️ Aranybarna Gyertyafény"]),
        2: ("Uralkodó Textúra", ["📜 Ódon, szakadt papír", "🪞 Tükörcserép", "🥀 Száradt szirom", "⛓️ Hideg láncok"]),
        3: ("Belső Hang", ["🎹 Magányos zongora", "🎻 Sikoltó hegedű", "⛈️ Távoli dörgés", "🤫 Nyomasztó csend"]),
        4: ("Írói Gyónás", ["🪦 Ma mindenkit megölök", "🎭 Elvesztem a maszk mögött", "🧩 Csak kódokat látok", "☕ Túl sok kávé, nulla szó"]),
        5: ("Karakter-sors", ["🔥 Lassú égés", "🔪 Hirtelen árulás", "🧠 Mentális összeomlás", "🖤 Megváltó halál"]),
        6: ("A Szimbólum", ["🗝️ Véres kulcs", "🐦 Döglött holló", "🖼️ Üres képkeret", "💍 Elvesztett gyűrű"]),
        7: ("Célpont", ["🤝 A hűséges olvasók", "👀 A néma figyelők", "👺 A belső démonok", "🌍 A közönyös világ"]),
        8: ("Aktuális érzelem", ["🧊 Megfagyott nihil", "🌋 Fojtott düh", "🌊 Sötét vágyakozás", "🍂 Fáradt beletörődés"]),
        9: ("Az Akadály", ["🚧 Plot hole", "💤 Motivációhiány", "📱 A külvilág zaja", "🖋️ Öngyűlölet"]),
        10: ("Domináns Szín", ["🔴 Alvadt vér", "⚫ Éjfekete", "⚪ Csontfehér", "🟣 Sötétlila"]),
        11: ("Írói Klisé", ["💘 Szerelmi háromszög", "🦄 Happy end", "⚡ Kiválasztott hős", "⏳ Cliffhanger"]),
        12: ("Titoktartási Szint", ["🕵️ Teljes inkognitó", "🎭 Elejtett utalások", "📂 Kiszivárgott részlet", "📢 Nyers őszinteség"]),
        13: ("Poszt Hangvétele", ["🖋️ Költői & Elvont", "🐍 Maróan szarkasztikus", "🔪 Rövid & Ideges", "🧠 Hideg & Logikus"]),
        14: ("Vizuális Stílus", ["🎥 Cinematic (Filmes)", "🎞️ Grainy (Szemcsés)", "🔳 Minimalista", "🎨 Szürreális"]),
        15: ("CTA", ["❓ Provokatív kérdés", "🥀 Csendes kérés", "⚠️ Figyelmeztetés", "🚪 Távozás angolosan"]),
    }

    if st.session_state.step <= 15:
        title, options = steps[st.session_state.step]
        st.markdown(f"<h2>{st.session_state.step}. {title}</h2>", unsafe_allow_html=True)
        cols = st.columns(2)
        for i, opt in enumerate(options):
            with cols[i % 2]:
                if st.button(opt, key=f"btn_{st.session_state.step}_{i}"):
                    st.session_state.answers[f"step_{st.session_state.step}"] = opt
                    st.session_state.step += 1
                    st.rerun()

    elif st.session_state.step == 16:
        st.markdown("<h2>16. Külvilág-Misszió</h2>", unsafe_allow_html=True)
        trend_input = st.text_input("Mi a legfurább dolog, amit ma láttál?", placeholder="Pl. Mindenki sminkvideót néz...")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("← Vissza"):
                st.session_state.step -= 1
                st.rerun()
        with c2:
            if st.button("🔥 GENERÁLÁS"):
                if trend_input:
                    st.session_state.answers['trend'] = trend_input
                    st.session_state.step += 1
                    st.rerun()
                else:
                    st.warning("A rituáléhoz kell a külvilág zaja.")

    if st.session_state.step > 16:
        st.markdown("<h1>🥀 Rituálé Beteljesítve</h1>", unsafe_allow_html=True)
        with st.spinner("Összefonjuk a sötétséget..."):
            time.sleep(2)
            ans = st.session_state.answers
            p_text = f"Míg kint '{ans.get('trend')}' a téma, addig én itt bent a '{ans.get('step_4')}' állapottal küzdök. A '{ans.get('step_1')}' tónusa mindent beborít. Stílus: {ans.get('step_13')}. {ans.get('step_15')}"
            img_prompt = f"Dark academia, {ans.get('step_14')}, {ans.get('step_10')}. Subject: {ans.get('step_6')}. Background: {ans.get('step_1')}. Texture: {ans.get('step_2')}. 8k, realistic."
        
        st.markdown("### 📝 A Posztod:")
        st.text_area("", value=p_text, height=150)
        st.markdown("### 🎨 Nano Banana Prompt:")
        st.code(img_prompt)
        if st.button("🔄 Új rituálé"):
            st.session_state.step = 1
            st.session_state.answers = {}
            st.rerun()

    if 1 < st.session_state.step <= 15:
        if st.button("← Előző lépés", key="global_back"):
            st.session_state.step -= 1
            st.rerun()
