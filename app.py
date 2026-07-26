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
from app_core import load_knowledge_base, get_response
from storage import (
    load_reminders, save_reminders,
    load_sessions, save_sessions,
)

st.set_page_config(page_title="Livestock Health Assistant", page_icon="🐄", layout="centered")

st.markdown("""
<style>
    .main .block-container { padding-top: 2rem; }
    .app-header {
        background: linear-gradient(135deg, #028090 0%, #02C39A 100%);
        padding: 1.5rem 1.8rem; border-radius: 14px; margin-bottom: 1.2rem;
    }
    .app-header h1 { color: white; margin: 0; font-size: 1.6rem; }
    .app-header p { color: #E3F3F1; margin: 0.3rem 0 0 0; font-size: 0.95rem; }
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
    section[data-testid="stSidebar"] button,
    div[data-testid="stSidebar"] button {
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
    section[data-testid="stSidebar"] button > div,
    div[data-testid="stSidebar"] button > div,
    section[data-testid="stSidebar"] button p,
    div[data-testid="stSidebar"] button p {
        text-align: left !important;
        justify-content: flex-start !important;
        width: 100% !important;
    }
    section[data-testid="stSidebar"] button:hover,
    div[data-testid="stSidebar"] button:hover {
        background-color: #EDEFEF !important;
        color: #1A2E2A !important;
    }
    section[data-testid="stSidebar"] button:focus,
    div[data-testid="stSidebar"] button:focus,
    section[data-testid="stSidebar"] button:active,
    div[data-testid="stSidebar"] button:active {
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
            "messages": [],
        }
    st.session_state.sessions[sid]["messages"].append([role, text])
    save_sessions(st.session_state.sessions)

# ============================== SIDEBAR NAV ==============================
st.sidebar.markdown(
    '<div style="font-weight:700; font-size:1.05rem; padding:0.3rem 0.5rem;">🐄 Livestock Health Assistant</div>'
    '<div style="color:#8A9694; font-size:0.8rem; padding:0 0.5rem 0.5rem 0.5rem;">የከብት ጤና ረዳት</div>',
    unsafe_allow_html=True,
)

if "current_session_id" not in st.session_state:
    st.session_state.current_session_id = None

MENU_OPTIONS = [
    ("💬", "Chat"),
    ("📚", "Disease Library"),
    ("🚨", "Emergency Guide"),
    ("📅", "Vaccination Reminders"),
]
if "current_page" not in st.session_state:
    st.session_state.current_page = MENU_OPTIONS[0][1]

# --- New chat (top, like ChatGPT's "New chat") ---
if st.sidebar.button("📝  New chat", use_container_width=True):
    st.session_state.current_session_id = None
    st.session_state.current_page = "Chat"
    st.rerun()

st.sidebar.markdown('<div style="height:0.4rem;"></div>', unsafe_allow_html=True)

# --- Main nav: active item shown as a static highlighted row, others as flat buttons ---
for icon, label in MENU_OPTIONS:
    if st.session_state.current_page == label:
        st.sidebar.markdown(f'<div class="nav-active">{icon}&nbsp;&nbsp;{label}</div>', unsafe_allow_html=True)
    else:
        if st.sidebar.button(f"{icon}  {label}", key=f"menu_{label}", use_container_width=True):
            st.session_state.current_page = label
            st.rerun()

page = st.session_state.current_page

# --- Context-specific settings (only relevant on the Chat page) ---
if page == "Chat":
    st.sidebar.markdown('<div class="sidebar-section-label">Animal Details / የእንስሳ ዝርዝር</div>', unsafe_allow_html=True)
    animal_type = st.sidebar.selectbox(
        "What animal is this about? / የትኛው እንስሳ ነው?",
        ["Cattle (ላም)", "Goat (ፍየል)", "Poultry (ዶሮ)", "Other / Not sure (ሌላ)"],
        label_visibility="collapsed",
    )
    response_language = st.sidebar.radio(
        "🌐 Response language / የምላሽ ቋንቋ", ["English", "Amharic (አማርኛ)"],
    )
    language_code = "Amharic" if response_language.startswith("Amharic") else "English"

    if st.session_state.current_session_id and st.sidebar.button("🗑️  Delete this chat", use_container_width=True):
        del st.session_state.sessions[st.session_state.current_session_id]
        save_sessions(st.session_state.sessions)
        st.session_state.current_session_id = None
        st.rerun()

    st.sidebar.markdown("---")

# --- Recent chats list ---
st.sidebar.markdown('<div class="sidebar-section-label">Recent</div>', unsafe_allow_html=True)
sorted_sessions = sorted(
    st.session_state.sessions.items(),
    key=lambda kv: kv[1]["timestamp"],
    reverse=True,
)
if not sorted_sessions:
    st.sidebar.caption("No conversations yet")
else:
    for sid, session in sorted_sessions[:12]:  # show most recent 12
        is_active = sid == st.session_state.current_session_id
        if is_active:
            st.sidebar.markdown(f'<div class="recent-active">{session["title"]}</div>', unsafe_allow_html=True)
        else:
            if st.sidebar.button(session["title"], key=f"recent_{sid}", use_container_width=True):
                st.session_state.current_session_id = sid
                st.session_state.current_page = "Chat"
                st.rerun()

st.sidebar.markdown("---")

st.sidebar.markdown(
    """
    <div style="background-color:#FDECEC; padding:0.8rem; border-radius:10px; font-size:0.8rem; color:#7A2E2E;">
    ⚠️ General guidance only. Always consult a local veterinarian for serious or persistent symptoms.<br><br>
    ⚠️ አጠቃላይ መመሪያ ብቻ ነው። ለከባድ ምልክቶች ሁልጊዜ የእንስሳት ሐኪም ያማክሩ።
    </div>
    """,
    unsafe_allow_html=True,
)

# ============================== MAIN AREA ==============================
st.markdown("""
<div class="app-header">
    <h1>🐄 Livestock Health Assistant</h1>
    <p>የከብት ጤና ረዳት &nbsp;|&nbsp; Offline AI guidance for smallholder farmers — not a replacement for a vet.</p>
</div>
""", unsafe_allow_html=True)

# ------------------------------ CHAT PAGE ------------------------------
if page == "Chat":
    QUICK_SYMPTOMS = [
        ("🫃 Swollen belly", "belly is swollen and it won't eat"),
        ("🦵 Limping", "limping and bad smell from its foot"),
        ("💩 Diarrhea", "watery diarrhea for two days"),
        ("😮\u200d💨 Breathing trouble", "coughing with fast breathing"),
        ("👁️ Eye problem", "cloudy red eye"),
        ("🐔 Egg drop", "stopped laying eggs this week"),
    ]

    st.markdown('<div class="quick-label">Quick tap - common symptoms / የተለመዱ ምልክቶች</div>', unsafe_allow_html=True)
    cols = st.columns(3)
    quick_pick = None
    for i, (label, symptom) in enumerate(QUICK_SYMPTOMS):
        with cols[i % 3]:
            if st.button(label, use_container_width=True, key=f"quick_{i}"):
                quick_pick = symptom

    for role, text in get_current_messages():
        with st.chat_message(role):
            st.markdown(text)

    typed_input = st.chat_input("Describe the symptom you're seeing... / ምልክቱን ይግለጹ...")
    user_input = typed_input or quick_pick

    if user_input:
        full_symptom_text = f"[{animal_type}] {user_input}"

        add_message_to_current_session("user", user_input)
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            with st.spinner("Checking... / በመፈተሽ ላይ..."):
                answer = get_response(full_symptom_text, st.session_state.kb, language=language_code)
            if answer.startswith("EMERGENCY") or answer.startswith("አደጋ"):
                st.error(answer)
            else:
                st.markdown(answer)

        add_message_to_current_session("assistant", answer)

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
