"""
Livestock Health Assistant - Streamlit Interface (Week 4: sidebar navigation)
---------------------------------------------------------------------------------
Left sidebar now works as the main navigation menu:
  Chat, Disease Library, Emergency Guide, Vaccination Reminders

Chat history and reminders are saved to local JSON files (storage.py) so
they persist between app restarts - still fully offline.

Run with: streamlit run app.py
"""

import streamlit as st
import uuid
from datetime import date, datetime
from app_core import load_knowledge_base, get_response, get_daily_tip, analyze_image, transcribe_audio
from storage import (
    load_reminders, save_reminders,
    load_sessions, save_sessions,
)

st.set_page_config(page_title="Livestock Health Assistant", page_icon="🐄", layout="centered")

st.markdown("""
<style>
    .main .block-container { padding-top: 2rem; }
    .app-header {
        background: linear-gradient(115deg, #016670 0%, #028090 35%, #02C39A 100%);
        padding: 1.8rem 1.8rem; border-radius: 14px; margin-bottom: 1.2rem;
        position: relative; overflow: hidden; min-height: 170px;
    }
    .app-header h1 { color: white; margin: 0; font-size: 1.7rem; }
    .app-header p { color: #E3F3F1; margin: 0.35rem 0 0 0; font-size: 0.95rem; max-width: 480px; }
    .hero-blob {
        position: absolute; border-radius: 50%; background: rgba(255,255,255,0.10);
    }
    .hero-blob.b1 { width: 220px; height: 220px; right: -40px; top: -60px; }
    .hero-blob.b2 { width: 160px; height: 160px; right: 120px; bottom: -70px; background: rgba(255,255,255,0.08); }
    .hero-animals {
        position: absolute; right: 2rem; bottom: 0.5rem;
        display: flex; align-items: flex-end; gap: 0.3rem; z-index: 2;
    }
    .hero-animals span {
        filter: drop-shadow(0 6px 10px rgba(0,0,0,0.18));
    }
    .hero-animals .a1 { font-size: 2.6rem; margin-bottom: 0.2rem; }
    .hero-animals .a2 { font-size: 3rem; }
    .hero-animals .a3 { font-size: 3.8rem; }
    .top-status-bar {
        display: flex; justify-content: flex-end; align-items: center;
        gap: 0.6rem; margin-bottom: 0.6rem; font-size: 0.82rem; color: #2E7D32;
    }
    .top-status-bar .dot { color: #2E7D32; }
    .quick-label { font-size: 0.85rem; color: #5C6F6C; margin-bottom: 0.3rem; font-weight: 600; }
    div[data-testid="stSidebar"] { background-color: #F4F7F6; }
    .stChatMessage { border-radius: 12px; }
    .lib-card {
        background-color: #FFFFFF; border-radius: 12px; padding: 1rem 1.2rem;
        margin-bottom: 0.8rem; border-left: 4px solid #028090;
    }
    .lib-card.emergency { border-left: 4px solid #D64545; background-color: #FDECEC; }
    .reminder-card {
        background-color: #FFFFFF; border-radius: 10px; padding: 0.8rem 1rem;
        margin-bottom: 0.6rem;
    }
    .reminder-overdue { border-left: 4px solid #D64545; background-color: #FDECEC; }
    .reminder-soon { border-left: 4px solid #E8A33D; background-color: #FFF6E5; }
    .reminder-ok { border-left: 4px solid #02C39A; }
    /* Sidebar: white background, clean nav list like a modern chat app */
    section[data-testid="stSidebar"], div[data-testid="stSidebar"] {
        background-color: #FAFBFB !important;
        border-right: 1px solid #E7ECEB;
    }
    /* Flat, list-style buttons - no box, no border, just a hover highlight */
    section[data-testid="stSidebar"] div[data-testid="stButton"] button,
    div[data-testid="stSidebar"] div[data-testid="stButton"] button {
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
        outline: none !important;
        color: #2B3A38 !important;
        font-weight: 400 !important;
        font-size: 0.92rem !important;
        padding: 0.5rem 0.7rem !important;
        border-radius: 8px !important;
        margin: 0.05rem 0 !important;
        width: 100% !important;
        display: flex !important;
        align-items: center !important;
        justify-content: flex-start !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stButton"] button > div,
    div[data-testid="stSidebar"] div[data-testid="stButton"] button > div,
    section[data-testid="stSidebar"] div[data-testid="stButton"] button p,
    div[data-testid="stSidebar"] div[data-testid="stButton"] button p {
        text-align: left !important;
        justify-content: flex-start !important;
        width: 100% !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stButton"] button:hover,
    div[data-testid="stSidebar"] div[data-testid="stButton"] button:hover {
        background-color: #EDEFEF !important;
        color: #1A2E2A !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stButton"] button:focus,
    div[data-testid="stSidebar"] div[data-testid="stButton"] button:focus,
    section[data-testid="stSidebar"] div[data-testid="stButton"] button:active,
    div[data-testid="stSidebar"] div[data-testid="stButton"] button:active {
        box-shadow: none !important;
        outline: none !important;
        border: none !important;
    }
    /* Active nav item / active chat - a static highlighted row (not a button) */
    .nav-active {
        background-color: #E4F0EF;
        color: #028090;
        font-weight: 600;
        padding: 0.5rem 0.7rem;
        border-radius: 8px;
        margin: 0.05rem 0;
        font-size: 0.92rem;
    }
    .recent-active {
        background-color: #E4F0EF;
        color: #028090;
        font-weight: 500;
        padding: 0.5rem 0.7rem;
        border-radius: 8px;
        margin: 0.05rem 0;
        font-size: 0.87rem;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .sidebar-section-label {
        font-size: 0.78rem;
        color: #8A9694;
        font-weight: 600;
        letter-spacing: 0.03em;
        margin: 1rem 0 0.3rem 0.5rem;
        text-transform: uppercase;
    }

    /* --- Homepage / Chat page polish --- */
    .hero-badges { margin-top: 0.6rem; }
    .hero-badge {
        display: inline-block;
        background-color: rgba(255,255,255,0.18);
        color: #FFFFFF;
        font-size: 0.75rem;
        font-weight: 600;
        padding: 0.25rem 0.7rem;
        border-radius: 999px;
        margin-right: 0.4rem;
    }
    .tip-card {
        background: linear-gradient(135deg, #FFF8E8 0%, #FFF3D6 100%);
        border-left: 4px solid #E8A33D;
        border-radius: 10px;
        padding: 0.7rem 1rem;
        margin-bottom: 1.1rem;
        font-size: 0.9rem;
        color: #6B4E1E;
    }
    .section-title {
        font-size: 0.95rem;
        font-weight: 700;
        color: #2B3A38;
        margin: 0.4rem 0 0.6rem 0;
    }
    div[data-testid="stButton"] button {
        border: 1px solid #E7ECEB !important;
        background-color: #FFFFFF !important;
        border-radius: 10px !important;
        padding: 0.7rem 0.8rem !important;
        font-weight: 500 !important;
        color: #2B3A38 !important;
        transition: all 0.15s ease;
        box-shadow: 0 1px 2px rgba(0,0,0,0.04);
    }
    div[data-testid="stButton"] button:hover {
        border-color: #028090 !important;
        background-color: #F0F9F8 !important;
        color: #028090 !important;
        box-shadow: 0 2px 8px rgba(2,128,144,0.12);
        transform: translateY(-1px);
    }
    div[data-testid="stButton"] button:focus,
    div[data-testid="stButton"] button:focus:not(:active) {
        border-color: #E7ECEB !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.04) !important;
        outline: none !important;
    }
    .welcome-box {
        text-align: center;
        padding: 2rem 1rem;
        color: #8A9694;
        font-size: 0.95rem;
    }
    .welcome-box .big-emoji { font-size: 2.2rem; margin-bottom: 0.5rem; }

    .stat-card {
        background-color: #FFFFFF;
        border: 1px solid #E7ECEB;
        border-radius: 12px;
        padding: 0.9rem 1rem;
        text-align: center;
    }
    .stat-number { font-size: 1.5rem; font-weight: 700; color: #028090; }
    .stat-label { font-size: 0.78rem; color: #5C6F6C; }

    .animal-picked {
        border: 2px solid #028090 !important;
        background-color: #F0F9F8 !important;
        color: #028090 !important;
    }

    .feature-card {
        border-radius: 12px;
        padding: 0.9rem 1rem;
        height: 100%;
    }
    .feature-card.green { background-color: #E9F7F1; }
    .feature-card.blue { background-color: #E9F1FB; }
    .feature-card.purple { background-color: #F2ECFB; }
    .feature-card.yellow { background-color: #FFF6E0; }
    .feature-card b { display: block; margin-bottom: 0.2rem; }
    .feature-card .fc-desc { font-size: 0.82rem; color: #5C6F6C; margin-bottom: 0.5rem; }

    .emergency-box {
        background-color: #FDECEC;
        border-radius: 10px;
        padding: 0.8rem 0.9rem;
        margin-bottom: 1rem;
    }
    .emergency-box b { color: #B02A2A; }
    .emergency-box ul { margin: 0.4rem 0 0.3rem 1.1rem; padding: 0; font-size: 0.82rem; color: #7A2E2E; }
    .emergency-box .contact-line { color: #B02A2A; font-weight: 600; font-size: 0.82rem; }
</style>
""", unsafe_allow_html=True)

if "kb" not in st.session_state:
    st.session_state.kb = load_knowledge_base()
if "sessions" not in st.session_state:
    st.session_state.sessions = load_sessions()  # {id: {title, timestamp, messages}}
if "current_session_id" not in st.session_state:
    st.session_state.current_session_id = None
if "reminders" not in st.session_state:
    st.session_state.reminders = load_reminders()


def get_current_messages():
    sid = st.session_state.current_session_id
    if sid and sid in st.session_state.sessions:
        return st.session_state.sessions[sid]["messages"]
    return []


def add_message_to_current_session(role, text, animal_type=None):
    sid = st.session_state.current_session_id
    if sid is None:
        # Starting a brand new conversation - create it now, titled after the
        # first message so it's recognizable in the Recent list.
        sid = str(uuid.uuid4())[:8]
        st.session_state.current_session_id = sid
        st.session_state.sessions[sid] = {
            "title": text[:45] + ("..." if len(text) > 45 else ""),
            "timestamp": datetime.now().isoformat(),
            "animal": animal_type or "",
            "messages": [],
        }
    st.session_state.sessions[sid]["messages"].append([role, text])
    save_sessions(st.session_state.sessions)


def time_ago(iso_timestamp):
    """Turns an ISO timestamp into a friendly relative string, e.g. '2 hours ago'."""
    try:
        then = datetime.fromisoformat(iso_timestamp)
    except (ValueError, TypeError):
        return ""
    delta = datetime.now() - then
    seconds = delta.total_seconds()
    if seconds < 60:
        return "just now"
    if seconds < 3600:
        mins = int(seconds // 60)
        return f"{mins} minute{'s' if mins != 1 else ''} ago"
    if seconds < 86400:
        hours = int(seconds // 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    days = int(seconds // 86400)
    return f"{days} day{'s' if days != 1 else ''} ago"


def compute_real_stats():
    """
    Real, honest numbers pulled from actual local data - no fabricated
    marketing stats. 'This month' is computed from real session timestamps.
    """
    now = datetime.now()
    sessions_this_month = [
        s for s in st.session_state.sessions.values()
        if datetime.fromisoformat(s["timestamp"]).month == now.month
        and datetime.fromisoformat(s["timestamp"]).year == now.year
    ]
    consultations_this_month = sum(
        len(s["messages"]) // 2 for s in sessions_this_month
    )
    return {
        "consultations": consultations_this_month,
        "conversations": len(sessions_this_month),
        "conditions": len(st.session_state.kb),
        "languages": 2,
    }

# ============================== SIDEBAR NAV ==============================
st.sidebar.markdown(
    '<div style="font-weight:700; font-size:1.05rem; padding:0.3rem 0.5rem;">🐄 Livestock Health Assistant</div>'
    '<div style="color:#8A9694; font-size:0.8rem; padding:0 0.5rem 0.5rem 0.5rem;">Offline AI guidance for smallholder farmers</div>',
    unsafe_allow_html=True,
)

if "current_session_id" not in st.session_state:
    st.session_state.current_session_id = None
if "renaming_session_id" not in st.session_state:
    st.session_state.renaming_session_id = None
if "selected_animal" not in st.session_state:
    st.session_state.selected_animal = "Cattle (ላም)"

# --- Language selector: always visible at the top, not tied to a specific page ---
response_language = st.sidebar.selectbox(
    "Response language", ["English", "Amharic (አማርኛ)"], label_visibility="collapsed",
)
language_code = "Amharic" if response_language.startswith("Amharic") else "English"

st.sidebar.markdown('<div style="height:0.3rem;"></div>', unsafe_allow_html=True)

# --- Menu: internal key (used in code) + display label (what's shown) ---
# internal keys stay the same as before so nothing else in the file needs to change
MENU_OPTIONS = [
    ("🏠", "Chat", "Home"),
    ("📚", "Disease Library", "Disease Library"),
    ("🚨", "Emergency Guide", "Emergency Guide"),
    ("📅", "Vaccination Reminders", "Vaccination Guide"),
    ("💡", "Daily Tips", "Daily Tips"),
    ("🕐", "My Consultations", "My Consultations"),
    ("⚙️", "Settings", "Settings"),
    ("ℹ️", "About", "About"),
]
if "current_page" not in st.session_state:
    st.session_state.current_page = MENU_OPTIONS[0][1]

# --- New Consultation ---
if st.sidebar.button("📝  New Consultation", use_container_width=True):
    st.session_state.current_session_id = None
    st.session_state.current_page = "Chat"
    st.rerun()

st.sidebar.markdown('<div style="height:0.15rem;"></div>', unsafe_allow_html=True)

# --- Main nav: active item shown as a static highlighted row, others as flat buttons ---
for icon, key, display in MENU_OPTIONS:
    if st.session_state.current_page == key:
        st.sidebar.markdown(f'<div class="nav-active">{icon}&nbsp;&nbsp;{display}</div>', unsafe_allow_html=True)
    else:
        if st.sidebar.button(f"{icon}  {display}", key=f"menu_{key}", use_container_width=True):
            st.session_state.current_page = key
            st.rerun()

page = st.session_state.current_page

st.sidebar.markdown("---")

st.sidebar.markdown(
    """
    <div class="emergency-box">
    <b>⚠️ Emergency Signs</b>
    <ul>
        <li>Cannot stand</li>
        <li>Severe bleeding</li>
        <li>Difficulty breathing</li>
        <li>Suspected poisoning</li>
        <li>Seizures</li>
    </ul>
    <div class="contact-line">Contact a veterinarian immediately.</div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.sidebar.markdown(
    """
    <div style="background-color:#FDECEC; padding:0.5rem 0.6rem; border-radius:8px; font-size:0.72rem; color:#7A2E2E; line-height:1.3;">
    ⚠️ General guidance only. Always consult a local veterinarian for serious or persistent symptoms.<br><br>
    ⚠️ አጠቃላይ መመሪያ ብቻ ነው። ለከባድ ምልክቶች ሁልጊዜ የእንስሳት ሐኪም ያማክሩ።
    </div>
    """,
    unsafe_allow_html=True,
)

st.sidebar.markdown(
    """
    <div style="background-color:#E9F7F1; border-radius:10px; padding:0.6rem 0.8rem; margin-top:0.8rem; font-size:0.82rem;">
    🌿 <b>Livestock Health Assistant</b><br>
    <span style="color:#5C6F6C; font-size:0.75rem;">Version 1.0.0</span>
    </div>
    """,
    unsafe_allow_html=True,
)

# ============================== MAIN AREA ==============================
st.markdown("""
<div class="top-status-bar">
    <span class="dot">🔌</span> Runs fully offline — no internet required
</div>
<div class="app-header">
    <div class="hero-blob b1"></div>
    <div class="hero-blob b2"></div>
    <div class="hero-animals">
        <span class="a1">🐐</span><span class="a2">🐑</span><span class="a3">🐄</span>
    </div>
    <h1>🐄 Livestock Health Assistant</h1>
    <p>የከብት ጤና ረዳት &nbsp;|&nbsp; Offline AI guidance for smallholder farmers — not a replacement for a vet.</p>
    <div class="hero-badges">
        <span class="hero-badge">🔌 Works Offline</span>
        <span class="hero-badge">🌐 English + Amharic</span>
        <span class="hero-badge">🚨 Emergency Detection</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ------------------------------ CHAT PAGE ------------------------------
if page == "Chat":
    # --- Real stats (no fabricated numbers) ---
    stats = compute_real_stats()
    scol1, scol2, scol3, scol4 = st.columns(4)
    with scol1:
        st.markdown(f'<div class="stat-card"><div class="stat-number">{stats["consultations"]}</div>'
                     f'<div class="stat-label">Consultations<br>This month (this device)</div></div>', unsafe_allow_html=True)
    with scol2:
        st.markdown(f'<div class="stat-card"><div class="stat-number">{stats["conversations"]}</div>'
                     f'<div class="stat-label">Conversations<br>This month (this device)</div></div>', unsafe_allow_html=True)
    with scol3:
        st.markdown(f'<div class="stat-card"><div class="stat-number">{stats["conditions"]}</div>'
                     f'<div class="stat-label">Diseases<br>Covered by our AI</div></div>', unsafe_allow_html=True)
    with scol4:
        st.markdown(f'<div class="stat-card"><div class="stat-number">{stats["languages"]}</div>'
                     f'<div class="stat-label">Languages<br>English, አማርኛ</div></div>', unsafe_allow_html=True)

    st.markdown('<div style="height:0.8rem;"></div>', unsafe_allow_html=True)

    st.markdown(
        f'<div class="tip-card">💡 <b>Daily Tip:</b> {get_daily_tip(language_code)}</div>',
        unsafe_allow_html=True,
    )

    # --- Animal picker (icon grid, replaces the old dropdown) ---
    st.markdown('<div class="section-title">Select Animal / እንስሳ ይምረጡ</div>', unsafe_allow_html=True)
    ANIMAL_OPTIONS = [
        ("🐄", "Cattle", "Cattle (ላም)"),
        ("🐐", "Goat", "Goat (ፍየል)"),
        ("🐔", "Poultry", "Poultry (ዶሮ)"),
        ("❓", "Not Sure", "Other / Not sure (ሌላ)"),
    ]
    acols = st.columns(4)
    for i, (icon, label, value) in enumerate(ANIMAL_OPTIONS):
        with acols[i]:
            is_selected = st.session_state.selected_animal == value
            btn_label = f"{'✅ ' if is_selected else ''}{icon} {label}"
            if st.button(btn_label, key=f"animal_{i}", use_container_width=True):
                st.session_state.selected_animal = value
                st.rerun()
    animal_type = st.session_state.selected_animal

    with st.expander("+ Add age, sex, weight (optional) / እድሜ፣ ጾታ፣ ክብደት"):
        aw1, aw2, aw3 = st.columns(3)
        with aw1:
            animal_age = st.text_input("Age", placeholder="e.g. 2 years")
        with aw2:
            animal_sex = st.selectbox("Sex", ["", "Female", "Male"])
        with aw3:
            animal_weight = st.text_input("Weight (optional)", placeholder="e.g. 250 kg")

    QUICK_SYMPTOMS = [
        ("🫃 Swollen belly", "belly is swollen and it won't eat"),
        ("🦵 Limping", "limping and bad smell from its foot"),
        ("💩 Diarrhea", "watery diarrhea for two days"),
        ("😮\u200d💨 Breathing trouble", "coughing with fast breathing"),
        ("👁️ Eye problem", "cloudy red eye"),
        ("🐔 Egg drop", "stopped laying eggs this week"),
    ]

    st.markdown('<div class="section-title">Quick tap — common symptoms / የተለመዱ ምልክቶች</div>', unsafe_allow_html=True)
    cols = st.columns(3)
    quick_pick = None
    for i, (label, symptom) in enumerate(QUICK_SYMPTOMS):
        with cols[i % 3]:
            if st.button(label, use_container_width=True, key=f"quick_{i}"):
                quick_pick = symptom

    current_messages = get_current_messages()
    if not current_messages:
        st.markdown(
            """
            <div class="welcome-box">
                <div class="big-emoji">🩺</div>
                <b>How can I help today?</b><br>
                Describe a symptom below, tap a common one above,
                or use the photo / voice options.
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown('<div class="section-title">Conversation</div>', unsafe_allow_html=True)
        for role, text in current_messages:
            with st.chat_message(role):
                st.markdown(text)

    st.markdown('<div class="section-title">Other ways to describe symptoms</div>', unsafe_allow_html=True)

    photo_col, voice_col = st.columns(2)

    # --- Photo upload (optional alternative to typing) ---
    with photo_col:
        with st.expander("📷 Upload Animal Photo / የእንስሳ ፎቶ ይላኩ"):
            st.caption(
                "Useful for eye problems, skin issues, wounds, or swelling. "
                "The photo is only described, never diagnosed directly — the description "
                "still goes through the same safety-checked knowledge base as typed symptoms."
            )
            uploaded_photo = st.file_uploader(
                "Choose a photo", type=["jpg", "jpeg", "png"], label_visibility="collapsed"
            )
            photo_symptom_request = None
            if uploaded_photo is not None:
                st.image(uploaded_photo, width=200)
                if st.button("🔍 Analyze Photo"):
                    with st.spinner("Looking at the photo... / ፎቶውን በመመልከት ላይ..."):
                        image_bytes = uploaded_photo.getvalue()
                        description = analyze_image(image_bytes, animal_type=animal_type)
                    photo_symptom_request = description
                    st.caption(f"Detected: *{description}*")

    # --- Voice input (optional alternative to typing) ---
    with voice_col:
        with st.expander("🎤 Describe Symptoms by Voice / በድምጽ ይግለጹ"):
            st.caption(
                "Speak your symptom description instead of typing. Transcription runs "
                "fully offline. Amharic accuracy is still being tested - if it comes out "
                "wrong, try English or type instead."
            )
            voice_symptom_request = None
            whisper_lang = "am" if language_code == "Amharic" else "en"

            if hasattr(st, "audio_input"):
                audio_data = st.audio_input("Record your description", label_visibility="collapsed")
                if audio_data is not None:
                    if st.button("📝 Transcribe Recording"):
                        with st.spinner("Transcribing... / ድምጽ በመተርጎም ላይ..."):
                            transcript = transcribe_audio(audio_data.getvalue(), language_hint=whisper_lang)
                        voice_symptom_request = transcript
                        st.caption(f"Transcribed: *{transcript}*")
            else:
                # Fallback for older Streamlit versions without built-in mic recording:
                # accept an audio file recorded elsewhere (e.g. phone voice memo).
                st.caption("Your Streamlit version doesn't support live mic recording - upload an audio file instead.")
                uploaded_audio = st.file_uploader(
                    "Upload audio file", type=["wav", "mp3", "m4a", "ogg"], label_visibility="collapsed"
                )
                if uploaded_audio is not None and st.button("📝 Transcribe Audio File"):
                    with st.spinner("Transcribing... / ድምጽ በመተርጎም ላይ..."):
                        transcript = transcribe_audio(uploaded_audio.getvalue(), language_hint=whisper_lang)
                    voice_symptom_request = transcript
                    st.caption(f"Transcribed: *{transcript}*")

    typed_input = st.chat_input("Describe the symptom you're seeing... / ምልክቱን ይግለጹ...")
    from_photo = False
    from_voice = False
    user_input = typed_input or quick_pick
    if not user_input and photo_symptom_request:
        user_input = photo_symptom_request
        from_photo = True
    elif not user_input and voice_symptom_request:
        user_input = voice_symptom_request
        from_voice = True

    if user_input:
        full_symptom_text = f"[{animal_type}] {user_input}"

        # Build a readable animal-info line if any optional fields were filled in
        info_bits = []
        if animal_age:
            info_bits.append(f"📅 Age: {animal_age}")
        if animal_sex:
            info_bits.append(f"⚥ Sex: {animal_sex}")
        if animal_weight:
            info_bits.append(f"⚖️ Weight: {animal_weight}")
        animal_info_str = "  |  ".join(info_bits) if info_bits else None

        display_user_text = user_input
        if from_photo:
            display_user_text = f"📷 *Photo shows:* {user_input}"
        elif from_voice:
            display_user_text = f"🎤 *Voice:* {user_input}"
        if animal_info_str:
            display_user_text = f"*{animal_info_str}*\n\n{display_user_text}"

        add_message_to_current_session("user", display_user_text, animal_type=animal_type)
        with st.chat_message("user"):
            st.markdown(display_user_text)

        with st.chat_message("assistant"):
            with st.spinner("Checking... / በመፈተሽ ላይ..."):
                answer = get_response(
                    full_symptom_text, st.session_state.kb,
                    language=language_code, animal_info=animal_info_str,
                )
            if "EMERGENCY" in answer or "አደጋ" in answer:
                st.error(answer)
            else:
                st.markdown(answer)

        add_message_to_current_session("assistant", answer)

    # --- Bottom summary row: real data only, no weather widget ---
    st.markdown('<div style="height:1rem;"></div>', unsafe_allow_html=True)
    bcol1, bcol2, bcol3 = st.columns(3)

    with bcol1:
        recent_sessions = sorted(
            st.session_state.sessions.items(), key=lambda kv: kv[1]["timestamp"], reverse=True,
        )[:3]
        rows = ""
        for sid, s in recent_sessions:
            animal_label = s.get("animal", "").split(" (")[0] or "—"
            rows += f'<div style="margin:0.4rem 0; font-size:0.85rem;"><b>{s["title"]}</b><br>' \
                    f'<span style="color:#5C6F6C; font-size:0.78rem;">{animal_label} • {time_ago(s["timestamp"])}</span></div>'
        if not rows:
            rows = '<div style="color:#8A9694; font-size:0.85rem;">No consultations yet</div>'
        st.markdown(f'''
            <div class="feature-card blue">
                <b>🕐 Recent Consultations</b>
                {rows}
            </div>
        ''', unsafe_allow_html=True)
        if st.button("View all →", key="recent_view_all", use_container_width=True):
            st.session_state.current_page = "My Consultations"
            st.rerun()

    with bcol2:
        st.markdown('''
            <div class="feature-card purple">
                <b>📚 Disease Library</b>
                <div class="fc-desc">Browse all 12 conditions covered, in English and Amharic.</div>
            </div>
        ''', unsafe_allow_html=True)
        if st.button("Browse Library →", key="lib_teaser", use_container_width=True):
            st.session_state.current_page = "Disease Library"
            st.rerun()

    with bcol3:
        upcoming = sorted(st.session_state.reminders, key=lambda r: r["due_date"])[:3]
        rows = ""
        for r in upcoming:
            rows += f'<div style="margin:0.4rem 0; font-size:0.85rem;"><b>{r["animal"]}</b>: {r["vaccine"]}<br>' \
                    f'<span style="color:#5C6F6C; font-size:0.78rem;">Due {r["due_date"]}</span></div>'
        if not rows:
            rows = '<div style="color:#8A9694; font-size:0.85rem;">No reminders yet</div>'
        st.markdown(f'''
            <div class="feature-card yellow">
                <b>💉 Vaccination Reminders</b>
                {rows}
            </div>
        ''', unsafe_allow_html=True)
        if st.button("View All →", key="vax_teaser", use_container_width=True):
            st.session_state.current_page = "Vaccination Reminders"
            st.rerun()

# -------------------------- DISEASE LIBRARY PAGE --------------------------
elif page == "Disease Library":
    st.subheader("📚 Disease Library / የበሽታ ማውጫ")
    st.caption("Browse all conditions currently in the knowledge base.")

    animal_filter = st.selectbox(
        "Filter by animal / በእንስሳ አጣራ",
        ["All", "cattle", "goat", "poultry", "general"],
    )

    for entry in st.session_state.kb:
        if animal_filter != "All" and entry["animal"] != animal_filter:
            continue
        card_class = "lib-card emergency" if entry.get("emergency") else "lib-card"
        emergency_tag = " 🚨 Emergency" if entry.get("emergency") else ""
        st.markdown(f"""
        <div class="{card_class}">
            <b>{entry['condition']}{emergency_tag}</b> <span style="color:#5C6F6C;">({entry['animal']})</span><br>
            <span style="color:#5C6F6C; font-size:0.9rem;">{entry.get('condition_am','')}</span>
            <p style="margin-top:0.5rem;">{entry['advice']}</p>
            <p style="color:#5C6F6C; font-size:0.9rem;">{entry.get('advice_am','')}</p>
        </div>
        """, unsafe_allow_html=True)

# -------------------------- EMERGENCY GUIDE PAGE --------------------------
elif page == "Emergency Guide":
    st.subheader("🚨 Emergency Guide / የአደጋ መመሪያ")
    st.caption("These conditions need urgent veterinary attention. Learn to recognize them.")

    emergencies = [e for e in st.session_state.kb if e.get("emergency")]
    for entry in emergencies:
        keywords_preview = ", ".join(entry["keywords"][:4])
        st.markdown(f"""
        <div class="lib-card emergency">
            <b>🚨 {entry['condition']}</b> <span style="color:#5C6F6C;">({entry['animal']})</span><br>
            <span style="color:#5C6F6C; font-size:0.9rem;">{entry.get('condition_am','')}</span>
            <p style="margin-top:0.5rem;"><b>Watch for:</b> {keywords_preview}</p>
            <p>{entry['advice']}</p>
        </div>
        """, unsafe_allow_html=True)

    st.info(
        "🌐 If you're ever unsure whether something is an emergency, treat it as one. "
        "It's always safer to contact a vet and be told it's not urgent, than to wait too long."
    )

# ------------------------ VACCINATION REMINDERS PAGE ------------------------
elif page == "Vaccination Reminders":
    st.subheader("📅 Vaccination Reminders / የክትባት ማስታወሻ")
    st.caption("Track upcoming vaccinations for your animals. Saved locally on this device.")

    with st.form("add_reminder_form", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            r_animal = st.text_input("Animal name/ID", placeholder="e.g. Cow #3")
        with col2:
            r_vaccine = st.text_input("Vaccine", placeholder="e.g. Anthrax")
        with col3:
            r_date = st.date_input("Due date", value=date.today())
        submitted = st.form_submit_button("➕ Add reminder")

        if submitted and r_animal and r_vaccine:
            new_reminder = {
                "id": f"{r_animal}_{r_vaccine}_{r_date.isoformat()}",
                "animal": r_animal,
                "vaccine": r_vaccine,
                "due_date": r_date.isoformat(),
            }
            st.session_state.reminders.append(new_reminder)
            save_reminders(st.session_state.reminders)
            st.rerun()

    st.markdown("---")

    if not st.session_state.reminders:
        st.caption("No reminders yet. Add one above.")
    else:
        sorted_reminders = sorted(st.session_state.reminders, key=lambda r: r["due_date"])
        today = date.today()

        for r in sorted_reminders:
            due = datetime.strptime(r["due_date"], "%Y-%m-%d").date()
            days_left = (due - today).days

            if days_left < 0:
                status_class, status_text = "reminder-overdue", f"⚠️ Overdue by {-days_left} day(s)"
            elif days_left <= 7:
                status_class, status_text = "reminder-soon", f"⏰ Due in {days_left} day(s)"
            else:
                status_class, status_text = "reminder-ok", f"Due {r['due_date']}"

            col_a, col_b = st.columns([5, 1])
            with col_a:
                st.markdown(f"""
                <div class="reminder-card {status_class}">
                    <b>{r['animal']}</b> — {r['vaccine']}<br>
                    <span style="font-size:0.85rem; color:#5C6F6C;">{status_text}</span>
                </div>
                """, unsafe_allow_html=True)
            with col_b:
                if st.button("Delete", key=f"del_{r['id']}"):
                    st.session_state.reminders = [
                        x for x in st.session_state.reminders if x["id"] != r["id"]
                    ]
                    save_reminders(st.session_state.reminders)
                    st.rerun()

# ------------------------------ DAILY TIPS PAGE ------------------------------
elif page == "Daily Tips":
    from app_core import PREVENTION_TIPS
    st.subheader("💡 Daily Tips / የቀን ምክሮች")
    st.caption("Simple prevention habits that reduce livestock illness before it starts.")
    for tip_en, tip_am in PREVENTION_TIPS:
        st.markdown(f"""
        <div class="lib-card">
            <p style="margin:0;">💡 {tip_en}</p>
            <p style="margin:0.3rem 0 0 0; color:#5C6F6C; font-size:0.88rem;">{tip_am}</p>
        </div>
        """, unsafe_allow_html=True)

# ------------------------------ ABOUT PAGE ------------------------------
elif page == "My Consultations":
    st.subheader("🕐 My Consultations / የእኔ ምክክሮች")
    st.caption("All past conversations, saved locally on this device. Click one to reopen it.")

    all_sessions = sorted(
        st.session_state.sessions.items(), key=lambda kv: kv[1]["timestamp"], reverse=True,
    )
    if not all_sessions:
        st.info("No consultations yet. Start one from the Home page.")
    else:
        for sid, session in all_sessions:
            if st.session_state.renaming_session_id == sid:
                new_title = st.text_input(
                    "Rename", value=session["title"], key=f"myc_rename_{sid}", label_visibility="collapsed",
                )
                rc1, rc2 = st.columns([1, 1])
                with rc1:
                    if st.button("✅ Save", key=f"myc_save_{sid}", use_container_width=True):
                        st.session_state.sessions[sid]["title"] = new_title.strip() or session["title"]
                        save_sessions(st.session_state.sessions)
                        st.session_state.renaming_session_id = None
                        st.rerun()
                with rc2:
                    if st.button("✖️ Cancel", key=f"myc_cancel_{sid}", use_container_width=True):
                        st.session_state.renaming_session_id = None
                        st.rerun()
            else:
                animal_label = session.get("animal", "").split(" (")[0] or "—"
                c1, c2, c3 = st.columns([5, 1, 1])
                with c1:
                    st.markdown(f"""
                    <div class="lib-card">
                        <b>{session['title']}</b><br>
                        <span style="color:#5C6F6C; font-size:0.82rem;">{animal_label} • {time_ago(session['timestamp'])} • {len(session['messages'])//2} exchange(s)</span>
                    </div>
                    """, unsafe_allow_html=True)
                    if st.button("Open", key=f"myc_open_{sid}", use_container_width=True):
                        st.session_state.current_session_id = sid
                        st.session_state.current_page = "Chat"
                        st.rerun()
                with c2:
                    if st.button("✏️", key=f"myc_rename_btn_{sid}"):
                        st.session_state.renaming_session_id = sid
                        st.rerun()
                with c3:
                    if st.button("🗑️", key=f"myc_del_{sid}"):
                        del st.session_state.sessions[sid]
                        save_sessions(st.session_state.sessions)
                        if st.session_state.current_session_id == sid:
                            st.session_state.current_session_id = None
                        st.rerun()

# ------------------------------ SETTINGS PAGE ------------------------------
elif page == "Settings":
    st.subheader("⚙️ Settings")

    st.markdown("**Data management**")
    st.caption("Everything is stored locally on this device — nothing is uploaded anywhere.")

    if st.button("🗑️ Clear all consultations"):
        st.session_state.sessions = {}
        save_sessions({})
        st.session_state.current_session_id = None
        st.success("All consultations cleared.")

    if st.button("🗑️ Clear all vaccination reminders"):
        st.session_state.reminders = []
        save_reminders([])
        st.success("All reminders cleared.")

    st.markdown("---")
    st.markdown("**App info**")
    st.caption(f"Conditions in knowledge base: {len(st.session_state.kb)}")
    st.caption("Languages: English, Amharic")
    st.caption("Version 1.0.0")

# ------------------------------ ABOUT PAGE ------------------------------
elif page == "About":
    st.subheader("ℹ️ About this app")
    st.markdown("""
    **Livestock Health Assistant** is an offline AI assistant that helps smallholder
    farmers in Ethiopia identify common livestock symptoms and get practical,
    structured guidance — with no internet connection required.

    **How it works:** symptoms are matched against a curated veterinary knowledge
    base covering 12 conditions across cattle, goats, and poultry. Responses are
    built from that curated data (not freely generated), so the structure and
    safety information stay consistent every time. A small local AI model adds
    natural phrasing on top, and a separate model can describe photos or
    transcribe spoken symptoms — all running entirely on-device.

    **Built for accessibility:** full bilingual support in English and Amharic,
    quick-tap common symptoms, photo upload, and voice input, so the app is usable
    regardless of literacy level or typing comfort.

    **Disclaimer:** this tool provides preliminary guidance only and does not
    replace professional veterinary care. In any emergency or when an animal is
    in visible distress, contact a veterinarian immediately.
    """)
    st.caption("Version 1.0.0")
